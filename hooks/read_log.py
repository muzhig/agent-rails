#!/usr/bin/env python3
"""PostToolUse hook: log which files the agent actually read.

Appends ``{"at", "session", "tool", "path"}`` lines to ``.rails/reads.log`` of
the git work tree that contains the file, so a sub-agent working in its own
worktree logs to that worktree. Files outside any repo are ignored.
``ghflow review`` refuses to move an issue while the log shows no docs read
since the claim, and ``ghflow result`` copies the docs list into the results
comment. "Explore the docs first" is checked by a side effect, not taken on
the model's word.

Read, Grep and Glob are logged by path. For shell tools, the arguments of
read-only commands (cat, head, tail, sed, less, nl, grep, rg, wc) that name
existing files are logged. Fail-open: a crash only loses a log line.
"""

import json
import os
import shlex
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

READERS = {"cat", "head", "tail", "sed", "less", "nl", "grep", "rg", "wc", "bat", "more"}


def paths_from_shell(command, root):
    """Return files named by read-only commands in a shell line."""
    found = []
    for segment in command.replace("&&", ";").replace("||", ";").replace("|", ";").split(";"):
        words = shlex.split(segment, posix=True) if segment.strip() else []
        if not words or Path(words[0]).name not in READERS:
            continue
        for word in words[1:]:
            candidate = (root / word).resolve() if not os.path.isabs(word) else Path(word)
            if not word.startswith("-") and candidate.is_file():
                found.append(candidate)
    return found


def repo_of(path, fallback):
    """Return the git work tree containing ``path``, so worktrees log to themselves."""
    proc = subprocess.run(["git", "-C", str(Path(path).parent), "rev-parse", "--show-toplevel"], capture_output=True, text=True)
    return Path(proc.stdout.strip()).resolve() if proc.returncode == 0 else fallback


def main():
    """Entry point."""
    payload = json.loads(sys.stdin.read() or "{}")
    root = Path(os.environ.get("CLAUDE_PROJECT_DIR") or payload.get("cwd") or os.getcwd()).resolve()
    tool = payload.get("tool_name", "")
    tool_input = payload.get("tool_input") or {}
    paths = []
    if tool == "Read" and tool_input.get("file_path"):
        paths = [tool_input["file_path"]]
    elif tool in ("Grep", "Glob") and tool_input.get("path"):
        paths = [tool_input["path"]]
    else:
        command = (tool_input.get("command") or tool_input.get("cmd")) if isinstance(tool_input, dict) else None
        if isinstance(command, list):
            command = shlex.join(map(str, command))
        if command:
            paths = paths_from_shell(command, root)
    at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    for path in paths:
        path = Path(path).resolve()
        repo = repo_of(path, root)
        if not path.is_relative_to(repo):
            continue
        log = Path(os.environ.get("AGENT_RAILS_DIR") or repo / ".rails") / "reads.log"
        log.parent.mkdir(parents=True, exist_ok=True)
        with log.open("a") as fh:
            fh.write(json.dumps({"at": at, "session": payload.get("session_id"), "tool": tool, "path": str(path.relative_to(repo))}) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
