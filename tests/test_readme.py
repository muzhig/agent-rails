"""Execute the README's checklist example after a fresh local install."""

import os
from pathlib import Path
import re
import subprocess
import tempfile
import unittest

KIT = Path(__file__).resolve().parent.parent


class TestReadmeQuickstart(unittest.TestCase):
    def test_checklist_example_runs_without_path_setup(self):
        readme = (KIT / "README.md").read_text()
        blocks = re.findall(r"```bash\n(.*?)```", readme, re.S)
        commands = [line.split("# the runner", 1)[0].split("# exit", 1)[0].rstrip()
                    for block in blocks for line in block.splitlines()
                    if re.match(r"(?:\.agent-rails/scripts/)?checklist (init|verify|status)\b", line)]
        self.assertEqual(len(commands), 3, "Keep the checklist quickstart executable")
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "repo"
            root.mkdir()
            subprocess.run(["git", "init", "-q", str(root)], check=True)
            subprocess.run([str(KIT / "scripts/install"), str(root)], check=True,
                           capture_output=True, text=True)
            # The example assumes Python sources; its comment asks the user to do the work.
            (root / "src").mkdir()
            source = root / "src/app.py"
            source.write_text('print("hello")\n')
            env = {**os.environ, "AGENT_RAILS_KEY": str(Path(temp) / "key")}
            env.pop("AGENT_RAILS_DIR", None)
            # Do not inherit a developer's manually configured kit PATH.
            env["PATH"] = os.pathsep.join(p for p in env.get("PATH", "").split(os.pathsep)
                                         if not (Path(p) / "checklist").exists())
            for command in commands:
                if "checklist verify" in command:
                    source.write_text('# SPDX-License-Identifier: MIT\n' + source.read_text())
                result = subprocess.run(command, shell=True, cwd=root, env=env,
                                        capture_output=True, text=True)
                self.assertEqual(result.returncode, 0,
                                 f"README command failed: {command}\n{result.stdout}{result.stderr}")


if __name__ == "__main__":
    unittest.main()
