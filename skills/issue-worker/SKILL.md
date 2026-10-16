---
name: issue-worker
description: Work GitHub issues end to end on rails (claim, explore docs, implement, verify, PR, review label) through the ghflow wrapper, or run as an observer that spawns one worker sub-agent per issue or checklist item and accepts "done" only from the record. Use when asked to "work on issue #N", "work the backlog", "take the ready issues", "apply X to every Y", or "run the issues with sub-agents".
---

# Issue worker

Two modes in one skill:

- **Worker** (`/issue-worker 42`): carry one issue from claim to `review`.
- **Observer** (`/issue-worker observe 41 42 43`, or `observe --label ready`, or
  `observe --checklist NAME`): spawn workers as sub-agents, watch GitHub, relay
  events, and accept results only from the record.

The rails are outside the model:

| Rail | Enforced by |
|------|-------------|
| Claim before work, states in order | `.agent-rails/scripts/ghflow` refuses illegal moves |
| Docs explored before coding | `ghflow review` reads the hook's read log, not your word |
| A result exists | `ghflow result` reads its own comment back before reporting success |
| `review` only with a linked PR | `ghflow review` checks for a PR saying `Closes #N` |
| `done` only after a merge | `ghflow done` checks the PR is merged |
| No raw label edits, no self-merge | the PreToolUse hook denies them |
| Every item of a list handled | `checklist` + the Stop hook block stopping while items are open |

If a command is refused, that's the rail working. Read the reason, fix the
cause, run the command again. Never route around the wrapper with raw `gh`.

Paths below are relative to the repo root; `ghflow` means
`.agent-rails/scripts/ghflow` and `checklist` means `.agent-rails/scripts/checklist`.

## Worker mode

### 1. Read the issue

```bash
gh issue view N --comments
```

Read the whole thread: the description, the acceptance criteria, every comment
and any linked issues. Write down the acceptance criteria as a numbered list in
your scratch notes; step 5 walks it.

### 2. Claim

```bash
ghflow claim N
```

This assigns you, adds `in-progress`, and reads both back. If it's refused
(already claimed, assigned to someone else, closed), stop and report. Don't
pick a different issue unless you were told to.

### 3. Explore the docs before coding

Read the project's docs for the area you're about to touch: `README*`,
`docs/`, `CONTRIBUTING*`, architecture notes and any page the issue links. Use
your file-reading tool (or `cat`/`sed -n`/`rg`), because the PostToolUse hook
logs what you read to `.rails/reads.log`. That log is the evidence:
`ghflow review` refuses while it shows no docs read since your claim, and
`ghflow result` copies the list into your results comment. Reading this skill
file doesn't count.

Don't skim one file to satisfy the check. The check proves you opened
something; whether you understood it shows in the PR. Before writing code,
list: the docs you read and one takeaway from each, the existing code you'll
follow, and the constraints that shape the change.

### 4. Implement

Work on a branch named `issue-N-<slug>`. Read the code you're changing before
you change it and match its style. Do exactly what the issue asks. Run the
tests after each logical chunk.

### 5. Verify

Run the project's full test and lint commands. Then walk the acceptance
criteria from step 1 one by one, and for each write what proves it: a test
name, a command and its output, a screenshot path. A criterion without proof
isn't met.

### 6. Open the PR

```bash
git push -u origin HEAD
gh pr create --title "<one line>" --body-file pr.md
```

`pr.md` must contain `Closes #N` (or `Fixes #N`/`Resolves #N`). That keyword is
how `ghflow` finds the PR, and how GitHub closes the issue on merge.

### 7. Post the result, then move to review

```bash
ghflow result N --body-file result.md
ghflow review N
```

`result.md` holds what changed, the PR link, and the proof for each criterion
from step 5. `ghflow result` exits 0 only after reading the comment back.
Exit 4 means GitHub accepted the write but a fresh read doesn't show it, so
run it again and don't claim it's posted.

`ghflow review` refuses unless the issue is `in-progress`, an open or merged
PR links it, your results comment is there, and the read log shows docs. Fix
whichever is missing and run it again.

### 8. Stop

Report in one block: issue, PR URL, and the `ghflow review` output. Don't
merge (the hook denies it) and don't run `ghflow done`; whoever merges does
that. If review feedback arrives later, `ghflow rework N`, address it, push,
post a new result, then `ghflow review N`.

### Apply X to every item in Y

When the issue says "do X to every file, issue or service in Y", don't
hand-write the list:

```bash
checklist init NAME --glob 'src/**/*.py' --check 'CMD that exits 0 when {item} is done'
# or --issues-label LABEL, or --from-cmd 'command that prints one item per line'
```

Do the work item by item, and after each one run
`checklist verify NAME ITEM`. The runner runs the stored check and writes the
receipt; you never write receipts. `checklist status` shows what's open, and
the Stop hook won't let the session end while anything is. If the check is
wrong, say so in your report instead of weakening it.

## Observer mode

The observer coordinates and never does a worker's job: no code, no PRs, no
results comments, no `ghflow review` for someone else's issue. Its output is
messages to workers and a final report built from the record.

### 1. Build the work list from the record

```bash
ghflow init
gh issue list --label ready --state open --json number,title    # or the numbers you were given
```

For per-item work, use `checklist init` (above) and treat each open item as a
unit. The list comes from GitHub or the data, never from memory.

### 2. One workspace per worker

```bash
git worktree add ../wt-issue-N -b issue-N
```

Each worker gets its own worktree, so its `.rails/` read log and claims are
its own. Two workers sharing a checkout would share a read log, and one
worker's docs reads would count for the other.

### 3. Spawn workers as sub-agents

One sub-agent per issue (or per checklist item), in the background, with this
prompt:

```
You are a worker. Use the issue-worker skill in worker mode for issue #N.
Your working directory is ../wt-issue-N; run every command from there.
Finish at `ghflow review N`, then reply with the PR URL and the ghflow output.
Do not merge. Do not touch other issues.
```

In Claude Code that's the Agent/Task tool; in Codex, a sub-agent or a second
`codex exec` in the worktree. Don't spawn more workers than you can watch
(three to five).

### 4. Watch through GitHub, not through the workers

```bash
ghflow watch --interval 60
```

It polls and prints one JSON line per change: `state` (label moved), `pr`
(opened, merged, closed), `comments` (new comment on the issue), `feedback`
(a new conversation comment, inline review comment or review on a linked
open PR, with `kind`, `author`, `url` and `review_state`), `issue` (closed or
reopened). Turn events into messages:

| Event | Message to the worker |
|-------|----------------------|
| `feedback` from a reviewer (not the worker), or `comments` on the issue from a reviewer | "New review feedback on #N: <url>. Address it: `ghflow rework N`, fix, push, new result, `ghflow review N`." |
| no event from a worker for 3 intervals | "No change on #N for 3 polls. Report what's blocking." |
| `state` → `review` | none; check acceptance (step 5) |
| `pr` → merged | none to the worker; run `ghflow done N` yourself |

Use `ghflow watch --once` in a loop if your harness can't keep a process
running. Don't wake a worker for events it caused itself.

### 5. Accept only what the record shows

A worker's reply ("done, PR is up, all tests pass") is a claim, not a
result. Before counting an issue:

```bash
ghflow status N
```

Count it only when `"accept": true`: a results comment is readable, and the
state is `review` with an open or merged linked PR, or `done` with a merged
one. A PR closed without merging doesn't count. For checklist units,
`checklist status NAME` must show the item done. If the worker says done and
the record disagrees, message the worker with the gap ("#N is still
`in-progress`: `ghflow review` hasn't run"), and don't fix it yourself.

`done` comes only from `ghflow done N` after the PR is merged, and that's the
merger's or the observer's move, never a worker's.

### 6. Report

One table, built from `ghflow status` for each issue: issue, state, PR, merged
yes or no. Below it, list the workers whose claims didn't match the record and
what was missing. Then `git worktree remove` the finished worktrees.
