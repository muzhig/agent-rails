#!/usr/bin/env python3
"""Stop hook (Claude Code and Codex): no stopping while checklist items are open.

Reads the hook payload on stdin, runs ``checklist status --all --json`` in the
project root and, if any item lacks a valid receipt, prints
``{"decision": "block", "reason": ...}`` naming the open items. The agent is
sent back to work with that reason as its next instruction.

Repeat cap: each session may be blocked at most AGENT_RAILS_STOP_CAP times
(default 3). After that the stop is allowed with a warning, because a gate
the agent cannot satisfy otherwise loops until a human kills the session.

Fail-open: if this script crashes, both harnesses treat a non-zero exit other
than 2 as a hook error and let the agent stop. Set AGENT_RAILS_FAIL_CLOSED=1
to turn a crash into one block (exit 2) instead; a second consecutive stop
(``stop_hook_active``) is then let through so a broken gate cannot loop.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

KIT = Path(__file__).resolve().parent.parent
MAX_LISTED = 15


def project_root(payload):
    """Return the project directory the hook runs for."""
    return Path(os.environ.get("CLAUDE_PROJECT_DIR") or payload.get("cwd") or os.getcwd())


def open_items(root):
    """Return [(list name, item, why)] for every open checklist item."""
    proc = subprocess.run(
        [sys.executable, str(KIT / "scripts" / "checklist"), "status", "--all", "--json"],
        cwd=root, capture_output=True, text=True,
    )
    if proc.returncode not in (0, 2):
        raise RuntimeError(f"checklist status failed ({proc.returncode}): {proc.stderr.strip()}")
    found = []
    for report in json.loads(proc.stdout):
        for item in report["open"]:
            why = "forged receipt" if item in report["forged"] else "stale receipt" if item in report["stale"] else "no receipt"
            found.append((report["name"], item, why))
    return found


def bump_counter(root, session):
    """Count blocks for this session and return the new count."""
    path = Path(os.environ.get("AGENT_RAILS_DIR", root / ".rails")) / "stop-blocks" / f"{session}.count"
    path.parent.mkdir(parents=True, exist_ok=True)
    count = int(path.read_text()) + 1 if path.exists() else 1
    path.write_text(str(count))
    return count


def decide(payload):
    """Return the hook output dict, or None to allow the stop silently."""
    root = project_root(payload)
    found = open_items(root)
    if not found:
        return None
    cap = int(os.environ.get("AGENT_RAILS_STOP_CAP", "3"))
    count = bump_counter(root, payload.get("session_id", "unknown"))
    if count > cap:
        return {"systemMessage": f"agent-rails: stop allowed after {cap} blocks with {len(found)} checklist items still open"}
    listed = "; ".join(f"{name}: {item} ({why})" for name, item, why in found[:MAX_LISTED])
    more = f" and {len(found) - MAX_LISTED} more" if len(found) > MAX_LISTED else ""
    reason = (
        f"{len(found)} checklist item(s) have no valid receipt: {listed}{more}. "
        "Finish each one, then run `checklist verify <list> <item>` so the runner writes its receipt. "
        f"Block {count} of {cap}."
    )
    return {"decision": "block", "reason": reason}


def main():
    """Entry point."""
    payload = {}
    try:
        payload = json.loads(sys.stdin.read() or "{}")
        result = decide(payload)
    except Exception as exc:
        if os.environ.get("AGENT_RAILS_FAIL_CLOSED") == "1" and not payload.get("stop_hook_active"):
            print(f"agent-rails stop gate crashed, blocking once (fail-closed): {exc}", file=sys.stderr)
            return 2
        raise
    if result:
        print(json.dumps(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
