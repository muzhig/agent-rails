"""Hook scripts against the payloads Claude Code and Codex send."""

import json
import subprocess
import sys
import unittest

from helpers import KIT, RepoCase


def stop_payload(session="s1", active=False):
    return json.dumps({"session_id": session, "hook_event_name": "Stop", "stop_hook_active": active, "cwd": "/"})


def tool_payload(tool, **tool_input):
    return json.dumps({"session_id": "s1", "hook_event_name": "PreToolUse", "tool_name": tool, "tool_input": tool_input})


class TestStopGate(RepoCase):

    def setUp(self):
        super().setUp()
        (self.root / "posts").mkdir()
        for name in ("a", "b"):
            (self.root / "posts" / f"{name}.md").write_text("x\n")

    def init_list(self):
        proc = self.run_script("scripts/checklist", "init", "stamp", "--glob", "posts/*.md", "--check", "grep -q DONE {item}")
        self.assertEqual(proc.returncode, 0, proc.stderr)

    def stop(self, env=None, **kw):
        return self.run_script("hooks/stop_gate.py", stdin=stop_payload(**kw), env=env)

    def test_no_checklists_allows_stop(self):
        proc = self.stop()
        self.assertEqual((proc.returncode, proc.stdout), (0, ""))

    def test_open_items_block_with_their_names(self):
        self.init_list()
        proc = self.stop()
        self.assertEqual(proc.returncode, 0)
        out = json.loads(proc.stdout)
        self.assertEqual(out["decision"], "block")
        self.assertIn("posts/a.md", out["reason"])
        self.assertIn("posts/b.md", out["reason"])

    def test_done_items_allow_stop(self):
        self.init_list()
        for name in ("a", "b"):
            (self.root / "posts" / f"{name}.md").write_text("DONE\n")
        self.run_script("scripts/checklist", "verify", "stamp", "--all")
        proc = self.stop()
        self.assertEqual((proc.returncode, proc.stdout), (0, ""))

    def test_installed_gate_checks_its_repo_from_a_parent_cwd(self):
        subprocess.run([str(KIT / "scripts" / "install"), str(self.root)], check=True, capture_output=True)
        self.init_list()
        env = {k: v for k, v in self.env.items() if k != "CLAUDE_PROJECT_DIR"}
        workspace = self.root.parent
        payload = json.dumps({"session_id": "s1", "hook_event_name": "Stop", "stop_hook_active": False, "cwd": str(workspace)})
        proc = subprocess.run([sys.executable, str(self.root / ".agent-rails" / "hooks" / "stop_gate.py")], cwd=workspace,
                              input=payload, capture_output=True, text=True, env=env)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(json.loads(proc.stdout)["decision"], "block")
        self.assertIn("posts/a.md", proc.stdout)

    def test_repeat_cap_lets_the_session_end(self):
        self.init_list()
        decisions = [json.loads(self.stop(session="loop").stdout) for _ in range(4)]
        self.assertEqual([d.get("decision") for d in decisions], ["block", "block", "block", None])
        self.assertIn("stop allowed after 3 blocks", decisions[3]["systemMessage"])

    def test_cap_is_per_session(self):
        self.init_list()
        for _ in range(3):
            self.stop(session="one")
        self.assertEqual(json.loads(self.stop(session="two").stdout)["decision"], "block")

    def test_crash_fails_open(self):
        self.init_list()
        (self.root / ".rails" / "checklists" / "stamp.json").write_text("{broken")
        proc = self.stop()
        self.assertEqual(proc.returncode, 1)
        self.assertEqual(proc.stdout, "")

    def test_fail_closed_blocks_once_then_lets_go(self):
        self.init_list()
        (self.root / ".rails" / "checklists" / "stamp.json").write_text("{broken")
        first = self.stop(env={"AGENT_RAILS_FAIL_CLOSED": "1"})
        self.assertEqual(first.returncode, 2)
        again = self.stop(env={"AGENT_RAILS_FAIL_CLOSED": "1"}, active=True)
        self.assertEqual(again.returncode, 1)


class TestToolGuard(RepoCase):

    def guard(self, payload):
        return self.run_script("hooks/tool_guard.py", stdin=payload)

    def assertDenied(self, payload):
        proc = self.guard(payload)
        self.assertEqual(proc.returncode, 0)
        self.assertEqual(json.loads(proc.stdout)["hookSpecificOutput"]["permissionDecision"], "deny")

    def assertAllowed(self, payload):
        proc = self.guard(payload)
        self.assertEqual((proc.returncode, proc.stdout), (0, ""))

    def test_raw_state_label_edit_denied(self):
        self.assertDenied(tool_payload("Bash", command="gh issue edit 3 --add-label review"))
        self.assertDenied(tool_payload("Bash", command="gh issue edit 3 --remove-label=in-progress --add-label done"))
        self.assertDenied(tool_payload("Bash", command="gh api -X POST repos/o/r/issues/3/labels -f labels[]=done"))

    def test_merge_denied(self):
        self.assertDenied(tool_payload("Bash", command="cd x && gh pr merge 5 --squash"))

    def test_receipt_tampering_denied(self):
        self.assertDenied(tool_payload("Bash", command="cat ~/.config/agent-rails/receipt.key"))
        self.assertDenied(tool_payload("Write", file_path="/r/.rails/receipts/stamp/abc.json", content="{}"))

    def test_codex_style_argv_command_is_inspected(self):
        self.assertDenied(tool_payload("shell", command=["bash", "-lc", "gh pr merge 5"]))
        self.assertDenied(tool_payload("Bash", cmd="gh pr merge 5"))

    def test_normal_work_allowed(self):
        self.assertAllowed(tool_payload("Bash", command="ghflow review 3"))
        self.assertAllowed(tool_payload("Bash", command="gh pr create --title t --body 'Closes #3'"))
        self.assertAllowed(tool_payload("Bash", command="gh issue edit 3 --add-label bug"))
        self.assertAllowed(tool_payload("Read", file_path="/r/docs/guide.md"))

    def test_docs_quoting_a_forbidden_command_allowed(self):
        quoted = "never run gh pr merge, or gh issue edit 1 --add-label review"
        self.assertAllowed(tool_payload("Write", file_path="/r/README.md", content=quoted))
        self.assertAllowed(tool_payload("Edit", file_path="/r/README.md", old_string="x", new_string=quoted))

    def test_garbage_input_fails_open(self):
        proc = self.guard("not json")
        self.assertEqual(proc.returncode, 1)
        self.assertEqual(proc.stdout, "")


class TestReadLog(RepoCase):

    def entries(self):
        log = self.root / ".rails" / "reads.log"
        return [json.loads(x)["path"] for x in log.read_text().splitlines()] if log.exists() else []

    def test_read_tool_logged_relative(self):
        (self.root / "docs").mkdir()
        (self.root / "docs" / "a.md").write_text("a")
        self.run_script("hooks/read_log.py", stdin=tool_payload("Read", file_path=str(self.root / "docs" / "a.md")))
        self.assertEqual(self.entries(), ["docs/a.md"])

    def test_shell_reads_logged_and_mentions_ignored(self):
        (self.root / "README.md").write_text("r")
        self.run_script("hooks/read_log.py", stdin=tool_payload("Bash", command="cat README.md | head -5"))
        self.run_script("hooks/read_log.py", stdin=tool_payload("Bash", command="echo README.md"))
        self.run_script("hooks/read_log.py", stdin=tool_payload("Bash", command="sed -n 1,9p missing.md"))
        self.assertEqual(self.entries(), ["README.md"])

    def test_codex_cmd_argument_logged(self):
        (self.root / "README.md").write_text("r")
        self.run_script("hooks/read_log.py", stdin=tool_payload("Bash", cmd="cat README.md"))
        self.assertEqual(self.entries(), ["README.md"])

    def test_read_in_another_worktree_logs_there(self):
        other = self.root.parent / "other"
        other.mkdir()
        subprocess.run(["git", "init", "-q", str(other)], check=True)
        (other / "README.md").write_text("r")
        self.run_script("hooks/read_log.py", stdin=tool_payload("Read", file_path=str(other / "README.md")))
        self.assertEqual(self.entries(), [])
        self.assertIn("README.md", (other / ".rails" / "reads.log").read_text())


if __name__ == "__main__":
    unittest.main()
