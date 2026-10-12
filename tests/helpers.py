"""Shared fixtures: a temp git repo, the fake gh and a script runner."""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

KIT = Path(__file__).resolve().parent.parent
FAKE_GH = KIT / "tests" / "fake_gh.py"


class RepoCase(unittest.TestCase):
    """A test case with a scratch git repo, a fake GitHub and a private key dir."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name) / "repo"
        self.root.mkdir()
        subprocess.run(["git", "init", "-q", str(self.root)], check=True)
        self.state_file = Path(self.tmp.name) / "gh.json"
        self.write_state({"me": "alice", "issues": {}, "pulls": [], "repo_labels": []})
        self.env = {
            **os.environ,
            "AGENT_RAILS_GH": str(FAKE_GH),
            "FAKE_GH_STATE": str(self.state_file),
            "AGENT_RAILS_KEY": str(Path(self.tmp.name) / "keys" / "receipt.key"),
            "CLAUDE_PROJECT_DIR": str(self.root),
        }
        self.env.pop("AGENT_RAILS_DIR", None)
        self.env.pop("AGENT_RAILS_FAIL_CLOSED", None)

    def tearDown(self):
        self.tmp.cleanup()

    def write_state(self, state):
        """Replace the fake GitHub state."""
        self.state_file.write_text(json.dumps(state))

    def state(self):
        """Read the fake GitHub state."""
        return json.loads(self.state_file.read_text())

    def add_issue(self, n, labels=(), assignees=(), state="open"):
        """Create an issue in the fake GitHub."""
        s = self.state()
        s["issues"][str(n)] = {"number": n, "title": f"issue {n}", "state": state,
                               "labels": list(labels), "assignees": list(assignees), "comments": []}
        self.write_state(s)

    def add_pr(self, number, body, merged=False, state="open"):
        """Create a PR in the fake GitHub."""
        s = self.state()
        s["pulls"].append({"number": number, "body": body, "state": "closed" if merged else state,
                           "merged_at": "2026-10-12T00:00:00Z" if merged else None,
                           "html_url": f"https://github.com/o/r/pull/{number}"})
        self.write_state(s)

    def run_script(self, rel, *args, stdin=None, env=None):
        """Run one of the kit's scripts inside the scratch repo."""
        return subprocess.run([sys.executable, str(KIT / rel), *args], cwd=self.root, input=stdin,
                              capture_output=True, text=True, env={**self.env, **(env or {})})

    def labels(self, n):
        """Return the labels of an issue in the fake GitHub."""
        return sorted(self.state()["issues"][str(n)]["labels"])

    def writes(self):
        """Return the mutating gh calls recorded by the fake."""
        return [c for c in self.state().get("calls", []) if "-X" in c and c[c.index("-X") + 1] != "GET"]
