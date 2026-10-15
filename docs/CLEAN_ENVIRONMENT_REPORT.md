# agent-rails clean-environment report


## Clean-environment run (2026-10-15)

Fresh authenticated clone of `muzhig/agent-rails`, PR #3 branch `build-kit`, starting at `a02069f41c18c0bad1c0153110d3b2847bbff7a9`. No push, merge, repository-setting change, or live GitHub write was performed. Existing machine tools were inventoried; missing/mismatched test CLIs were installed in a separate prefix. This is a fresh checkout and fresh test fixtures inside a managed Debian environment, not a claim that the host itself was newly provisioned.

Earlier results above were treated as historical claims, not evidence for this run. All output below was generated during this run. Model behavior is only claimed where a CLI actually reached the model endpoint. The local scripted model is explicitly not a real model.

### Result table

| Check | How | Result | Observed evidence |
|---|---|---|---|
| Versions | version commands plus OS files | Recorded | Debian 13.6 x86_64; Python 3.12.14; Node v24.19.0; Git 2.52.0; initial Claude absent; initial Codex 0.159.2 |
| Pinned CLIs | npm packages matching earlier TESTED.md | Installed | Claude 2.1.280; Codex 0.160.0; `added 4 packages in 20s` |
| Unit baseline | `python3 -m unittest discover -s tests -v` | Pass | `Ran 63 tests in 22.835s`, `OK` |
| Unit after fixes | same command | Pass | `Ran 68 tests in 27.848s`, `OK` |
| Claude scripted model | `python3 tests/harness/claude_e2e.py` | Pass, 5/5 baseline and fixed | Every observed scenario JSON line is pasted below |
| Codex scripted model | `python3 tests/harness/codex_e2e.py` | Blocked before model | Baseline incorrectly reported 2 passes; fixed harness reports all 6 failures with startup diagnostics, JSON pasted below |
| Compatible Codex sandbox attempt | workspace-write/on-request | Blocked before model | `app-server socket directory must be a user-owned directory with mode 0700` |
| Newcomer walkthrough | fresh git repo, ten posts, installed kit, direct payloads | All required core cases pass | Detailed check/how/result/output table and raw transcript below |
| README executable checklist example | exact original command lines | Bug fixed | Each exited 127, `checklist: command not found`; README-derived regression red then green |
| Real Codex prerequisite | login status, exec probes, normal interactive start | Blocked | `Logged in using ChatGPT`; startup `Read-only file system (os error 30)` |
| Public clone command | exact URL with noninteractive terminal | Failed before auth | `fatal: could not read Username for 'https://github.com': terminal prompts disabled`, exit 128; private pre-publication access, not evidence that public clone will fail after publication |

### Bugs and fixes

1. **False positive Codex harness results when the CLI never runs.** In this environment the original `fail_open` scenario printed `ok: true`, `model_requests: 0`, `turn_completed: false`; `untrusted_hooks_do_not_run` also printed success. Reproduce by running the harness with a CLI that exits before contacting the local server (the real managed-environment failure here does this). Commit `832d159` checks exit status, at least one observed model request, and a `turn.completed` event before scenario assertions. Three regression cases fail on the original code; all four health tests pass after the fix. This prevents lack of execution from proving fail-open or untrusted-hook semantics. It does not fix the host's Codex startup restrictions.
2. **README checklist commands are not runnable after install.** The installer does not add scripts to PATH. All three original bare `checklist` example lines exit 127. Commit `29e0825` uses installed paths, explains prerequisites and sample files, and adds a test extracting and executing the README commands against a fresh installation. Actual red/green output is pasted below.

### Versions and CLI installation

The requested global npm install failed because `/home/agent/.local/lib` could not be created. Used isolated writable prefix `/tmp/agent-rails-cli` and cache `/tmp/agent-rails-npm-cache`, then prepended `/tmp/agent-rails-cli/bin` to PATH for the harness runs. No system-wide CLI was replaced. Install command:

```sh
npm i -g --prefix /tmp/agent-rails-cli --cache /tmp/agent-rails-npm-cache @anthropic-ai/claude-code@2.1.280 @openai/codex@0.160.0
```

#### Initial versions

```text
Thu Oct 15 06:16:16 UTC 2026
PRETTY_NAME="Debian GNU/Linux 13 (trixie)"
NAME="Debian GNU/Linux"
VERSION_ID="13"
VERSION="13 (trixie)"
VERSION_CODENAME=trixie
DEBIAN_VERSION_FULL=13.6
ID=debian
HOME_URL="https://www.debian.org/"
SUPPORT_URL="https://www.debian.org/support"
BUG_REPORT_URL="https://bugs.debian.org/"
Linux 468072cbbe4d 6.18.44 #1 SMP Sat Sep 26 20:02:31 UTC 2026 x86_64 GNU/Linux
Python 3.12.14
v24.19.0
git version 2.52.0
/bin/bash: line 1: claude: command not found
WARNING: proceeding, even though we could not create PATH aliases: Read-only file system (os error 30)
codex-cli 0.159.2
```

#### Global install attempt

```text
npm warn Unknown env config "http-proxy". This will stop working in the next major version of npm.
npm error code ENOENT
npm error syscall mkdir
npm error path /home/agent/.local/lib
npm error errno -2
npm error enoent ENOENT: no such file or directory, mkdir '/home/agent/.local/lib'
npm error enoent This is related to npm not being able to find a file.
npm error enoent
npm error Log files were not written due to an error writing to the directory: /home/agent/.npm/_logs
npm error You can rerun the command with `--loglevel=verbose` to see the logs in your terminal
exit=254
```

#### Isolated install

```text
npm warn Unknown env config "http-proxy". This will stop working in the next major version of npm.

added 4 packages in 20s
npm notice
npm notice New major version of npm available! 11.9.0 -> 12.2.0
npm notice Changelog: https://github.com/npm/cli/releases/tag/v12.2.0
npm notice To update run: npm install -g npm@12.2.0
npm notice
```

#### Pinned versions

```text
2.1.280 (Claude Code)
WARNING: proceeding, even though we could not create PATH aliases: Read-only file system (os error 30)
codex-cli 0.160.0
```

#### Public clone attempt

```text
Cloning into 'agent-rails'...
fatal: could not read Username for 'https://github.com': terminal prompts disabled
exit=128
```

### Unit test summaries

unit-baseline.txt
```text

----------------------------------------------------------------------
Ran 63 tests in 22.835s

OK
```

unit-fixed.txt
```text

----------------------------------------------------------------------
Ran 68 tests in 27.848s

OK
```

Full verbose outputs are preserved alongside this report in `docs/evidence/clean-2026-10-15/`.

#### Claude baseline: every scenario

```text
{"scenario": "stop_blocks", "ok": true, "seconds": 2.6, "stop_hook_feedback": ["Stop hook feedback:\n3 checklist item(s) have no valid receipt: stamp: posts/a.md (no receipt); stamp: posts/b.md (no receipt); stamp: posts/c.md (no receipt). Finish each one, then run `checklist verify <list> <item>` so the runner writes its receipt. Block 1 of 3."], "final_open": [], "result": "success"}
{"scenario": "guard_and_wrapper", "ok": true, "seconds": 1.5, "pretooluse_denial": "ERROR Change workflow labels with `ghflow claim|review|rework|done <issue>`, not raw gh; ghflow checks the PR, the results comment and the merge.", "wrapper_refusal": "ERROR Exit code 3\n{\"issue\": 1, \"state\": \"in-progress\", \"assignee\": \"alice\"}\nghflow: refused: no open or merged PR links #1 (put 'Closes #1' in the PR body)", "labels_after": ["in-progress"], "raw_gh_issue_edit_calls": []}
{"scenario": "forged_receipt_and_cap", "ok": true, "seconds": 2.2, "blocks": 3, "first_block": "Stop hook feedback:\n3 checklist item(s) have no valid receipt: stamp: posts/a.md (no receipt); stamp: posts/b.md (forged receipt); stamp: posts/c.md (no receipt). Finish each one, then run `checklist verify <list> <item>` so the runner writes its receipt. Block 1 of 3.", "cap_system_message_seen": true, "forged": ["posts/b.md"], "result": "success"}
{"scenario": "fail_open", "ok": true, "seconds": 1.3, "stop_hook_feedback": [], "result": "success", "hook_error_events": ["stop-hook-error"]}
{"scenario": "read_log", "ok": true, "seconds": 2.2, "reads_log": [{"at": "2026-10-15T06:17:38+00:00", "session": "01367ce4-bbba-43a8-a4bb-dfc250e16211", "tool": "Read", "path": "docs/guide.md"}], "results_comment": "<!-- agent-rails:result -->\nStamped the posts.\n\n**Docs read (from the hook log):**\n- `docs/guide.md`\n"}
```

#### Claude after fixes: every scenario

```text
{"scenario": "stop_blocks", "ok": true, "seconds": 1.3, "stop_hook_feedback": ["Stop hook feedback:\n3 checklist item(s) have no valid receipt: stamp: posts/a.md (no receipt); stamp: posts/b.md (no receipt); stamp: posts/c.md (no receipt). Finish each one, then run `checklist verify <list> <item>` so the runner writes its receipt. Block 1 of 3."], "final_open": [], "result": "success"}
{"scenario": "guard_and_wrapper", "ok": true, "seconds": 2.3, "pretooluse_denial": "ERROR Change workflow labels with `ghflow claim|review|rework|done <issue>`, not raw gh; ghflow checks the PR, the results comment and the merge.", "wrapper_refusal": "ERROR Exit code 3\n{\"issue\": 1, \"state\": \"in-progress\", \"assignee\": \"alice\"}\nghflow: refused: no open or merged PR links #1 (put 'Closes #1' in the PR body)", "labels_after": ["in-progress"], "raw_gh_issue_edit_calls": []}
{"scenario": "forged_receipt_and_cap", "ok": true, "seconds": 2.3, "blocks": 3, "first_block": "Stop hook feedback:\n3 checklist item(s) have no valid receipt: stamp: posts/a.md (no receipt); stamp: posts/b.md (forged receipt); stamp: posts/c.md (no receipt). Finish each one, then run `checklist verify <list> <item>` so the runner writes its receipt. Block 1 of 3.", "cap_system_message_seen": true, "forged": ["posts/b.md"], "result": "success"}
{"scenario": "fail_open", "ok": true, "seconds": 1.1, "stop_hook_feedback": [], "result": "success", "hook_error_events": ["stop-hook-error"]}
{"scenario": "read_log", "ok": true, "seconds": 2.6, "reads_log": [{"at": "2026-10-15T06:20:24+00:00", "session": "32f56673-f5e2-4717-aea7-08ef9501bc84", "tool": "Read", "path": "docs/guide.md"}], "results_comment": "<!-- agent-rails:result -->\nStamped the posts.\n\n**Docs read (from the hook log):**\n- `docs/guide.md`\n"}
```

#### Codex baseline: every scenario (two false positives)

```text
{"scenario": "stop_blocks", "ok": false, "why": "[]", "dir": "/tmp/rails-cx-stop_blocks-dmitfs3q"}
{"scenario": "guard_and_wrapper", "ok": false, "why": "[]", "dir": "/tmp/rails-cx-guard_and_wrapper-zbdvjw5f"}
{"scenario": "forged_receipt_and_cap", "ok": false, "why": "[]", "dir": "/tmp/rails-cx-forged_receipt_and_cap-77ptueih"}
{"scenario": "fail_open", "ok": true, "seconds": 0.4, "hook_prompts": [], "model_requests": 0, "turn_completed": false}
{"scenario": "read_log", "ok": false, "why": "([], [])", "dir": "/tmp/rails-cx-read_log-qjhcm_sr"}
{"scenario": "untrusted_hooks_do_not_run", "ok": true, "seconds": 0.4, "hook_prompts": [], "codex_notices": []}
```

#### Codex after fix: every scenario (all blocked)

```text
{"scenario": "stop_blocks", "ok": false, "why": "Codex exited 1: WARNING: proceeding, even though we could not create PATH aliases: Refusing to create helper binaries under temporary dir \"/tmp\" (codex_home: AbsolutePathBuf(\"/tmp/rails-cx-stop_blocks-y8bvorkc/codex-home\"))\nError: `approval_policy = \"never\"` cannot be used because requirements do not allow `sandbox_mode = \"danger-full-access\"`; Codex would fall back to read-only permissions with approvals disabled. Choose an `approval_policy` based on what you need, such as `on-request`, or choose an allowed sandbox mode.\n", "dir": "/tmp/rails-cx-stop_blocks-y8bvorkc"}
{"scenario": "guard_and_wrapper", "ok": false, "why": "Codex exited 1: WARNING: proceeding, even though we could not create PATH aliases: Refusing to create helper binaries under temporary dir \"/tmp\" (codex_home: AbsolutePathBuf(\"/tmp/rails-cx-guard_and_wrapper-7_gp8wd9/codex-home\"))\nError: `approval_policy = \"never\"` cannot be used because requirements do not allow `sandbox_mode = \"danger-full-access\"`; Codex would fall back to read-only permissions with approvals disabled. Choose an `approval_policy` based on what you need, such as `on-request`, or choose an allowed sandbox mode.\n", "dir": "/tmp/rails-cx-guard_and_wrapper-7_gp8wd9"}
{"scenario": "forged_receipt_and_cap", "ok": false, "why": "Codex exited 1: WARNING: proceeding, even though we could not create PATH aliases: Refusing to create helper binaries under temporary dir \"/tmp\" (codex_home: AbsolutePathBuf(\"/tmp/rails-cx-forged_receipt_and_cap-rtmkwxmf/codex-home\"))\nError: `approval_policy = \"never\"` cannot be used because requirements do not allow `sandbox_mode = \"danger-full-access\"`; Codex would fall back to read-only permissions with approvals disabled. Choose an `approval_policy` based on what you need, such as `on-request`, or choose an allowed sandbox mode.\n", "dir": "/tmp/rails-cx-forged_receipt_and_cap-rtmkwxmf"}
{"scenario": "fail_open", "ok": false, "why": "Codex exited 1: WARNING: proceeding, even though we could not create PATH aliases: Refusing to create helper binaries under temporary dir \"/tmp\" (codex_home: AbsolutePathBuf(\"/tmp/rails-cx-fail_open-8qbdno_3/codex-home\"))\nError: `approval_policy = \"never\"` cannot be used because requirements do not allow `sandbox_mode = \"danger-full-access\"`; Codex would fall back to read-only permissions with approvals disabled. Choose an `approval_policy` based on what you need, such as `on-request`, or choose an allowed sandbox mode.\n", "dir": "/tmp/rails-cx-fail_open-8qbdno_3"}
{"scenario": "read_log", "ok": false, "why": "Codex exited 1: WARNING: proceeding, even though we could not create PATH aliases: Refusing to create helper binaries under temporary dir \"/tmp\" (codex_home: AbsolutePathBuf(\"/tmp/rails-cx-read_log-p6w9asll/codex-home\"))\nError: `approval_policy = \"never\"` cannot be used because requirements do not allow `sandbox_mode = \"danger-full-access\"`; Codex would fall back to read-only permissions with approvals disabled. Choose an `approval_policy` based on what you need, such as `on-request`, or choose an allowed sandbox mode.\n", "dir": "/tmp/rails-cx-read_log-p6w9asll"}
{"scenario": "untrusted_hooks_do_not_run", "ok": false, "why": "Codex exited 1: WARNING: proceeding, even though we could not create PATH aliases: Refusing to create helper binaries under temporary dir \"/tmp\" (codex_home: AbsolutePathBuf(\"/tmp/rails-cx-untrusted_hooks_do_not_run-1y18uz98/codex-home\"))\nError: `approval_policy = \"never\"` cannot be used because requirements do not allow `sandbox_mode = \"danger-full-access\"`; Codex would fall back to read-only permissions with approvals disabled. Choose an `approval_policy` based on what you need, such as `on-request`, or choose an allowed sandbox mode.\n", "dir": "/tmp/rails-cx-untrusted_hooks_do_not_run-1y18uz98"}
```

#### Compatible sandbox diagnostic

```text
command: ['/tmp/agent-rails-cli/bin/codex', '-c', 'approval_policy="on-request"', '-c', 'sandbox_mode="workspace-write"', 'exec', '--dangerously-bypass-hook-trust', '--json', 'SCENARIO stamp every post']
exit: 1 stderr: WARNING: proceeding, even though we could not create PATH aliases: Refusing to create helper binaries under temporary dir "/tmp" (codex_home: AbsolutePathBuf("/tmp/rails-compatible-o5om_wk2/codex-home"))
Reading additional input from stdin...
2026-10-15T06:19:12.240004Z ERROR codex_core::session: Failed to create session: failed to load AGENTS.md instructions for environment `local`: fs sandbox helper failed with status exit status: 1: error building bubblewrap command: app-server socket directory must be a user-owned directory with mode 0700
Error: thread/start: thread/start failed: error creating thread: failed to load AGENTS.md instructions for environment `local`: fs sandbox helper failed with status exit status: 1: error building bubblewrap command: app-server socket directory must be a user-owned directory with mode 0700 (code -32603)
 stdout: 
AssertionError Codex exited 1: WARNING: proceeding, even though we could not create PATH aliases: Refusing to create helper binaries under temporary dir "/tmp" (codex_home: AbsolutePathBuf("/tmp/rails-compatible-o5om_wk2/codex-home"))
Reading additional input from stdin...
2026-10-15T06:19:12.240004Z ERROR codex_core::session: Failed to create session: failed to load AGENTS.md instructions for environment `local`: fs sandbox helper failed with status exit status: 1: error building bubblewrap command: app-server socket directory must be a user-owned directory with mode 0700
Error: thread/start: thread/start failed: error creating thread: failed to load AGENTS.md instructions for environment `local`: fs sandbox helper failed with status exit status: 1: error building bubblewrap command: app-server socket directory must be a user-owned directory with mode 0700 (code -32603)

```

#### Harness regression before fix

```text
test_healthy_session_is_accepted (test_harness_health.TestCodexHarnessHealth.test_healthy_session_is_accepted) ... ok
test_incomplete_turn_is_failure (test_harness_health.TestCodexHarnessHealth.test_incomplete_turn_is_failure) ... FAIL
test_no_model_request_is_failure (test_harness_health.TestCodexHarnessHealth.test_no_model_request_is_failure) ... FAIL
test_nonzero_cli_exit_is_failure (test_harness_health.TestCodexHarnessHealth.test_nonzero_cli_exit_is_failure) ... FAIL

======================================================================
FAIL: test_incomplete_turn_is_failure (test_harness_health.TestCodexHarnessHealth.test_incomplete_turn_is_failure)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/4feb111f0821/agent-rails-clean/tests/test_harness_health.py", line 36, in test_incomplete_turn_is_failure
    with self.assertRaisesRegex(AssertionError, 'turn.completed'):
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: AssertionError not raised

======================================================================
FAIL: test_no_model_request_is_failure (test_harness_health.TestCodexHarnessHealth.test_no_model_request_is_failure)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/4feb111f0821/agent-rails-clean/tests/test_harness_health.py", line 32, in test_no_model_request_is_failure
    with self.assertRaisesRegex(AssertionError, 'model request'):
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: AssertionError not raised

======================================================================
FAIL: test_nonzero_cli_exit_is_failure (test_harness_health.TestCodexHarnessHealth.test_nonzero_cli_exit_is_failure)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/4feb111f0821/agent-rails-clean/tests/test_harness_health.py", line 28, in test_nonzero_cli_exit_is_failure
    with self.assertRaisesRegex(AssertionError, 'CLI startup diagnostic'):
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: AssertionError not raised

----------------------------------------------------------------------
Ran 4 tests in 0.007s

FAILED (failures=3)
```

#### Harness regression after fix

```text
test_healthy_session_is_accepted (test_harness_health.TestCodexHarnessHealth.test_healthy_session_is_accepted) ... ok
test_incomplete_turn_is_failure (test_harness_health.TestCodexHarnessHealth.test_incomplete_turn_is_failure) ... ok
test_no_model_request_is_failure (test_harness_health.TestCodexHarnessHealth.test_no_model_request_is_failure) ... ok
test_nonzero_cli_exit_is_failure (test_harness_health.TestCodexHarnessHealth.test_nonzero_cli_exit_is_failure) ... ok

----------------------------------------------------------------------
Ran 4 tests in 0.006s

OK
```

#### README regression before and after fix

```text
test_checklist_example_runs_without_path_setup (test_readme.TestReadmeQuickstart.test_checklist_example_runs_without_path_setup) ... FAIL

======================================================================
FAIL: test_checklist_example_runs_without_path_setup (test_readme.TestReadmeQuickstart.test_checklist_example_runs_without_path_setup)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/4feb111f0821/agent-rails-clean/tests/test_readme.py", line 41, in test_checklist_example_runs_without_path_setup
    self.assertEqual(result.returncode, 0,
AssertionError: 127 != 0 : README command failed: checklist init headers --glob 'src/**/*.py' --check "head -1 {item} | grep -q 'SPDX-License-Identifier'"
/bin/sh: 1: checklist: not found


----------------------------------------------------------------------
Ran 1 test in 0.042s

FAILED (failures=1)

AFTER README FIX
test_checklist_example_runs_without_path_setup (test_readme.TestReadmeQuickstart.test_checklist_example_runs_without_path_setup) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.285s

OK
```

### Walkthrough and README audit

###### Independent newcomer walkthrough

Date: 2026-10-15. Installed from the clean checkout into a separate `git init` repository `/tmp/agent-rails-new-user-20261015/repo`, populated with ten small `posts/01.md` … `posts/10.md` and `docs/guide.md`. The real install/checklist/hook/ghflow scripts ran. For GitHub operations only, `AGENT_RAILS_GH` pointed at `tests/fake_gh.py`, with a new local JSON state. No live GitHub label, issue, PR, or merge was changed. The receipt key was explicitly isolated outside the fixture repository at `/tmp/agent-rails-new-user-20261015/keys/receipt.key`. Full commands, stdin, stdout, stderr and exit statuses are in [walkthrough.txt](walkthrough.txt).

| Check | How | Result | Observed output excerpt |
|---|---|---|---|
| Fresh repo | `git init`, create ten posts + guide, run installer | Pass | `Initialized empty Git repository in /tmp/agent-rails-new-user-20261015/repo/.git/`; `installed agent-rails into /tmp/agent-rails-new-user-20261015/repo` |
| Label initialization | installed `ghflow init`, fake gh | Pass, local fake only | `{"labels": ["in-progress", "review", "done"]}`, exit 0 |
| Literal README checklist example | run all 3 lines before modifying PATH | Fail, fixed | `/bin/bash: line 1: checklist: command not found`, exit 127 for all three |
| Ten-post checklist | installed `checklist init review --glob 'posts/*.md' --check "head -1 {item} \| grep -q '^<!-- reviewed: '"` | Pass | `{"name": "review", "items": 10}` |
| Verify three posts | add reviewed first lines, verify each | Pass | `{"item": "posts/01.md", "ok": true}`; corresponding lines for 02 and 03 |
| Incomplete status | installed `checklist status` | Pass | `review: 3/10 done`, seven open paths, exit 2 |
| Hand-written receipt | write unsigned receipt at post 04 receipt filename | Pass | `"forged": ["posts/04.md", "posts/05.md"]` (combined report with copied receipt) |
| Copied receipt | copy valid post 01 receipt to post 05 receipt filename | Pass | same forged array includes `posts/05.md` |
| Edited verified file | append content to post 02 | Pass | `"stale": ["posts/02.md"]` |
| Failed recheck | remove post 03 header, run verify again | Pass | `{"item": "posts/03.md", "ok": false, "exit": 1, "stderr": ""}`, exit 1; status lists post 03 open, not stale |
| Stop blocks with names | tests-shaped Stop payload, same session, project env points at fixture | Pass | `"decision": "block"`; reason lists all nine remaining items with stale/forged/no receipt and `Block 1 of 3.` |
| Stop repeat cap | repeat same session, active=true on subsequent stops | Pass | third reason ends `Block 3 of 3.`; fourth: `{"systemMessage": "agent-rails: stop allowed after 3 blocks with 9 checklist items still open"}` |
| Corrupt checklist default | replace review.json with `{broken`, invoke hook | Script fail-open signal observed | stdout empty; traceback `json.decoder.JSONDecodeError: Expecting property name enclosed in double quotes: line 1 column 2 (char 1)`; exit 1. Direct invocation does not itself prove an actual CLI continued; CLI harness evidence is separate. |
| Corrupt fail-closed | same corruption with `AGENT_RAILS_FAIL_CLOSED=1` | Pass | stderr begins `agent-rails stop gate crashed, blocking once (fail-closed): checklist status failed (1):`; exit 2 first time, exit 1 with active=true next time |
| Raw label guard | PreToolUse Bash `gh issue edit 1 --add-label review` | Pass | `"permissionDecision": "deny"`, reason starts `Change workflow labels with` |
| Merge guard | PreToolUse Bash `gh pr merge 1` | Pass | `"permissionDecision": "deny"`, reason `Agents don't merge. Move the issue to review with` |
| Ordinary tool | PreToolUse Bash `printf hello` | Pass | empty stdout/stderr, exit 0 |
| Quoted forbidden commands | PreToolUse Write to docs/example.md with both forbidden commands in content | Pass | empty stdout/stderr, exit 0 |
| Read log | PostToolUse Read and Bash `cat docs/guide.md` | Pass | two actual log lines: `"tool": "Read", "path": "docs/guide.md"` and `"tool": "Bash", "path": "docs/guide.md"` |
| Corrected Python-source example | add scripts to PATH and create SPDX-stamped src/app.py | Pass | `{"name": "headers", "items": 1}`; `{"item": "src/app.py", "ok": true}`; `headers: 1/1 done` |
| Fake GitHub workflow | claim, logged docs read, fixture linked PR, result, review, status | Pass, fake only | `{"issue": 1, "state": "review", "prs": ["https://example.invalid/pr/2"]}`; status `"accept": true` |
| Done without merge | `ghflow done 1` before fake merge | Correct refusal | `ghflow: refused: no merged PR links #1; done is earned by a merge, not a report`, exit 3 |
| Done after merge fixture | change only fake PR JSON to merged, run done | Pass, fake only | `{"issue": 1, "state": "done", "merged": ["https://example.invalid/pr/2"]}` |
| Observer snapshot | `ghflow watch --once` | Pass, fake only | actual `"event": "seen", "state": "done"` JSON in transcript |
| Subdirectory use | invoke status and Stop from docs/, cwd payload docs/, no CLAUDE_PROJECT_DIR | Pass | status retains ten posts and exit 2; Stop blocks with all nine remaining items |

#### Bug fixed and regression

Commit `29e0825` (`docs: make installed checklist quickstart runnable without PATH setup`) fixes README commands that fail immediately in a clean installation. Installer leaves scripts in `.agent-rails/scripts` but README used bare `checklist`/`ghflow` without PATH setup. The three executable checklist example lines each actually exited 127. README now uses explicit installed paths and explains the example requires existing Python source files and the header-editing step. Installation prerequisites and the absence of PATH modification are explicit.

`tests/test_readme.py` extracts the README checklist commands and runs them in a newly initialized and installed repository without any developer `checklist` PATH entry. It creates the assumed Python file and performs the documented header work between initialization and verification. It failed on the original README (`AssertionError: 127 != 0`, `/bin/sh: 1: checklist: not found`), then passed after the wording/path fix. [readme-regression.txt](readme-regression.txt) contains both actual runs.

#### Additional README wording suggestions

- Clarify that the kit's Python code uses the standard library, but normal use also needs Git, a shell and the utilities referenced by each check; GitHub workflow needs installed/authenticated `gh`. Partly addressed in the prerequisite paragraph.
- “Appends every file the agent opens” is stronger than the implementation promises. Prefer “Records paths exposed by supported Read/Grep/Glob payloads and recognized shell readers; this is partial read evidence, not a complete filesystem audit.” Source inspection shows Grep/Glob log their input path rather than every result path; do not present glob enumeration as proven content reading.
- “At most 3 blocks” does not mean success after the cap: the warning explicitly preserves the nine outstanding items in this run. Existing warning/cap wording accurately reflects the observed behavior.
- Hook crash behavior distinguishes exit 1/error (default fail-open) from exit 2 (one fail-closed block); direct hook invocation proves emitted output/status only. Actual CLI behavior belongs in harness evidence.

#### Not run / scope boundaries

- Literal public `git clone https://github.com/muzhig/agent-rails.git`: not run by this walkthrough; coordinator supplied the fresh private `build-kit` checkout. This avoids accidentally testing the default branch instead of PR #3. Do not count public-clone usability as proven before publication.
- Literal `/path/to/your/repo`: a documentation placeholder, substituted with the actual fresh fixture path. Likewise N/F in command reference tables were instantiated as issue 1/result.txt.
- Live GitHub workflow writes: not run because unnecessary and outside the authorized mutation scope. The actual ghflow commands ran against the bundled fake, explicitly as labeled above.
- Unbounded `ghflow watch`: not run because it deliberately never exits; its `--help` and actual `--once` polling were run.
- Unit suite and CLI harness commands in the README Tests section: owned/run by the coordinator or other worker, not duplicated here. See their evidence, not an inferred pass from this walkthrough.
- Real-model Codex: owned by separate worker, not run by this walkthrough. Direct JSON-hook invocations above are not a simulation claimed as a real model test.

Coordinator update: the literal public clone URL was subsequently attempted and failed before authentication (output above). The authenticated branch-specific clone succeeded; public anonymous onboarding remains unverified until publication.

#### Full walkthrough commands and outputs

```text
Fresh independent fixture: /tmp/agent-rails-new-user-20261015/repo
Fake gh only: no live GitHub writes. AGENT_RAILS_KEY outside repository: /tmp/agent-rails-new-user-20261015/keys/receipt.key

$ git init
stdout:
Initialized empty Git repository in /tmp/agent-rails-new-user-20261015/repo/.git/
stderr:
hint: Using 'master' as the name for the initial branch. This default branch name
hint: will change to "main" in Git 3.0. To configure the initial branch name
hint: to use in all of your new repositories, which will suppress this warning,
hint: call:
hint:
hint: 	git config --global init.defaultBranch <name>
hint:
hint: Names commonly chosen instead of 'master' are 'main', 'trunk' and
hint: 'development'. The just-created branch can be renamed via this command:
hint:
hint: 	git branch -m <name>
hint:
hint: Disable this message with "git config set advice.defaultBranchName false"
exit=0
Fixture creation: wrote posts/01.md through posts/10.md and docs/guide.md.

$ /workspace/scratch/4feb111f0821/agent-rails-clean/scripts/install /tmp/agent-rails-new-user-20261015/repo
stdout:
wrote .claude/settings.json
wrote .codex/hooks.json
installed agent-rails into /tmp/agent-rails-new-user-20261015/repo
stderr:
exit=0

$ .agent-rails/scripts/ghflow init
stdout:
{"labels": ["in-progress", "review", "done"]}
stderr:
exit=0

$ checklist init headers --glob 'src/**/*.py' --check "head -1 {item} | grep -q 'SPDX-License-Identifier'"
stdout:
stderr:
/bin/bash: line 1: checklist: command not found
exit=127

$ checklist verify headers src/app.py
stdout:
stderr:
/bin/bash: line 1: checklist: command not found
exit=127

$ checklist status
stdout:
stderr:
/bin/bash: line 1: checklist: command not found
exit=127

$ .agent-rails/scripts/checklist init review --glob 'posts/*.md' --check "head -1 {item} | grep -q '^<!-- reviewed: '"
stdout:
{"name": "review", "items": 10}
stderr:
exit=0
Fixture edit: added reviewed header to posts/01.md

$ .agent-rails/scripts/checklist verify review posts/01.md
stdout:
{"item": "posts/01.md", "ok": true}
stderr:
exit=0
Fixture edit: added reviewed header to posts/02.md

$ .agent-rails/scripts/checklist verify review posts/02.md
stdout:
{"item": "posts/02.md", "ok": true}
stderr:
exit=0
Fixture edit: added reviewed header to posts/03.md

$ .agent-rails/scripts/checklist verify review posts/03.md
stdout:
{"item": "posts/03.md", "ok": true}
stderr:
exit=0

$ .agent-rails/scripts/checklist status
stdout:
review: 3/10 done
  open: posts/04.md
  open: posts/05.md
  open: posts/06.md
  open: posts/07.md
  open: posts/08.md
  open: posts/09.md
  open: posts/10.md
stderr:
exit=2

$ .agent-rails/scripts/checklist status --json
stdout:
[
  {
    "name": "review",
    "total": 10,
    "done": 3,
    "open": [
      "posts/04.md",
      "posts/05.md",
      "posts/06.md",
      "posts/07.md",
      "posts/08.md",
      "posts/09.md",
      "posts/10.md"
    ],
    "forged": [],
    "stale": [],
    "added_since_init": []
  }
]
stderr:
exit=2
Fixture tampering: handwritten receipt for posts/04.md, not generated by runner.
Fixture tampering: copied posts/01.md receipt bytes to receipt path of posts/05.md.
Fixture edit: appended content to verified posts/02.md.

$ .agent-rails/scripts/checklist status --json
stdout:
[
  {
    "name": "review",
    "total": 10,
    "done": 2,
    "open": [
      "posts/02.md",
      "posts/04.md",
      "posts/05.md",
      "posts/06.md",
      "posts/07.md",
      "posts/08.md",
      "posts/09.md",
      "posts/10.md"
    ],
    "forged": [
      "posts/04.md",
      "posts/05.md"
    ],
    "stale": [
      "posts/02.md"
    ],
    "added_since_init": []
  }
]
stderr:
exit=2
Fixture edit: removed review header from posts/03.md.

$ .agent-rails/scripts/checklist verify review posts/03.md
stdout:
{"item": "posts/03.md", "ok": false, "exit": 1, "stderr": ""}
stderr:
exit=1

$ .agent-rails/scripts/checklist status --json
stdout:
[
  {
    "name": "review",
    "total": 10,
    "done": 1,
    "open": [
      "posts/02.md",
      "posts/03.md",
      "posts/04.md",
      "posts/05.md",
      "posts/06.md",
      "posts/07.md",
      "posts/08.md",
      "posts/09.md",
      "posts/10.md"
    ],
    "forged": [
      "posts/04.md",
      "posts/05.md"
    ],
    "stale": [
      "posts/02.md"
    ],
    "added_since_init": []
  }
]
stderr:
exit=2

$ python3 .agent-rails/hooks/stop_gate.py
STDIN {"session_id": "walkthrough-cap", "hook_event_name": "Stop", "stop_hook_active": false, "cwd": "/"}
stdout:
{"decision": "block", "reason": "9 checklist item(s) have no valid receipt: review: posts/02.md (stale receipt); review: posts/03.md (no receipt); review: posts/04.md (forged receipt); review: posts/05.md (forged receipt); review: posts/06.md (no receipt); review: posts/07.md (no receipt); review: posts/08.md (no receipt); review: posts/09.md (no receipt); review: posts/10.md (no receipt). Finish each one, then run `checklist verify <list> <item>` so the runner writes its receipt. Block 1 of 3."}
stderr:
exit=0

$ python3 .agent-rails/hooks/stop_gate.py
STDIN {"session_id": "walkthrough-cap", "hook_event_name": "Stop", "stop_hook_active": true, "cwd": "/"}
stdout:
{"decision": "block", "reason": "9 checklist item(s) have no valid receipt: review: posts/02.md (stale receipt); review: posts/03.md (no receipt); review: posts/04.md (forged receipt); review: posts/05.md (forged receipt); review: posts/06.md (no receipt); review: posts/07.md (no receipt); review: posts/08.md (no receipt); review: posts/09.md (no receipt); review: posts/10.md (no receipt). Finish each one, then run `checklist verify <list> <item>` so the runner writes its receipt. Block 2 of 3."}
stderr:
exit=0

$ python3 .agent-rails/hooks/stop_gate.py
STDIN {"session_id": "walkthrough-cap", "hook_event_name": "Stop", "stop_hook_active": true, "cwd": "/"}
stdout:
{"decision": "block", "reason": "9 checklist item(s) have no valid receipt: review: posts/02.md (stale receipt); review: posts/03.md (no receipt); review: posts/04.md (forged receipt); review: posts/05.md (forged receipt); review: posts/06.md (no receipt); review: posts/07.md (no receipt); review: posts/08.md (no receipt); review: posts/09.md (no receipt); review: posts/10.md (no receipt). Finish each one, then run `checklist verify <list> <item>` so the runner writes its receipt. Block 3 of 3."}
stderr:
exit=0

$ python3 .agent-rails/hooks/stop_gate.py
STDIN {"session_id": "walkthrough-cap", "hook_event_name": "Stop", "stop_hook_active": true, "cwd": "/"}
stdout:
{"systemMessage": "agent-rails: stop allowed after 3 blocks with 9 checklist items still open"}
stderr:
exit=0
Fixture corruption: review.json = {broken
Overrides: {}

$ python3 .agent-rails/hooks/stop_gate.py
STDIN {"session_id": "corrupt", "hook_event_name": "Stop", "stop_hook_active": false, "cwd": "/"}
stdout:
stderr:
Traceback (most recent call last):
  File "/tmp/agent-rails-new-user-20261015/repo/.agent-rails/hooks/stop_gate.py", line 96, in <module>
    sys.exit(main())
             ^^^^^^
  File "/tmp/agent-rails-new-user-20261015/repo/.agent-rails/hooks/stop_gate.py", line 84, in main
    result = decide(payload)
             ^^^^^^^^^^^^^^^
  File "/tmp/agent-rails-new-user-20261015/repo/.agent-rails/hooks/stop_gate.py", line 62, in decide
    found = open_items(root)
            ^^^^^^^^^^^^^^^^
  File "/tmp/agent-rails-new-user-20261015/repo/.agent-rails/hooks/stop_gate.py", line 41, in open_items
    raise RuntimeError(f"checklist status failed ({proc.returncode}): {proc.stderr.strip()}")
RuntimeError: checklist status failed (1): Traceback (most recent call last):
  File "/tmp/agent-rails-new-user-20261015/repo/.agent-rails/scripts/checklist", line 268, in <module>
    sys.exit(main())
             ^^^^^^
  File "/tmp/agent-rails-new-user-20261015/repo/.agent-rails/scripts/checklist", line 264, in main
    return args.func(args)
           ^^^^^^^^^^^^^^^
  File "/tmp/agent-rails-new-user-20261015/repo/.agent-rails/scripts/checklist", line 221, in cmd_status
    reports = [status_of(name, key) for name in names]
               ^^^^^^^^^^^^^^^^^^^^
  File "/tmp/agent-rails-new-user-20261015/repo/.agent-rails/scripts/checklist", line 198, in status_of
    checklist = load_list(name)
                ^^^^^^^^^^^^^^^
  File "/tmp/agent-rails-new-user-20261015/repo/.agent-rails/scripts/checklist", line 112, in load_list
    return json.loads(list_path(name).read_text())
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/codex/runtimes/codex-primary-runtime/dependencies/python/lib/python3.12/json/__init__.py", line 346, in loads
    return _default_decoder.decode(s)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/codex/runtimes/codex-primary-runtime/dependencies/python/lib/python3.12/json/decoder.py", line 338, in decode
    obj, end = self.raw_decode(s, idx=_w(s, 0).end())
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/codex/runtimes/codex-primary-runtime/dependencies/python/lib/python3.12/json/decoder.py", line 354, in raw_decode
    obj, end = self.scan_once(s, idx)
               ^^^^^^^^^^^^^^^^^^^^^^
json.decoder.JSONDecodeError: Expecting property name enclosed in double quotes: line 1 column 2 (char 1)
exit=1
Overrides: {'AGENT_RAILS_FAIL_CLOSED': '1'}

$ python3 .agent-rails/hooks/stop_gate.py
STDIN {"session_id": "corrupt", "hook_event_name": "Stop", "stop_hook_active": false, "cwd": "/"}
stdout:
stderr:
agent-rails stop gate crashed, blocking once (fail-closed): checklist status failed (1): Traceback (most recent call last):
  File "/tmp/agent-rails-new-user-20261015/repo/.agent-rails/scripts/checklist", line 268, in <module>
    sys.exit(main())
             ^^^^^^
  File "/tmp/agent-rails-new-user-20261015/repo/.agent-rails/scripts/checklist", line 264, in main
    return args.func(args)
           ^^^^^^^^^^^^^^^
  File "/tmp/agent-rails-new-user-20261015/repo/.agent-rails/scripts/checklist", line 221, in cmd_status
    reports = [status_of(name, key) for name in names]
               ^^^^^^^^^^^^^^^^^^^^
  File "/tmp/agent-rails-new-user-20261015/repo/.agent-rails/scripts/checklist", line 198, in status_of
    checklist = load_list(name)
                ^^^^^^^^^^^^^^^
  File "/tmp/agent-rails-new-user-20261015/repo/.agent-rails/scripts/checklist", line 112, in load_list
    return json.loads(list_path(name).read_text())
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/codex/runtimes/codex-primary-runtime/dependencies/python/lib/python3.12/json/__init__.py", line 346, in loads
    return _default_decoder.decode(s)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/codex/runtimes/codex-primary-runtime/dependencies/python/lib/python3.12/json/decoder.py", line 338, in decode
    obj, end = self.raw_decode(s, idx=_w(s, 0).end())
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/codex/runtimes/codex-primary-runtime/dependencies/python/lib/python3.12/json/decoder.py", line 354, in raw_decode
    obj, end = self.scan_once(s, idx)
               ^^^^^^^^^^^^^^^^^^^^^^
json.decoder.JSONDecodeError: Expecting property name enclosed in double quotes: line 1 column 2 (char 1)
exit=2
Overrides: {'AGENT_RAILS_FAIL_CLOSED': '1'}

$ python3 .agent-rails/hooks/stop_gate.py
STDIN {"session_id": "corrupt", "hook_event_name": "Stop", "stop_hook_active": true, "cwd": "/"}
stdout:
stderr:
Traceback (most recent call last):
  File "/tmp/agent-rails-new-user-20261015/repo/.agent-rails/hooks/stop_gate.py", line 96, in <module>
    sys.exit(main())
             ^^^^^^
  File "/tmp/agent-rails-new-user-20261015/repo/.agent-rails/hooks/stop_gate.py", line 84, in main
    result = decide(payload)
             ^^^^^^^^^^^^^^^
  File "/tmp/agent-rails-new-user-20261015/repo/.agent-rails/hooks/stop_gate.py", line 62, in decide
    found = open_items(root)
            ^^^^^^^^^^^^^^^^
  File "/tmp/agent-rails-new-user-20261015/repo/.agent-rails/hooks/stop_gate.py", line 41, in open_items
    raise RuntimeError(f"checklist status failed ({proc.returncode}): {proc.stderr.strip()}")
RuntimeError: checklist status failed (1): Traceback (most recent call last):
  File "/tmp/agent-rails-new-user-20261015/repo/.agent-rails/scripts/checklist", line 268, in <module>
    sys.exit(main())
             ^^^^^^
  File "/tmp/agent-rails-new-user-20261015/repo/.agent-rails/scripts/checklist", line 264, in main
    return args.func(args)
           ^^^^^^^^^^^^^^^
  File "/tmp/agent-rails-new-user-20261015/repo/.agent-rails/scripts/checklist", line 221, in cmd_status
    reports = [status_of(name, key) for name in names]
               ^^^^^^^^^^^^^^^^^^^^
  File "/tmp/agent-rails-new-user-20261015/repo/.agent-rails/scripts/checklist", line 198, in status_of
    checklist = load_list(name)
                ^^^^^^^^^^^^^^^
  File "/tmp/agent-rails-new-user-20261015/repo/.agent-rails/scripts/checklist", line 112, in load_list
    return json.loads(list_path(name).read_text())
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/codex/runtimes/codex-primary-runtime/dependencies/python/lib/python3.12/json/__init__.py", line 346, in loads
    return _default_decoder.decode(s)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/codex/runtimes/codex-primary-runtime/dependencies/python/lib/python3.12/json/decoder.py", line 338, in decode
    obj, end = self.raw_decode(s, idx=_w(s, 0).end())
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/codex/runtimes/codex-primary-runtime/dependencies/python/lib/python3.12/json/decoder.py", line 354, in raw_decode
    obj, end = self.scan_once(s, idx)
               ^^^^^^^^^^^^^^^^^^^^^^
json.decoder.JSONDecodeError: Expecting property name enclosed in double quotes: line 1 column 2 (char 1)
exit=1

$ python3 .agent-rails/hooks/tool_guard.py
STDIN {"session_id": "guard", "hook_event_name": "PreToolUse", "tool_name": "Bash", "tool_input": {"command": "gh issue edit 1 --add-label review"}}
stdout:
{"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny", "permissionDecisionReason": "Change workflow labels with `ghflow claim|review|rework|done <issue>`, not raw gh; ghflow checks the PR, the results comment and the merge."}}
stderr:
exit=0

$ python3 .agent-rails/hooks/tool_guard.py
STDIN {"session_id": "guard", "hook_event_name": "PreToolUse", "tool_name": "Bash", "tool_input": {"command": "gh pr merge 1"}}
stdout:
{"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny", "permissionDecisionReason": "Agents don't merge. Move the issue to review with `ghflow review <issue>` and stop."}}
stderr:
exit=0

$ python3 .agent-rails/hooks/tool_guard.py
STDIN {"session_id": "guard", "hook_event_name": "PreToolUse", "tool_name": "Bash", "tool_input": {"command": "printf hello"}}
stdout:
stderr:
exit=0

$ python3 .agent-rails/hooks/tool_guard.py
STDIN {"session_id": "guard", "hook_event_name": "PreToolUse", "tool_name": "Write", "tool_input": {"file_path": "/tmp/agent-rails-new-user-20261015/repo/docs/example.md", "content": "gh issue edit 1 --add-label review\ngh pr merge 1"}}
stdout:
stderr:
exit=0

$ cat docs/guide.md
stdout:
# Guide
Read this guide before work.
stderr:
exit=0

$ python3 .agent-rails/hooks/read_log.py
STDIN {"session_id": "read-log", "hook_event_name": "PostToolUse", "tool_name": "Read", "tool_input": {"file_path": "/tmp/agent-rails-new-user-20261015/repo/docs/guide.md"}}
stdout:
stderr:
exit=0

$ python3 .agent-rails/hooks/read_log.py
STDIN {"session_id": "read-log", "hook_event_name": "PostToolUse", "tool_name": "Bash", "tool_input": {"command": "cat docs/guide.md"}}
stdout:
stderr:
exit=0

$ cat .rails/reads.log
stdout:
{"at": "2026-10-15T06:17:29+00:00", "session": "read-log", "tool": "Read", "path": "docs/guide.md"}
{"at": "2026-10-15T06:17:29+00:00", "session": "read-log", "tool": "Bash", "path": "docs/guide.md"}
stderr:
exit=0
Correction: prepend installed .agent-rails/scripts to PATH; README does not say to do this.
Created README assumed src/app.py fixture.

$ checklist init headers --glob 'src/**/*.py' --check "head -1 {item} | grep -q 'SPDX-License-Identifier'"
stdout:
{"name": "headers", "items": 1}
stderr:
exit=0

$ checklist verify headers src/app.py
stdout:
{"item": "src/app.py", "ok": true}
stderr:
exit=0

$ checklist status
stdout:
headers: 1/1 done
review: 1/10 done
  open: posts/02.md (stale receipt)
  open: posts/03.md
  open: posts/04.md (forged receipt)
  open: posts/05.md (forged receipt)
  open: posts/06.md
  open: posts/07.md
  open: posts/08.md
  open: posts/09.md
  open: posts/10.md
stderr:
exit=2

$ ghflow claim 1
stdout:
{"issue": 1, "state": "in-progress", "assignee": "alice"}
stderr:
exit=0

$ cat docs/guide.md
stdout:
# Guide
Read this guide before work.
stderr:
exit=0

$ python3 .agent-rails/hooks/read_log.py
STDIN {"tool_name": "Bash", "tool_input": {"command": "cat docs/guide.md"}, "cwd": "/tmp/agent-rails-new-user-20261015/repo"}
stdout:
stderr:
exit=0
Fake fixture: linked open PR #2; no actual PR opened.

$ ghflow result 1 --body-file result.txt
stdout:
{"issue": 1, "comment": "https://github.com/o/r/issues/1#issuecomment-1001", "id": 1001}
stderr:
exit=0

$ ghflow review 1
stdout:
{"issue": 1, "state": "review", "prs": ["https://example.invalid/pr/2"]}
stderr:
exit=0

$ ghflow status 1
stdout:
{
  "issue": 1,
  "state": "review",
  "issue_state": "open",
  "assignees": [
    "alice"
  ],
  "prs": [
    {
      "number": 2,
      "url": "https://example.invalid/pr/2",
      "state": "open"
    }
  ],
  "results": [
    "https://github.com/o/r/issues/1#issuecomment-1001"
  ],
  "accept": true
}
stderr:
exit=0

$ ghflow done 1
stdout:
stderr:
ghflow: refused: no merged PR links #1; done is earned by a merge, not a report
exit=3
Fake fixture: marked PR merged in JSON only; no actual merge.

$ ghflow done 1
stdout:
{"issue": 1, "state": "done", "merged": ["https://example.invalid/pr/2"]}
stderr:
exit=0

$ ghflow status 1
stdout:
{
  "issue": 1,
  "state": "done",
  "issue_state": "open",
  "assignees": [
    "alice"
  ],
  "prs": [
    {
      "number": 2,
      "url": "https://example.invalid/pr/2",
      "state": "merged"
    }
  ],
  "results": [
    "https://github.com/o/r/issues/1#issuecomment-1001"
  ],
  "accept": true
}
stderr:
exit=0

$ ghflow watch --help
stdout:
usage: ghflow watch [-h] [--interval INTERVAL] [--once] [--state STATE]
                    [issues ...]

positional arguments:
  issues               limit to these issues

options:
  -h, --help           show this help message and exit
  --interval INTERVAL
  --once               one poll, then exit
  --state STATE        snapshot file (default .rails/watch.json)
stderr:
exit=0
Public git clone command not run: private pre-publication branch checkout supplied by coordinator. Placeholder /path/to/your/repo substituted above. Test section commands executed separately by coordinator; see its evidence. Abstract N/F metavariables substituted with fixture 1/result.txt. Bare ghflow claim/review/result without arguments are incomplete references, not executable examples. Continuous ghflow watch not run: ongoing polling outside walkthrough scope; help run.

$ (cd /tmp/agent-rails-new-user-20261015/repo/docs; ../.agent-rails/scripts/checklist status --json)
STDIN None
stdout:
[
  {
    "name": "headers",
    "total": 1,
    "done": 1,
    "open": [],
    "forged": [],
    "stale": [],
    "added_since_init": []
  },
  {
    "name": "review",
    "total": 10,
    "done": 1,
    "open": [
      "posts/02.md",
      "posts/03.md",
      "posts/04.md",
      "posts/05.md",
      "posts/06.md",
      "posts/07.md",
      "posts/08.md",
      "posts/09.md",
      "posts/10.md"
    ],
    "forged": [
      "posts/04.md",
      "posts/05.md"
    ],
    "stale": [
      "posts/02.md"
    ],
    "added_since_init": []
  }
]
stderr:
exit=2

$ (cd /tmp/agent-rails-new-user-20261015/repo/docs; python3 ../.agent-rails/hooks/stop_gate.py)
STDIN {"hook_event_name": "Stop", "session_id": "subdir", "cwd": "/tmp/agent-rails-new-user-20261015/repo/docs", "stop_hook_active": false}
stdout:
{"decision": "block", "reason": "9 checklist item(s) have no valid receipt: review: posts/02.md (stale receipt); review: posts/03.md (no receipt); review: posts/04.md (forged receipt); review: posts/05.md (forged receipt); review: posts/06.md (no receipt); review: posts/07.md (no receipt); review: posts/08.md (no receipt); review: posts/09.md (no receipt); review: posts/10.md (no receipt). Finish each one, then run `checklist verify <list> <item>` so the runner writes its receipt. Block 1 of 3."}
stderr:
exit=0

$ (cd /tmp/agent-rails-new-user-20261015/repo; .agent-rails/scripts/ghflow watch --once)
STDIN None
stdout:
{"at": "2026-10-15T06:18:20+00:00", "issue": 1, "event": "seen", "state": "done", "issue_state": "open", "assignees": ["alice"], "comments": 1, "prs": {"2": "merged"}, "feedback": {}}
stderr:
exit=0
```

### Real Codex and normal trust

#### Real-model Codex check

Installed pinned Codex 0.160.0 reports `Logged in using ChatGPT`, but a real model was **not reached**. Two minimal exec probes failed during local app-server initialization with a read-only filesystem error. A normal interactive launch (no hook-trust bypass) failed opening `/home/agent/.codex/state_5.sqlite`; it never reached a project/hook approval prompt. This is an environment blocker, not evidence of an agent-rails defect or invalid login. The CLI's “database appears to be damaged” wording does not prove corruption; its technical error is inability to open the database.

Prepared separate fresh git repo `/tmp/agent-rails-real-codex` with ten markdown posts, `docs/guide.md`, and the kit installed by `scripts/install`.

- Real-model task prompt: **not run**, because prerequisite real-model connectivity could not be established due to local startup failure.
- Normal project trust and hook approval: **not completed**, interactive CLI failed before approval prompt.
- Real-model Stop hook block: **not run**, same startup blocker.
- Model response (finish remaining posts versus argue): **not run**, same startup blocker.
- Real-model Stop cap: **not run**, same startup blocker.
- Real-model `apply_patch` reaching PreToolUse guard: **not run**, same startup blocker; no claim inferred from scripted tests.

No hook-trust bypass was used. No auth tokens were read or copied, and no global configuration was changed. Commands and observed output are in `real-codex.txt`.

#### Real CLI probe output

```text
Real Codex, 2026-10-15 UTC

$ /tmp/agent-rails-cli/bin/codex --version
WARNING: proceeding, even though we could not create PATH aliases: Read-only file system (os error 30)
codex-cli 0.160.0

$ /tmp/agent-rails-cli/bin/codex login status
WARNING: proceeding, even though we could not create PATH aliases: Read-only file system (os error 30)
Logged in using ChatGPT

$ scripts/install /tmp/agent-rails-real-codex
wrote .claude/settings.json
wrote .codex/hooks.json
installed agent-rails into /tmp/agent-rails-real-codex

$ timeout 90 /tmp/agent-rails-cli/bin/codex exec --ephemeral --ignore-user-config --json -C /tmp/agent-rails-real-codex 'Reply with exactly REAL_MODEL_PROBE_OK. Do not use tools.'
WARNING: proceeding, even though we could not create PATH aliases: Read-only file system (os error 30)
Reading additional input from stdin...
Error: failed to initialize in-process app-server client: Read-only file system (os error 30)
exit=1

$ /tmp/agent-rails-cli/bin/codex exec --ephemeral --ignore-user-config --json -c sqlite_home='"/tmp/agent-rails-real-codex-state"' -c log_dir='"/tmp/agent-rails-real-codex-logs"' -C /tmp/agent-rails-real-codex 'Reply with exactly REAL_MODEL_PROBE_OK. Do not use tools.' </dev/null
WARNING: proceeding, even though we could not create PATH aliases: Read-only file system (os error 30)
Reading additional input from stdin...
Error: failed to initialize in-process app-server client: Read-only file system (os error 30)
exit=1

$ timeout 15 /tmp/agent-rails-cli/bin/codex --no-daemon --no-alt-screen -C /tmp/agent-rails-real-codex
Interactive terminal output excerpt (ANSI painting omitted):
WARNING: proceeding, even though we could not create PATH aliases: Read-only file system (os error 30)
WARNING: TERM is set to "dumb". Codex's interactive TUI may not work in this terminal.
Continue anyway? [y/N]:
y
Codex couldn't start because its local database appears to be damaged.
Run `codex doctor` to check your setup and get next-step guidance.
If this keeps happening, share the technical details below when asking for help.
Technical details:
  Location: /home/agent/.codex/state_5.sqlite
  Cause: failed to initialize state runtime at /home/agent/.codex: failed to open state DB at /home/agent/.codex/state_5.sqlite: error returned from database: (code: 14) unable to open database file: error returned from database: (code: 14) unable to open database file: (code: 14) unable to open database file
ERROR: failed to initialize sqlite local db at /home/agent/.codex/state_5.sqlite: failed to initialize state runtime at /home/agent/.codex: failed to open state DB at /home/agent/.codex/state_5.sqlite: error returned from database: (code: 14) unable to open database file: error returned from database: (code: 14) unable to open database file: (code: 14) unable to open database file
exit=1
```

### Remaining not-run items

- Real-model Codex prompt, model response to Stop, stop cap, and `apply_patch` dispatch: not run, because the existing logged-in CLI could not start. Authentication status alone does not establish model reachability. Normal trust/hook approval was attempted interactively but did not reach a prompt. No hook-trust bypass was used for the real-model attempt.
- Codex scripted hook semantics: not exercised because startup failed before any model request. The six harness scenarios were invoked; they are failures/blocked, not successful checks. A legitimate workspace-write/on-request diagnostic also failed. No enforced security setting was weakened.
- Old TESTED.md live interactive Claude real-model run: not reproduced; only the explicitly requested scripted Claude run and direct hook checks were exercised here.
- Old live GitHub issue/PR run and observer with real models/GitHub: not reproduced; this task forbids merges/settings changes, and no live issue/PR/label changes were needed or performed. Fake-GitHub workflow and observer snapshot ran; units cover the transition and feedback checks. No worker orchestration claim is inferred from those.
- `AGENT_RAILS_FAIL_CLOSED=1` within a real CLI: not run; direct hook and unit behavior were observed. Default fail-open was observed in the real Claude CLI with fake model.
- macOS behavior: not run, host is Linux.
- Anonymous public clone after publication: not run, repository is still pre-publication/private. Literal current URL attempt failed authentication; authenticated build-kit checkout was tested.
- Unbounded observer watch: not run because it intentionally never exits; `watch --once` ran against fake gh.
- Placeholder `/path/to/your/repo`, `N`, `F`: substituted with the actual fresh repository and fixture issue/file rather than treated as literal valid paths/identifiers.

Additional wording suggestion: replace “appends every file the agent opens” with “records paths exposed by supported tool payloads and recognized shell readers.” Grep/Glob input paths are not a proof of every matched file being read. This is a documentation limitation noted from source inspection, not a claim of an unrun end-to-end read audit.
