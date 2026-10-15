# agent-rails

Keep coding agents on rails: hooks, a GitHub-issues worker skill with an observer mode, and a data-derived checklist.

Coding agents declare victory early. They say "done" with items skipped, report a PR they didn't open, post a result that never landed, and move a ticket forward because the instructions said to. Asking them more firmly doesn't fix it. This kit moves the important checks out of the prompt into things the model can't talk its way past: hook scripts the harness runs, a wrapper that refuses illegal moves, and receipts written by a runner instead of the agent.

It's small on purpose: three hook scripts, two CLI scripts and one skill file. Python 3 standard library only, no dependencies.

```
hooks/
  stop_gate.py          Stop: no stopping while checklist items lack a receipt
  tool_guard.py         PreToolUse: deny raw label edits, self-merge, receipt tampering
  read_log.py           PostToolUse: log which files were actually read
  claude/settings.json  wiring for Claude Code
  codex/hooks.json      wiring for Codex
scripts/
  ghflow                gh wrapper: issue states with enforced ordering and read-back
  checklist             "apply X to every item in Y": items from data, receipts from the runner
  install               vendor the kit into a repo
skills/issue-worker/SKILL.md   worker mode + observer mode
tests/                  unit tests (fake gh) and real-CLI harnesses (fake model)
docs/TESTED.md          every test run, with versions and output
```

## Install

Run the commands from a shell with Git and Python 3 available. The GitHub workflow additionally requires the `gh` CLI, an authenticated GitHub account, and a target repository with a GitHub remote (or an explicit `ghflow --repo OWNER/REPO` argument). Replace `/path/to/your/repo` below with an existing Git working tree.

```bash
git clone https://github.com/muzhig/agent-rails.git
agent-rails/scripts/install /path/to/your/repo
cd /path/to/your/repo && .agent-rails/scripts/ghflow init   # creates the in-progress / review / done labels
```

Run the installed commands from your target repository. The installer does not add its scripts to PATH; use `.agent-rails/scripts/checklist` and `.agent-rails/scripts/ghflow` as shown below.

`install` does five things:

- copies the kit to `.agent-rails/`;
- writes `.claude/settings.json` and `.codex/hooks.json`, but never overwrites existing ones (merge the `hooks` block by hand);
- puts the skill in `.claude/skills/` and `.agents/skills/`;
- adds `.rails/` to `.gitignore`;
- leaves the local state to `.rails/`: the read log, claims, checklists, receipts and stop counters.

Codex runs a project's hooks only after you've trusted the project and reviewed the hooks. Until then it skips them without saying so (see the failure modes).

## The pieces

### 1. `ghflow`: ordering enforced by a script, not by the model

Issue states are labels: `(none) → in-progress → review → done`, and `rework` goes back from `review` to `in-progress`. The agent moves them only through `ghflow`:

| Command | Refuses unless |
|---------|----------------|
| `.agent-rails/scripts/ghflow claim N` | the issue is open, has no state label, and isn't assigned to someone else |
| `.agent-rails/scripts/ghflow review N` | it's `in-progress`; an open or merged PR body says `Closes #N` (or Fixes/Resolves); a results comment by you exists; the read log shows docs read since the claim |
| `.agent-rails/scripts/ghflow done N` | it's `review` and a linked PR is **merged** |
| `.agent-rails/scripts/ghflow result N --body-file F` | (always posts) exits 0 only once a fresh read shows the comment |

**What it prevents:** a ticket moved to review with no PR; a ticket moved to done on a worker's say-so; skipped docs; "I posted the result" when the write never landed. Every write is followed by a GET, so label changes, assignments and comments count only once they read back. Exit 3 means refused. Exit 4 means GitHub accepted the write but a fresh read doesn't show it.

**Cost:** about 4–8 `gh api` calls per transition. `status`, `watch` and `review` list up to 100 PRs per page. `watch` adds three calls per linked open PR per poll (conversation comments, inline review comments, reviews) so the observer sees PR feedback.

**Failure modes:**

- The linked-PR check is a regex on PR bodies. `Closes #12` won't match issue #1, but a PR that says "fixes #1" in passing will count.
- The rails hold only while raw `gh` label edits are blocked. That's `tool_guard.py`'s job. Without the hooks, an agent can still run `gh issue edit` itself.

### 2. "Explore the docs first", verified by side effect

`read_log.py` (PostToolUse on Read/Grep/Glob/Bash) appends every file the agent opens to `.rails/reads.log`, in the git work tree that contains the file. `.agent-rails/scripts/ghflow review` refuses while the log shows no docs read since the claim. Docs means `README*`, `CONTRIBUTING*`, `docs/*` and `*.md`, but not the agent's own config (`.claude/`, `.agents/`, `.codex/`). Override with `AGENT_RAILS_DOCS` and `AGENT_RAILS_NOT_DOCS`. `.agent-rails/scripts/ghflow result` copies the list into the results comment, so a reviewer sees which docs were opened, written by a hook rather than typed by the agent.

**Failure modes:**

- It proves a file was opened, not understood. `cat README.md` passes.
- Shell reads are caught only for common readers (`cat`, `head`, `sed`, `rg`, …).
- Two workers in one checkout share a log, which is why observer mode gives each worker its own worktree.

### 3. `checklist`: "apply X to every item in Y"

This example assumes your target repo contains `src/app.py` (and any other Python files you want to check). Substitute your own glob and file path if it does not. The source must match at least one file. Between `init` and `verify`, add the SPDX header to each matched file.

```bash
.agent-rails/scripts/checklist init headers --glob 'src/**/*.py' --check "head -1 {item} | grep -q 'SPDX-License-Identifier'"
# ...do the work...
.agent-rails/scripts/checklist verify headers src/app.py        # the runner runs the stored check; writes a receipt on exit 0
.agent-rails/scripts/checklist status                           # exit 2 while anything is open
```

The list comes from the data, never from the agent's memory of what it touched. The source is a glob, `--issues-label`, or `--from-cmd` (one item per output line). `status` re-derives the items every time, so a file added after `init` shows up as open.

Each receipt is HMAC-signed with a key at `~/.config/agent-rails/receipt.key` (mode 0600, outside the repo). It binds the item, the exact check command, the checklist's creation time and, for files, the content hash. `status` marks a receipt **forged** when the signature, item or check don't match, and **stale** when the file changed after the check passed. A recheck deletes the old receipt before running, so if the item passed once and then fails (a dependency went away), it's open again.

**The trust boundary.** The runner (`.agent-rails/scripts/checklist verify`) is trusted: it runs a check that was fixed at `init`. The agent isn't trusted: it never writes the list or a receipt, and a hand-written or copied receipt is rejected.

That boundary is a speed bump, not a wall. The agent runs as the same OS user, so a determined agent could read the key, sign its own receipts, or re-`init` the list with a weaker check. `tool_guard.py` denies the obvious routes (the key path, `.rails/receipts/`), but a shell can get around a regex. For a hard boundary, run `verify` somewhere the agent can't reach: CI, a different user, or a container that holds the key.

A check is also only as good as you write it. Shape satisfies the gate: `grep -q License` passes for a file that says "License: TODO".

**Cost:** one check process per item per `verify`. `status` hashes every file item.

### 4. The Stop hook: no "done" while items are open

`stop_gate.py` runs `.agent-rails/scripts/checklist status --all`. If anything is open, it returns `{"decision": "block", "reason": "..."}`. The reason names each open item, why it's open (no receipt, forged or stale) and the command that fixes it. The harness hands that reason to the model as its next instruction. Tested on both Claude Code and Codex.

**Repeat cap:** at most `AGENT_RAILS_STOP_CAP` blocks per session (default 3). After that, the stop is allowed with a `systemMessage` warning. Without a cap, a gate the agent can't satisfy loops and burns tokens until someone kills the session.

**Fail-open:** if the hook crashes (bad JSON, missing Python), both harnesses treat the non-zero exit as a hook error and **let the agent stop**. Claude Code shows a "Stop hook error" notice; Codex shows nothing in `exec` mode. Set `AGENT_RAILS_FAIL_CLOSED=1` to make a crash block once (exit 2). The next stop is let through, so a broken gate can't loop.

### 5. The PreToolUse guard

`tool_guard.py` denies three things, each with a reason the model sees:

- state-label edits through raw `gh issue edit --add-label/--remove-label` or `gh api …/issues/N/labels`;
- `gh pr merge`, because merging is the reviewer's call;
- anything touching the receipt key or `.rails/receipts/`.

It matches shell commands on their text and file tools on their path only. A Write that *quotes* a forbidden command, like this README, is allowed. It's a regex, so it guards against habits and mistakes, not an adversary: `cd .rails && echo … > receipts/x` slips past it. That's why receipts are signed rather than just protected, and the harness tests exactly that path.

**Fail-open:** if the guard crashes, the tool call goes through.

### 6. The skill: worker mode and observer mode

`skills/issue-worker/SKILL.md` is one skill with two modes.

**Worker mode** runs one issue from claim to review:

1. Read the issue and its comments.
2. `.agent-rails/scripts/ghflow claim`.
3. Explore the docs (logged).
4. Implement.
5. Verify by walking each acceptance criterion with its proof.
6. Open a PR that says `Closes #N`.
7. `.agent-rails/scripts/ghflow result`, then `.agent-rails/scripts/ghflow review`, and stop. No merging.

**Observer mode** coordinates workers:

- It builds the work list from GitHub or `checklist`.
- It spawns one worker sub-agent per issue or item, each in its own git worktree.
- It watches through `.agent-rails/scripts/ghflow watch` (polling, one JSON line per change, including reviewer feedback on linked PRs) and turns events into messages for the workers.
- It accepts an issue only when `.agent-rails/scripts/ghflow status N` says `"accept": true` (`review` with an open or merged linked PR, or `done` with a merged one, plus a results comment), never on a worker's report.
- It never writes code, PRs or results for a worker.

**Cost:** observer polling is two list calls per interval (60 s by default). Each worker is a full agent session.

**Failure modes:** the rule against doing a worker's job lives in the prompt, so the observer can still be talked into it. Acceptance doesn't live in the prompt: `done` needs a merged PR whatever anyone says.

## Failure modes in one place

| Failure | What it looks like | What the kit does about it |
|---------|--------------------|----------------------------|
| Shape satisfies the gate | the check passes, the work is wrong | nothing automatic: write checks that test substance, and review PRs |
| Silent harness failure | hooks never run (Codex project untrusted, settings not loaded, wrong path) | the harnesses show what "on" and "off" look like; `codex_e2e.py untrusted_hooks_do_not_run` reproduces "off" |
| Fail-open | the hook crashes and the agent stops anyway | documented and tested; `AGENT_RAILS_FAIL_CLOSED=1` blocks once |
| Loops | a gate the agent can't satisfy | `AGENT_RAILS_STOP_CAP`, then a warning |
| Write not landed | "result attached", nothing on the issue | read-back, exit 4 |
| Forged evidence | a hand-written receipt or read log | receipts are signed; the read log is only a speed bump (same-user agent) |
| Self-report trusted | "done, PR is up" with no PR | the observer accepts only `.agent-rails/scripts/ghflow status` |

## Tests

```bash
python3 -m unittest discover -s tests -v       # unit tests against a fake gh, no network
python3 tests/harness/claude_e2e.py            # the real Claude Code CLI with a scripted fake model
python3 tests/harness/codex_e2e.py             # the real Codex CLI with a scripted fake model
```

The harnesses run the real CLIs, so the hook dispatch is real. A local stand-in for the model API answers with scripted turns ("I'm done", a forbidden command, …), and the tests assert what the harness fed back to the model. They need no API key and make no network calls. [docs/TESTED.md](docs/TESTED.md) has the versions, the runs, and what's still unverified.

## License

MIT
