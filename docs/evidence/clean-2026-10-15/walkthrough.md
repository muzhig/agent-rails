# Independent newcomer walkthrough

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

## Bug fixed and regression

Commit `29e0825` (`docs: make installed checklist quickstart runnable without PATH setup`) fixes README commands that fail immediately in a clean installation. Installer leaves scripts in `.agent-rails/scripts` but README used bare `checklist`/`ghflow` without PATH setup. The three executable checklist example lines each actually exited 127. README now uses explicit installed paths and explains the example requires existing Python source files and the header-editing step. Installation prerequisites and the absence of PATH modification are explicit.

`tests/test_readme.py` extracts the README checklist commands and runs them in a newly initialized and installed repository without any developer `checklist` PATH entry. It creates the assumed Python file and performs the documented header work between initialization and verification. It failed on the original README (`AssertionError: 127 != 0`, `/bin/sh: 1: checklist: not found`), then passed after the wording/path fix. [readme-regression.txt](readme-regression.txt) contains both actual runs.

## Additional README wording suggestions

- Clarify that the kit's Python code uses the standard library, but normal use also needs Git, a shell and the utilities referenced by each check; GitHub workflow needs installed/authenticated `gh`. Partly addressed in the prerequisite paragraph.
- “Appends every file the agent opens” is stronger than the implementation promises. Prefer “Records paths exposed by supported Read/Grep/Glob payloads and recognized shell readers; this is partial read evidence, not a complete filesystem audit.” Source inspection shows Grep/Glob log their input path rather than every result path; do not present glob enumeration as proven content reading.
- “At most 3 blocks” does not mean success after the cap: the warning explicitly preserves the nine outstanding items in this run. Existing warning/cap wording accurately reflects the observed behavior.
- Hook crash behavior distinguishes exit 1/error (default fail-open) from exit 2 (one fail-closed block); direct hook invocation proves emitted output/status only. Actual CLI behavior belongs in harness evidence.

## Not run / scope boundaries

- Literal public `git clone https://github.com/muzhig/agent-rails.git`: not run by this walkthrough; coordinator supplied the fresh private `build-kit` checkout. This avoids accidentally testing the default branch instead of PR #3. Do not count public-clone usability as proven before publication.
- Literal `/path/to/your/repo`: a documentation placeholder, substituted with the actual fresh fixture path. Likewise N/F in command reference tables were instantiated as issue 1/result.txt.
- Live GitHub workflow writes: not run because unnecessary and outside the authorized mutation scope. The actual ghflow commands ran against the bundled fake, explicitly as labeled above.
- Unbounded `ghflow watch`: not run because it deliberately never exits; its `--help` and actual `--once` polling were run.
- Unit suite and CLI harness commands in the README Tests section: owned/run by the coordinator or other worker, not duplicated here. See their evidence, not an inferred pass from this walkthrough.
- Real-model Codex: owned by separate worker, not run by this walkthrough. Direct JSON-hook invocations above are not a simulation claimed as a real model test.
