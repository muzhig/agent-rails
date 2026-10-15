"""A broken CLI must never look like a successful fail-open scenario."""
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).parent / 'harness'))
import codex_e2e


class TestCodexHarnessHealth(unittest.TestCase):
    def run_session(self, returncode=0, requests=True, completed=True):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            if requests:
                (base / 'model.log').write_text(json.dumps({'newest_input': 'SCENARIO'}) + '\n')
            proc = Mock(returncode=returncode, stderr='CLI startup diagnostic',
                        stdout=json.dumps({'type': 'turn.completed'}) if completed else '')
            server = Mock()
            server.stderr.readline.return_value = 'ready\n'
            with patch.object(codex_e2e.subprocess, 'Popen', return_value=server), \
                 patch.object(codex_e2e.subprocess, 'run', return_value=proc):
                return codex_e2e.run_codex(base, base, [], 'SCENARIO', 'codex')

    def test_nonzero_cli_exit_is_failure(self):
        with self.assertRaisesRegex(AssertionError, 'CLI startup diagnostic'):
            self.run_session(returncode=1, requests=False, completed=False)

    def test_no_model_request_is_failure(self):
        with self.assertRaisesRegex(AssertionError, 'model request'):
            self.run_session(requests=False)

    def test_incomplete_turn_is_failure(self):
        with self.assertRaisesRegex(AssertionError, 'turn.completed'):
            self.run_session(completed=False)

    def test_healthy_session_is_accepted(self):
        events, requests = self.run_session()
        self.assertEqual(events[0]['type'], 'turn.completed')
        self.assertEqual(len(requests), 1)
