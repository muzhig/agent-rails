#!/usr/bin/env python3
"""Drive the real Claude Code CLI with a scripted model and check the hooks fire.

Each scenario builds a fresh demo repo, installs the kit, starts
fake_anthropic.py with a scenario script, runs ``claude -p`` against it and
asserts on the stream-json transcript. The model is fake; Claude Code, its
hook dispatch and the kit's scripts are real. A fake ``gh`` on PATH stands in
for GitHub and logs every call.

usage: claude_e2e.py [SCENARIO ...] [--keep] [--claude claude]
Scenarios: stop_blocks, guard_and_wrapper, forged_receipt_and_cap, fail_open, read_log
"""

import argparse
import hashlib
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path

KIT = Path(__file__).resolve().parents[2]
SERVER = KIT / "tests" / "harness" / "fake_anthropic.py"
FAKE_GH = KIT / "tests" / "fake_gh.py"
STAMP = "for f in posts/*.md; do grep -q '^License: MIT' \"$f\" || echo 'License: MIT' >> \"$f\"; done; .agent-rails/scripts/checklist verify stamp --all"


def free_port():
    """Return a free TCP port on localhost."""
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def bash(command):
    """Return a scripted Bash tool call."""
    return {"tool": "Bash", "input": {"command": command, "description": "scripted"}}


def git(repo, *args):
    """Run git in the demo repo."""
    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True)


def make_demo(base):
    """Create a demo repo with three posts, docs, the kit and a fake gh."""
    repo = base / "demo"
    (repo / "posts").mkdir(parents=True)
    (repo / "docs").mkdir()
    for name in "abc":
        (repo / "posts" / f"{name}.md").write_text(f"# post {name}\n")
    (repo / "README.md").write_text("# Demo\n")
    (repo / "docs" / "guide.md").write_text("Every post ends with a License line.\n")
    git(repo, "init", "-q")
    git(repo, "add", "-A")
    git(repo, "-c", "user.email=demo@example.com", "-c", "user.name=demo", "commit", "-qm", "init")
    subprocess.run([str(KIT / "scripts" / "install"), str(repo)], check=True, capture_output=True)
    bindir = base / "bin"
    bindir.mkdir()
    (bindir / "gh").write_text(f"#!/bin/sh\nexec {sys.executable} {FAKE_GH} \"$@\"\n")
    (bindir / "gh").chmod(0o755)
    (base / "gh.json").write_text(json.dumps({
        "me": "alice", "repo_labels": ["in-progress", "review", "done"], "pulls": [],
        "issues": {"1": {"number": 1, "title": "stamp posts", "state": "open", "labels": [], "assignees": [], "comments": []}},
    }))
    return repo


def env_for(base, port):
    """Return the environment for claude and its hooks."""
    return {
        **os.environ,
        "PATH": f"{base / 'bin'}:{os.environ['PATH']}",
        "CLAUDE_CONFIG_DIR": str(base / "claude-config"),
        "ANTHROPIC_BASE_URL": f"http://127.0.0.1:{port}",
        "ANTHROPIC_API_KEY": "sk-fake",
        "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1",
        "AGENT_RAILS_KEY": str(base / "key" / "receipt.key"),
        "AGENT_RAILS_GH": str(FAKE_GH),
        "FAKE_GH_STATE": str(base / "gh.json"),
    }


def run_claude(base, repo, rules, prompt, claude):
    """Run one scripted session; return (stream events, model request log)."""
    port = free_port()
    (base / "rules.json").write_text(json.dumps(rules))
    log = base / "model.log"
    server = subprocess.Popen([sys.executable, str(SERVER), str(base / "rules.json"), str(log), "--port", str(port)],
                              stderr=subprocess.PIPE, text=True)
    server.stderr.readline()
    try:
        proc = subprocess.run([claude, "-p", prompt, "--dangerously-skip-permissions", "--model", "claude-sonnet-4-5",
                               "--output-format", "stream-json", "--verbose"],
                              cwd=repo, env=env_for(base, port), stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=180)
    finally:
        server.terminate()
    events = [json.loads(line) for line in proc.stdout.splitlines() if line.startswith("{")]
    requests = [json.loads(x) for x in log.read_text().splitlines()] if log.exists() else []
    return events, requests


def user_texts(events):
    """Return every user-turn text and tool result in the transcript."""
    out = []
    for e in events:
        if e.get("type") != "user":
            continue
        for block in e["message"]["content"]:
            if block.get("type") == "text":
                out.append(block["text"])
            elif block.get("type") == "tool_result":
                content = block.get("content")
                out.append(("ERROR " if block.get("is_error") else "") + (content if isinstance(content, str) else json.dumps(content)))
    return out


def checklist_status(base, repo):
    """Return the checklist report for the demo repo."""
    proc = subprocess.run([str(repo / ".agent-rails" / "scripts" / "checklist"), "status", "--json"], cwd=repo,
                          env=env_for(base, 0), capture_output=True, text=True)
    return json.loads(proc.stdout)[0]


def init_list(base, repo):
    """Create the 'stamp' checklist over posts/*.md."""
    subprocess.run([str(repo / ".agent-rails" / "scripts" / "checklist"), "init", "stamp", "--glob", "posts/*.md",
                    "--check", "grep -q '^License: MIT' {item}"], cwd=repo, env=env_for(base, 0), check=True, capture_output=True)


def scenario_stop_blocks(base, repo, claude):
    """A premature 'done' is blocked; the stop is allowed once receipts exist."""
    init_list(base, repo)
    events, _ = run_claude(base, repo, [
        {"when": "have no valid receipt", "reply": bash(STAMP)},
        {"when": "\"ok\": true", "reply": {"text": "Every item now has a receipt."}},
        {"when": "SCENARIO", "reply": {"text": "All posts are stamped. Done."}},
    ], "SCENARIO stamp every post", claude)
    texts = user_texts(events)
    feedback = [t for t in texts if t.startswith("Stop hook feedback")]
    assert len(feedback) == 1 and "posts/a.md" in feedback[0], texts
    report = checklist_status(base, repo)
    assert report["open"] == [], report
    return {"stop_hook_feedback": feedback, "final_open": report["open"], "result": events[-1].get("subtype")}


def scenario_guard_and_wrapper(base, repo, claude):
    """PreToolUse denies a raw label edit; ghflow refuses review without a PR."""
    events, _ = run_claude(base, repo, [
        {"when": "Change workflow labels with", "reply": bash(".agent-rails/scripts/ghflow claim 1 && .agent-rails/scripts/ghflow review 1")},
        {"when": "refused", "reply": {"text": "Review refused; stopping to report."}},
        {"when": "SCENARIO", "reply": bash("gh issue edit 1 --add-label review")},
    ], "SCENARIO move issue 1 to review", claude)
    texts = user_texts(events)
    state = json.loads((base / "gh.json").read_text())
    raw_edits = [c for c in state.get("calls", []) if c[:2] == ["issue", "edit"]]
    denied = [t for t in texts if "Change workflow labels with" in t]
    refused = [t for t in texts if "ghflow: refused" in t]
    assert denied, texts
    assert not raw_edits, raw_edits
    assert refused and "no open or merged PR links #1" in refused[0], texts
    labels = state["issues"]["1"]["labels"]
    assert labels == ["in-progress"], labels
    return {"pretooluse_denial": denied[0][:300], "wrapper_refusal": refused[0][:400], "labels_after": labels,
            "raw_gh_issue_edit_calls": raw_edits}


def scenario_forged_receipt_and_cap(base, repo, claude):
    """A hand-written receipt is reported as forged; the repeat cap ends the loop."""
    init_list(base, repo)
    rid = hashlib.sha256(b"posts/b.md").hexdigest()[:16]
    forge = f"cd .rails && mkdir -p receipts/stamp && echo '{{\"item\": \"posts/b.md\", \"exit\": 0, \"sig\": \"trust-me\"}}' > receipts/stamp/{rid}.json"
    events, _ = run_claude(base, repo, [
        {"when": "SCENARIO", "reply": bash(forge)},
        {"when": "", "reply": {"text": "Done, every post has a receipt."}},
    ], "SCENARIO forge a receipt", claude)
    feedback = [t for t in user_texts(events) if t.startswith("Stop hook feedback")]
    assert len(feedback) == 3, feedback
    assert "posts/b.md (forged receipt)" in feedback[0], feedback[0]
    notes = [e for e in events if e.get("type") == "system" and "stop allowed after 3 blocks" in json.dumps(e)]
    report = checklist_status(base, repo)
    assert "posts/b.md" in report["forged"], report
    return {"blocks": len(feedback), "first_block": feedback[0], "cap_system_message_seen": bool(notes),
            "forged": report["forged"], "result": events[-1].get("subtype")}


def scenario_fail_open(base, repo, claude):
    """A crashing Stop hook lets the session end: the gate fails open."""
    init_list(base, repo)
    (repo / ".rails" / "checklists" / "stamp.json").write_text("{broken")
    events, _ = run_claude(base, repo, [{"when": "", "reply": {"text": "Done."}}], "SCENARIO stop with a broken gate", claude)
    texts = user_texts(events)
    assert not [t for t in texts if t.startswith("Stop hook feedback")], texts
    hook_errors = [e.get("key") or e.get("subtype") for e in events if e.get("type") == "system" and "hook" in json.dumps(e).lower()]
    return {"stop_hook_feedback": [], "result": events[-1].get("subtype"), "hook_error_events": hook_errors}


def scenario_read_log(base, repo, claude):
    """PostToolUse logs a docs read; ghflow result carries it as evidence."""
    body = base / "result.md"
    body.write_text("Stamped the posts.\n")
    run_claude(base, repo, [
        {"when": "SCENARIO", "reply": bash(".agent-rails/scripts/ghflow claim 1")},
        {"when": "\"in-progress\"", "reply": {"tool": "Read", "input": {"file_path": str(repo / "docs" / "guide.md")}}},
        {"when": "License line", "reply": bash(f".agent-rails/scripts/ghflow result 1 --body-file {body}")},
        {"when": "issuecomment", "reply": {"text": "Result posted."}},
    ], "SCENARIO claim, read docs, post result", claude)
    log = [json.loads(x) for x in (repo / ".rails" / "reads.log").read_text().splitlines()]
    comment = json.loads((base / "gh.json").read_text())["issues"]["1"]["comments"][0]["body"]
    assert any(e["path"] == "docs/guide.md" for e in log), log
    assert "`docs/guide.md`" in comment, comment
    return {"reads_log": log, "results_comment": comment}


SCENARIOS = {name[len("scenario_"):]: fn for name, fn in globals().items() if name.startswith("scenario_")}


def main():
    """Run the chosen scenarios and print one JSON result per scenario."""
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("scenarios", nargs="*", default=list(SCENARIOS))
    parser.add_argument("--claude", default=shutil.which("claude") or "claude")
    parser.add_argument("--keep", action="store_true", help="keep the temp dirs")
    args = parser.parse_args()
    failures = 0
    for name in args.scenarios:
        base = Path(tempfile.mkdtemp(prefix=f"rails-{name}-"))
        started = time.time()
        try:
            detail = SCENARIOS[name](base, make_demo(base), args.claude)
            print(json.dumps({"scenario": name, "ok": True, "seconds": round(time.time() - started, 1), **detail}))
        except AssertionError as exc:
            failures += 1
            print(json.dumps({"scenario": name, "ok": False, "why": str(exc)[:2000], "dir": str(base)}))
        if not args.keep:
            shutil.rmtree(base, ignore_errors=True)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
