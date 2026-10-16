"""The checklist comes from the data and only the runner's receipts count."""

import hashlib
import hmac
import json
import os
import unittest

from helpers import RepoCase


class ChecklistCase(RepoCase):

    def setUp(self):
        super().setUp()
        (self.root / "posts").mkdir()
        for name in ("a", "b", "c"):
            (self.root / "posts" / f"{name}.md").write_text(f"# {name}\n")

    def checklist(self, *args):
        return self.run_script("scripts/checklist", *args)

    def init_posts(self):
        proc = self.checklist("init", "license", "--glob", "posts/*.md", "--check", "grep -q '^License: MIT' {item}")
        self.assertEqual(proc.returncode, 0, proc.stderr)

    def stamp(self, name):
        path = self.root / "posts" / f"{name}.md"
        path.write_text(path.read_text() + "License: MIT\n")

    def status(self):
        proc = self.checklist("status", "--json")
        return proc.returncode, json.loads(proc.stdout)[0]

    def receipts(self):
        return self.root / ".rails" / "receipts" / "license"


class TestItemsFromData(ChecklistCase):

    def test_items_come_from_the_glob(self):
        self.init_posts()
        definition = json.loads((self.root / ".rails" / "checklists" / "license.json").read_text())
        self.assertEqual(definition["items"], ["posts/a.md", "posts/b.md", "posts/c.md"])

    def test_file_added_after_init_is_open(self):
        self.init_posts()
        (self.root / "posts" / "d.md").write_text("# d\n")
        _, report = self.status()
        self.assertIn("posts/d.md", report["open"])
        self.assertEqual(report["added_since_init"], ["posts/d.md"])

    def test_empty_source_refused(self):
        proc = self.checklist("init", "x", "--glob", "nothing/*.md", "--check", "true")
        self.assertEqual(proc.returncode, 3)

    def test_items_from_issue_label(self):
        self.add_issue(4, labels=["migrate"])
        self.add_issue(7, labels=["migrate"])
        self.add_issue(9, labels=["other"])
        proc = self.checklist("init", "mig", "--issues-label", "migrate", "--check", "true")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        definition = json.loads((self.root / ".rails" / "checklists" / "mig.json").read_text())
        self.assertEqual(definition["items"], ["4", "7"])

    def test_items_from_command(self):
        proc = self.checklist("init", "svc", "--from-cmd", "printf 'api\\nweb\\napi\\n'", "--check", "true")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        definition = json.loads((self.root / ".rails" / "checklists" / "svc.json").read_text())
        self.assertEqual(definition["items"], ["api", "web"])

    def test_verify_rejects_an_item_not_in_the_data(self):
        self.init_posts()
        proc = self.checklist("verify", "license", "posts/zzz.md")
        self.assertEqual(proc.returncode, 1)
        self.assertIn("not an item of this list", proc.stdout)


class TestReceipts(ChecklistCase):

    def test_skipped_item_stays_open(self):
        self.init_posts()
        self.stamp("a")
        self.stamp("c")
        proc = self.checklist("verify", "license", "--all")
        self.assertEqual(proc.returncode, 1)
        code, report = self.status()
        self.assertEqual(code, 2)
        self.assertEqual(report["open"], ["posts/b.md"])
        self.assertEqual(report["done"], 2)

    def test_all_done_exits_zero(self):
        self.init_posts()
        for name in "abc":
            self.stamp(name)
        self.assertEqual(self.checklist("verify", "license", "--all").returncode, 0)
        code, report = self.status()
        self.assertEqual((code, report["open"]), (0, []))

    def test_failing_check_writes_no_receipt(self):
        self.init_posts()
        self.checklist("verify", "license", "posts/a.md")
        self.assertFalse(any(self.receipts().glob("*.json")))

    def test_hand_written_receipt_is_forged(self):
        self.init_posts()
        definition = json.loads((self.root / ".rails" / "checklists" / "license.json").read_text())
        item = "posts/b.md"
        fields = {"list": "license", "created": definition["created"], "item": item, "check": definition["check"],
                  "exit": 0, "at": "2026-10-12T00:00:00+00:00",
                  "content_sha": hashlib.sha256((self.root / item).read_bytes()).hexdigest()}
        self.receipts().mkdir(parents=True)
        rid = hashlib.sha256(item.encode()).hexdigest()[:16]
        wrong_key = hmac.new(b"guess", json.dumps(fields, sort_keys=True, separators=(",", ":")).encode(), hashlib.sha256).hexdigest()
        (self.receipts() / f"{rid}.json").write_text(json.dumps({**fields, "sig": wrong_key}))
        code, report = self.status()
        self.assertEqual(code, 2)
        self.assertIn(item, report["forged"])

    def test_receipt_copied_to_another_item_is_forged(self):
        self.init_posts()
        self.stamp("a")
        self.checklist("verify", "license", "posts/a.md")
        src = self.receipts() / f"{hashlib.sha256(b'posts/a.md').hexdigest()[:16]}.json"
        dst = self.receipts() / f"{hashlib.sha256(b'posts/b.md').hexdigest()[:16]}.json"
        dst.write_text(src.read_text())
        _, report = self.status()
        self.assertIn("posts/b.md", report["forged"])

    def test_edit_after_receipt_goes_stale(self):
        self.init_posts()
        self.stamp("a")
        self.checklist("verify", "license", "posts/a.md")
        (self.root / "posts" / "a.md").write_text("# a\nrewritten\nLicense: MIT\n")
        _, report = self.status()
        self.assertIn("posts/a.md", report["stale"])

    def test_receipt_for_an_older_check_is_rejected(self):
        self.init_posts()
        self.stamp("a")
        self.checklist("verify", "license", "posts/a.md")
        path = self.root / ".rails" / "checklists" / "license.json"
        definition = json.loads(path.read_text())
        definition["check"] = "true"
        path.write_text(json.dumps(definition))
        _, report = self.status()
        self.assertIn("posts/a.md", report["forged"])

    def test_failed_recheck_of_a_command_item_reopens_it(self):
        proc = self.checklist("init", "svc", "--from-cmd", "echo api", "--check", "test -f healthy")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        (self.root / "healthy").write_text("")
        self.assertEqual(self.checklist("verify", "svc", "api").returncode, 0)
        (self.root / "healthy").unlink()
        self.assertEqual(self.checklist("verify", "svc", "api").returncode, 1)
        proc = self.checklist("status", "svc", "--json")
        self.assertEqual(proc.returncode, 2)
        self.assertEqual(json.loads(proc.stdout)[0]["open"], ["api"])

    def test_failed_recheck_of_an_issue_item_reopens_it(self):
        self.add_issue(4, labels=["migrate"])
        self.checklist("init", "mig", "--issues-label", "migrate", "--check", "test -f migrated-{item}")
        (self.root / "migrated-4").write_text("")
        self.assertEqual(self.checklist("verify", "mig", "4").returncode, 0)
        (self.root / "migrated-4").unlink()
        self.checklist("verify", "mig", "4")
        proc = self.checklist("status", "mig", "--json")
        self.assertEqual((proc.returncode, json.loads(proc.stdout)[0]["open"]), (2, ["4"]))

    def test_failed_recheck_with_an_external_dependency_reopens_a_file_item(self):
        self.checklist("init", "dep", "--glob", "posts/a.md", "--check", "test -f build.ok")
        (self.root / "build.ok").write_text("")
        self.assertEqual(self.checklist("verify", "dep", "posts/a.md").returncode, 0)
        (self.root / "build.ok").unlink()
        self.checklist("verify", "dep", "posts/a.md")
        proc = self.checklist("status", "dep", "--json")
        self.assertEqual((proc.returncode, json.loads(proc.stdout)[0]["open"]), (2, ["posts/a.md"]))

    def test_key_lives_outside_the_repo_with_0600(self):
        self.init_posts()
        key = self.env["AGENT_RAILS_KEY"]
        self.assertEqual(os.stat(key).st_mode & 0o777, 0o600)
        self.assertFalse(key.startswith(str(self.root)))


if __name__ == "__main__":
    unittest.main()
