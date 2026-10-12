"""ghflow refuses illegal moves and confirms every write by reading it back."""

import json
import unittest

from helpers import RepoCase

REFUSED, UNCONFIRMED = 3, 4


class GhflowCase(RepoCase):
    """Helpers for driving ghflow against the fake gh."""

    def ghflow(self, *args, stdin=None):
        return self.run_script("scripts/ghflow", *args, stdin=stdin)

    def log_read(self, rel):
        """Simulate the PostToolUse hook logging a Read of ``rel``."""
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("text\n")
        payload = json.dumps({"session_id": "s1", "tool_name": "Read", "tool_input": {"file_path": str(path)}})
        self.assertEqual(self.run_script("hooks/read_log.py", stdin=payload).returncode, 0)

    def log_docs_read(self):
        self.log_read("docs/guide.md")

    def post_result(self, n):
        (self.root / "result.md").write_text("Did the thing.\n")
        return self.ghflow("result", str(n), "--body-file", str(self.root / "result.md"))

    def claimed_ready_for_review(self, n=1):
        self.add_issue(n)
        self.assertEqual(self.ghflow("claim", str(n)).returncode, 0)
        self.log_docs_read()
        self.add_pr(10, f"Closes #{n}")
        self.assertEqual(self.post_result(n).returncode, 0)


class TestClaim(GhflowCase):

    def test_claim_assigns_and_labels(self):
        self.add_issue(1)
        proc = self.ghflow("claim", "1")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(self.labels(1), ["in-progress"])
        self.assertEqual(self.state()["issues"]["1"]["assignees"], ["alice"])
        self.assertTrue((self.root / ".rails" / "claims" / "1.json").exists())

    def test_claim_refused_when_already_in_progress(self):
        self.add_issue(1, labels=["in-progress"])
        proc = self.ghflow("claim", "1")
        self.assertEqual(proc.returncode, REFUSED)
        self.assertIn("already 'in-progress'", proc.stderr)
        self.assertEqual(self.writes(), [])

    def test_claim_refused_when_assigned_to_someone_else(self):
        self.add_issue(1, assignees=["bob"])
        proc = self.ghflow("claim", "1")
        self.assertEqual(proc.returncode, REFUSED)
        self.assertEqual(self.writes(), [])

    def test_claim_refused_on_closed_issue(self):
        self.add_issue(1, state="closed")
        self.assertEqual(self.ghflow("claim", "1").returncode, REFUSED)

    def test_dropped_label_write_is_not_confirmed(self):
        self.add_issue(1)
        s = self.state()
        s["drop"] = ["labels"]
        self.write_state(s)
        proc = self.ghflow("claim", "1")
        self.assertEqual(proc.returncode, UNCONFIRMED)
        self.assertIn("not visible on read-back", proc.stderr)


class TestResult(GhflowCase):

    def test_result_is_read_back_and_carries_docs_evidence(self):
        self.add_issue(1)
        self.ghflow("claim", "1")
        self.log_docs_read()
        proc = self.post_result(1)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        body = self.state()["issues"]["1"]["comments"][0]["body"]
        self.assertIn("<!-- agent-rails:result -->", body)
        self.assertIn("`docs/guide.md`", body)

    def test_dropped_comment_is_not_confirmed(self):
        self.add_issue(1)
        s = self.state()
        s["drop"] = ["comments"]
        self.write_state(s)
        proc = self.post_result(1)
        self.assertEqual(proc.returncode, UNCONFIRMED)
        self.assertIn("not readable back", proc.stderr)


class TestReview(GhflowCase):

    def test_review_allowed_with_pr_results_and_docs(self):
        self.claimed_ready_for_review()
        proc = self.ghflow("review", "1")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(self.labels(1), ["review"])

    def test_review_refused_without_linked_pr(self):
        self.add_issue(1)
        self.ghflow("claim", "1")
        self.log_docs_read()
        self.post_result(1)
        proc = self.ghflow("review", "1")
        self.assertEqual(proc.returncode, REFUSED)
        self.assertIn("no open or merged PR links #1", proc.stderr)
        self.assertEqual(self.labels(1), ["in-progress"])

    def test_pr_for_issue_12_does_not_link_issue_1(self):
        self.add_issue(1)
        self.ghflow("claim", "1")
        self.log_docs_read()
        self.post_result(1)
        self.add_pr(10, "Closes #12")
        self.assertEqual(self.ghflow("review", "1").returncode, REFUSED)

    def test_closed_unmerged_pr_does_not_count(self):
        self.add_issue(1)
        self.ghflow("claim", "1")
        self.log_docs_read()
        self.post_result(1)
        self.add_pr(10, "Closes #1", state="closed")
        self.assertEqual(self.ghflow("review", "1").returncode, REFUSED)

    def test_review_refused_without_results_comment(self):
        self.add_issue(1)
        self.ghflow("claim", "1")
        self.log_docs_read()
        self.add_pr(10, "Fixes #1")
        proc = self.ghflow("review", "1")
        self.assertEqual(proc.returncode, REFUSED)
        self.assertIn("no results comment", proc.stderr)

    def test_review_refused_without_docs_reads(self):
        self.add_issue(1)
        self.ghflow("claim", "1")
        self.add_pr(10, "Resolves #1")
        self.post_result(1)
        proc = self.ghflow("review", "1")
        self.assertEqual(proc.returncode, REFUSED)
        self.assertIn("no docs read", proc.stderr)

    def test_reading_the_skill_itself_is_not_docs(self):
        self.add_issue(1)
        self.ghflow("claim", "1")
        self.log_read(".claude/skills/issue-worker/SKILL.md")
        self.add_pr(10, "Closes #1")
        self.post_result(1)
        proc = self.ghflow("review", "1")
        self.assertEqual(proc.returncode, REFUSED)
        self.assertIn("no docs read", proc.stderr)

    def test_review_refused_from_unclaimed(self):
        self.add_issue(1)
        self.add_pr(10, "Closes #1")
        self.assertEqual(self.ghflow("review", "1").returncode, REFUSED)
        self.assertEqual(self.labels(1), [])

    def test_two_state_labels_refused(self):
        self.add_issue(1, labels=["in-progress", "review"])
        proc = self.ghflow("review", "1")
        self.assertEqual(proc.returncode, REFUSED)
        self.assertIn("more than one state label", proc.stderr)


class TestDone(GhflowCase):

    def test_done_refused_with_open_pr(self):
        self.claimed_ready_for_review()
        self.ghflow("review", "1")
        proc = self.ghflow("done", "1")
        self.assertEqual(proc.returncode, REFUSED)
        self.assertIn("no merged PR", proc.stderr)
        self.assertEqual(self.labels(1), ["review"])

    def test_done_allowed_after_merge(self):
        self.claimed_ready_for_review()
        self.ghflow("review", "1")
        s = self.state()
        s["pulls"][0].update(state="closed", merged_at="2026-10-12T01:00:00Z")
        self.write_state(s)
        proc = self.ghflow("done", "1")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(self.labels(1), ["done"])

    def test_done_cannot_skip_review(self):
        self.add_issue(1)
        self.ghflow("claim", "1")
        self.add_pr(10, "Closes #1", merged=True)
        proc = self.ghflow("done", "1")
        self.assertEqual(proc.returncode, REFUSED)
        self.assertEqual(self.labels(1), ["in-progress"])

    def test_rework_returns_to_in_progress(self):
        self.claimed_ready_for_review()
        self.ghflow("review", "1")
        self.assertEqual(self.ghflow("rework", "1").returncode, 0)
        self.assertEqual(self.labels(1), ["in-progress"])

    def test_release_drops_claim(self):
        self.add_issue(1)
        self.ghflow("claim", "1")
        self.assertEqual(self.ghflow("release", "1").returncode, 0)
        self.assertEqual(self.labels(1), [])
        self.assertEqual(self.state()["issues"]["1"]["assignees"], [])


class TestObserverViews(GhflowCase):

    def test_status_accepts_only_recorded_results(self):
        self.add_issue(1)
        self.ghflow("claim", "1")
        status = json.loads(self.ghflow("status", "1").stdout)
        self.assertFalse(status["accept"])
        self.log_docs_read()
        self.add_pr(10, "Closes #1")
        self.post_result(1)
        self.ghflow("review", "1")
        status = json.loads(self.ghflow("status", "1").stdout)
        self.assertTrue(status["accept"])
        self.assertEqual(status["prs"][0]["state"], "open")

    def status(self, n=1):
        return json.loads(self.ghflow("status", str(n)).stdout)

    def test_pr_closed_unmerged_after_review_is_not_accepted(self):
        self.claimed_ready_for_review()
        self.ghflow("review", "1")
        self.assertTrue(self.status()["accept"])
        s = self.state()
        s["pulls"][0]["state"] = "closed"
        self.write_state(s)
        status = self.status()
        self.assertEqual((status["state"], status["prs"][0]["state"]), ("review", "closed"))
        self.assertFalse(status["accept"])

    def test_done_label_without_merged_pr_is_not_accepted(self):
        self.add_issue(1, labels=["done"])
        self.add_pr(10, "Closes #1")
        self.log_docs_read()
        self.post_result(1)
        self.assertFalse(self.status()["accept"])
        s = self.state()
        s["pulls"][0].update(state="closed", merged_at="2026-10-12T01:00:00Z")
        self.write_state(s)
        self.assertTrue(self.status()["accept"])

    def test_merged_pr_accepted_in_review(self):
        self.claimed_ready_for_review()
        self.ghflow("review", "1")
        s = self.state()
        s["pulls"][0].update(state="closed", merged_at="2026-10-12T01:00:00Z")
        self.write_state(s)
        self.assertTrue(self.status()["accept"])

    def test_watch_reports_new_pr_feedback_once(self):
        self.add_issue(1)
        self.add_pr(10, "Closes #1")
        snap = str(self.root / "snap.json")
        self.ghflow("watch", "--once", "--state", snap)
        s = self.state()
        s["pr_feedback"] = {"10": {
            "comments": [{"id": 1, "user": {"login": "rev"}, "html_url": "https://github.com/o/r/pull/10#issuecomment-1"}],
            "review_comments": [{"id": 2, "user": {"login": "rev"}, "html_url": "https://github.com/o/r/pull/10#discussion_r2"}],
            "reviews": [{"id": 3, "user": {"login": "rev"}, "state": "CHANGES_REQUESTED", "html_url": "https://github.com/o/r/pull/10#pullrequestreview-3"}],
        }}
        self.write_state(s)
        events = [json.loads(x) for x in self.ghflow("watch", "--once", "--state", snap).stdout.splitlines()]
        feedback = [e for e in events if e["event"] == "feedback"]
        self.assertEqual(sorted(e["kind"] for e in feedback), ["comment", "review", "review_comment"])
        self.assertTrue(all(e["pr"] == 10 and e["author"] == "rev" and e["url"] for e in feedback))
        self.assertEqual([e["review_state"] for e in feedback if e["kind"] == "review"], ["CHANGES_REQUESTED"])
        self.assertEqual(self.ghflow("watch", "--once", "--state", snap).stdout, "")

    def test_watch_turns_changes_into_events(self):
        self.add_issue(1)
        self.add_issue(2)
        snap = str(self.root / "snap.json")
        first = [json.loads(x) for x in self.ghflow("watch", "--once", "--state", snap).stdout.splitlines()]
        self.assertEqual([e["event"] for e in first], ["seen", "seen"])
        self.assertEqual(self.ghflow("watch", "--once", "--state", snap).stdout, "")
        self.ghflow("claim", "1")
        self.add_pr(10, "Closes #1", merged=True)
        events = [json.loads(x) for x in self.ghflow("watch", "--once", "--state", snap).stdout.splitlines()]
        kinds = {(e["issue"], e["event"]) for e in events}
        self.assertIn((1, "state"), kinds)
        self.assertIn((1, "pr"), kinds)
        self.assertNotIn(2, {e["issue"] for e in events})

    def test_init_creates_missing_labels_once(self):
        self.assertEqual(self.ghflow("init").returncode, 0)
        self.assertEqual(self.ghflow("init").returncode, 0)
        self.assertEqual(sorted(self.state()["repo_labels"]), ["done", "in-progress", "review"])


if __name__ == "__main__":
    unittest.main()
