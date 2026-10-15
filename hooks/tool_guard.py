#!/usr/bin/env python3
"""PreToolUse hook (Claude Code and Codex): deny the moves that bypass the rails.

Rules (first match wins):

* state labels (in-progress, review, done) changed with raw ``gh`` instead of
  ``ghflow``, which would skip the PR, results and merge checks;
* ``gh pr merge`` by an agent; merging is the reviewer's call;
* touching the receipt key, or writing receipts by hand.

Shell commands are matched on the command text; file tools (Read, Write,
Edit) only on their path, so writing docs that quote a forbidden command
is fine. A denial is printed as ``hookSpecificOutput.permissionDecision =
"deny"`` with a reason the model sees. Anything else passes through.
Fail-open: a crash here exits non-zero (not 2) and the tool call proceeds.
"""

import json
import re
import sys

STATE = r"(?:in-progress|review|done)"
RULES = [
    (re.compile(rf"\bgh\s+(?:issue|pr)\s+edit\b.*--(?:add|remove)-label[\s=]+['\"]?[^\s]*{STATE}"),
     "Change workflow labels with `.agent-rails/scripts/ghflow claim|review|rework|done <issue>`, not raw gh; ghflow checks the PR, the results comment and the merge."),
    (re.compile(r"\bgh\s+api\b.*issues/\d+/labels"),
     "Label writes through `gh api` bypass ghflow's checks; use `.agent-rails/scripts/ghflow`."),
    (re.compile(r"\bgh\s+pr\s+merge\b"),
     "Agents don't merge. Move the issue to review with `.agent-rails/scripts/ghflow review <issue>` and stop."),
    (re.compile(r"agent-rails/receipt\.key|\.rails/receipts/"),
     "Receipts are written by `.agent-rails/scripts/checklist verify`, never by hand, and the receipt key is off limits."),
]


def command_of(tool_input):
    """Return the text to inspect: a shell command, or a file tool's path."""
    if not isinstance(tool_input, dict):
        return str(tool_input)
    for key in ("command", "cmd"):
        value = tool_input.get(key)
        if isinstance(value, list):
            return " ".join(map(str, value))
        if isinstance(value, str):
            return value
    return " ".join(str(tool_input.get(k, "")) for k in ("file_path", "path", "notebook_path"))


def main():
    """Entry point."""
    payload = json.loads(sys.stdin.read() or "{}")
    text = command_of(payload.get("tool_input", {}))
    for pattern, reason in RULES:
        if pattern.search(text):
            print(json.dumps({"hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": reason,
            }}))
            return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
