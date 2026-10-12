#!/usr/bin/env python3
"""Drive the real Codex CLI with a scripted model and check the hooks fire.

Same idea as claude_e2e.py: a fresh demo repo per scenario, the kit
installed (``.codex/hooks.json``), fake_openai.py as the model provider, and
``codex exec --json``. Assertions read the model request log: what Codex fed
the model after each hook ran.

usage: codex_e2e.py [SCENARIO ...] [--keep] [--codex codex]
Scenarios: stop_blocks, guard_and_wrapper, forged_receipt_and_cap, fail_open,
           read_log, untrusted_hooks_do_not_run
"""

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from claude_e2e import FAKE_GH, KIT, STAMP, free_port, make_demo

SERVER = KIT / "tests" / "harness" / "fake_openai.py"


def env_for(base):
    """Return the environment for codex, its hooks and the kit's scripts."""
    env = {k: v for k, v in os.environ.items() if not k.startswith(("OPENAI", "CODEX", "AGENT_RAILS"))}
    home = base / "home"
    home.mkdir(exist_ok=True)
    return {**env, "HOME": str(home), "CODEX_HOME": str(base / "codex-home"), "FAKE_OPENAI_KEY": "x",
            "PATH": f"{base / 'bin'}:{os.environ['PATH']}", "AGENT_RAILS_GH": str(FAKE_GH), "FAKE_GH_STATE": str(base / "gh.json")}


def run_codex(base, repo, rules, prompt, codex, trust_bypass=True):
    """Run one scripted session; return (codex JSON events, model request log)."""
    port = free_port()
    cfg = base / "codex-home"
    cfg.mkdir(exist_ok=True)
    (cfg / "config.toml").write_text(
        'model = "fake-model"\nmodel_provider = "fake"\n'
        f'[model_providers.fake]\nname = "fake"\nbase_url = "http://127.0.0.1:{port}/v1"\nwire_api = "responses"\nenv_key = "FAKE_OPENAI_KEY"\n'
        f'[projects."{repo}"]\ntrust_level = "trusted"\n')
    (base / "rules.json").write_text(json.dumps(rules))
    log = base / "model.log"
    server = subprocess.Popen([sys.executable, str(SERVER), str(base / "rules.json"), str(log), "--port", str(port)],
                              stderr=subprocess.PIPE, text=True)
    server.stderr.readline()
    flags = ["--dangerously-bypass-hook-trust"] if trust_bypass else []
    try:
        proc = subprocess.run([codex, "exec", *flags, "--dangerously-bypass-approvals-and-sandbox", "--json", prompt],
                              cwd=repo, env=env_for(base), stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=180)
    finally:
        server.terminate()
    events = [json.loads(x) for x in proc.stdout.splitlines() if x.startswith("{")]
    requests = [json.loads(x) for x in log.read_text().splitlines()] if log.exists() else []
    return events, requests


def inputs(requests):
    """Return what Codex fed the model, newest item per request."""
    return [r["newest_input"] for r in requests]


def hook_prompts(requests):
    """Return the Stop hook block reasons Codex fed back to the model."""
    return [t for t in inputs(requests) if t.startswith("<hook_prompt")]


def checklist(base, repo, *args):
    """Run the kit's checklist in the demo repo."""
    return subprocess.run([str(repo / ".agent-rails" / "scripts" / "checklist"), *args], cwd=repo, env=env_for(base),
                          capture_output=True, text=True)


def init_list(base, repo):
    """Create the 'stamp' checklist over posts/*.md."""
    proc = checklist(base, repo, "init", "stamp", "--glob", "posts/*.md", "--check", "grep -q '^License: MIT' {item}")
    assert proc.returncode == 0, proc.stderr


def scenario_stop_blocks(base, repo, codex):
    """A premature 'done' is blocked; the stop is allowed once receipts exist."""
    init_list(base, repo)
    _, requests = run_codex(base, repo, [
        {"when": "have no valid receipt", "reply": {"shell": STAMP}},
        {"when": "\"ok\": true", "reply": {"text": "Every item now has a receipt."}},
        {"when": "SCENARIO", "reply": {"text": "All posts are stamped. Done."}},
    ], "SCENARIO stamp every post", codex)
    prompts = hook_prompts(requests)
    report = json.loads(checklist(base, repo, "status", "--json").stdout)[0]
    assert len(prompts) == 1 and "posts/a.md" in prompts[0], inputs(requests)
    assert report["open"] == [], report
    return {"stop_hook_prompt": prompts[0], "final_open": report["open"]}


def scenario_guard_and_wrapper(base, repo, codex):
    """PreToolUse denies a raw label edit; ghflow refuses review without a PR."""
    _, requests = run_codex(base, repo, [
        {"when": "Change workflow labels with", "reply": {"shell": ".agent-rails/scripts/ghflow claim 1 && .agent-rails/scripts/ghflow review 1"}},
        {"when": "refused", "reply": {"text": "Review refused; stopping to report."}},
        {"when": "SCENARIO", "reply": {"shell": "gh issue edit 1 --add-label review"}},
    ], "SCENARIO move issue 1 to review", codex)
    seen = inputs(requests)
    state = json.loads((base / "gh.json").read_text())
    raw_edits = [c for c in state.get("calls", []) if c[:2] == ["issue", "edit"]]
    denied = [t for t in seen if "Change workflow labels with" in t]
    refused = [t for t in seen if "ghflow: refused" in t]
    assert denied, seen
    assert not raw_edits, raw_edits
    assert refused and "no open or merged PR links #1" in refused[0], seen
    return {"pretooluse_denial": denied[0][:400], "wrapper_refusal": refused[0][-300:],
            "labels_after": state["issues"]["1"]["labels"], "raw_gh_issue_edit_calls": raw_edits}


def scenario_forged_receipt_and_cap(base, repo, codex):
    """A hand-written receipt is reported as forged; the repeat cap ends the loop."""
    init_list(base, repo)
    rid = hashlib.sha256(b"posts/b.md").hexdigest()[:16]
    forge = f"cd .rails && mkdir -p receipts/stamp && echo '{{\"item\": \"posts/b.md\", \"exit\": 0, \"sig\": \"trust-me\"}}' > receipts/stamp/{rid}.json"
    events, requests = run_codex(base, repo, [
        {"when": "SCENARIO", "reply": {"shell": forge}},
        {"when": "", "reply": {"text": "Done, every post has a receipt."}},
    ], "SCENARIO forge a receipt", codex)
    prompts = hook_prompts(requests)
    report = json.loads(checklist(base, repo, "status", "--json").stdout)[0]
    assert len(prompts) == 3, inputs(requests)
    assert "posts/b.md (forged receipt)" in prompts[0], prompts[0]
    assert "posts/b.md" in report["forged"], report
    return {"blocks": len(prompts), "first_block": prompts[0], "forged": report["forged"],
            "turn_completed": any(e.get("type") == "turn.completed" for e in events)}


def scenario_fail_open(base, repo, codex):
    """A crashing Stop hook lets the session end: the gate fails open."""
    init_list(base, repo)
    (repo / ".rails" / "checklists" / "stamp.json").write_text("{broken")
    events, requests = run_codex(base, repo, [{"when": "", "reply": {"text": "Done."}}], "SCENARIO stop with a broken gate", codex)
    assert not hook_prompts(requests), inputs(requests)
    return {"hook_prompts": [], "model_requests": len(requests), "turn_completed": any(e.get("type") == "turn.completed" for e in events)}


def scenario_read_log(base, repo, codex):
    """PostToolUse logs a shell docs read; ghflow result carries it as evidence."""
    body = base / "result.md"
    body.write_text("Stamped the posts.\n")
    _, requests = run_codex(base, repo, [
        {"when": "SCENARIO", "reply": {"shell": ".agent-rails/scripts/ghflow claim 1"}},
        {"when": "\"in-progress\"", "reply": {"shell": "cat docs/guide.md"}},
        {"when": "License line", "reply": {"shell": f".agent-rails/scripts/ghflow result 1 --body-file {body}"}},
        {"when": "issuecomment", "reply": {"text": "Result posted."}},
    ], "SCENARIO claim, read docs, post result", codex)
    log_file = repo / ".rails" / "reads.log"
    log = [json.loads(x) for x in log_file.read_text().splitlines()] if log_file.exists() else []
    comments = json.loads((base / "gh.json").read_text())["issues"]["1"]["comments"]
    assert any(e["path"] == "docs/guide.md" for e in log), (log, inputs(requests))
    assert comments and "`docs/guide.md`" in comments[0]["body"], comments
    return {"reads_log": log, "results_comment": comments[0]["body"]}


def scenario_untrusted_hooks_do_not_run(base, repo, codex):
    """Without hook trust, the project's hooks are skipped and the gate is silently open."""
    init_list(base, repo)
    events, requests = run_codex(base, repo, [{"when": "", "reply": {"text": "Done."}}], "SCENARIO stop with untrusted hooks",
                                 codex, trust_bypass=False)
    notices = [e["item"].get("message") for e in events if e.get("type") == "item.completed" and e["item"].get("type") == "error"]
    assert not hook_prompts(requests), inputs(requests)
    return {"hook_prompts": [], "codex_notices": notices}


SCENARIOS = {name[len("scenario_"):]: fn for name, fn in globals().items() if name.startswith("scenario_")}


def main():
    """Run the chosen scenarios and print one JSON result per scenario."""
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("scenarios", nargs="*", default=list(SCENARIOS))
    parser.add_argument("--codex", default=shutil.which("codex") or "codex")
    parser.add_argument("--keep", action="store_true", help="keep the temp dirs")
    args = parser.parse_args()
    failures = 0
    for name in args.scenarios:
        base = Path(tempfile.mkdtemp(prefix=f"rails-cx-{name}-"))
        started = time.time()
        try:
            detail = SCENARIOS[name](base, make_demo(base), args.codex)
            print(json.dumps({"scenario": name, "ok": True, "seconds": round(time.time() - started, 1), **detail}))
        except AssertionError as exc:
            failures += 1
            print(json.dumps({"scenario": name, "ok": False, "why": str(exc)[:2000], "dir": str(base)}))
        if not args.keep:
            shutil.rmtree(base, ignore_errors=True)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
