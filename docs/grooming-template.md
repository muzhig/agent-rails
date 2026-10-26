# A grooming template, and how to judge the plan it produces

A groom is a planning pass an agent makes before it codes: it reads the code and the docs, then writes down what the change needs. It's not free. Expect it to take a third to half of the session. On small, clear tickets it may change nothing. In [a small study on small tasks](https://potapov.dev/blog/how-much-planning/), a groom like this one didn't measurably reduce the two mistakes it targets: rebuilding a helper the codebase already has, and trusting a name the code has drifted from. So use it where the premises or the decisions are still open, not on every ticket.

## When to groom

- **The ticket is a title.** One sentence means someone has to dig up the context before touching the code. Often the agent can do it.
- **The ticket makes claims about the code** (that something is a bug, a hole, or the same as something else) and nobody has checked them. Agents write tickets too, and a confident wrong claim reads like a requirement.
- **The work spans several issues.** Groom the whole piece once and let each issue inherit the plan, rather than planning every issue on its own.

A short ticket isn't, by itself, a reason to groom. A short, well-defined change can go straight to work.

## The template

Before writing any code, the worker writes the groomed task to a file next to the task, with the same name plus `.plan.md`. For `docs/tasks/X.md`, that's `docs/tasks/X.plan.md`. It has five sections:

- **Context:** why this change exists, in two or three sentences.
- **Requirements:** the concrete deliverables.
- **Implementation notes:**
  - the files, functions and entry points involved;
  - existing helpers, patterns, utilities and tests to reuse, with their locations;
  - conventions;
  - gotchas, including facts found away from where the change goes.

  Enough to start coding.
- **Sub-tasks:** a checklist of steps.
- **Acceptance criteria:** criteria that can each be tested on their own.

The worker commits the plan on its own, then implements against it and commits the change. A separate commit makes the plan reviewable, and shows it existed before the code.

With `issue-worker`, the groom fits after step 3 (explore the docs). The read log already records what the worker opened, so a plan that claims to have checked a file can be compared with what was actually read.

## Judge the plan by what it found

Length says nothing. Ask the plan for four things:

1. **What it checked, and where:** the files and docs it read for each claim in the ticket. A check can come back true. A plan that confirms a constraint or narrows an unknown has done its job without contradicting anything.
2. **What it will reuse, by name:** the helpers, patterns and tests the change should build on, so reinvention is visible before the diff.
3. **Which names it checked against their implementation:** a function called `commit()` that doesn't commit inside an open transaction, or a `_deep_merge` that does a shallow update. The code around a call can make the name look true.
4. **Which assumptions are still open,** and which findings changed the work.

For each factual claim in the ticket, the plan should give one of five labels, and act on it:

| Label | What to do |
|---|---|
| Missing information | ask |
| A stale fact | reproduce or verify it |
| A false assertion | turn it into a question, not an instruction |
| A deliberate constraint | keep it, and mark it as a decision |
| A verified current fact | keep it, with the file or doc that confirms it |

**The plan needs permission to say "don't build this" or "already built".** A plan that can only say yes is a delay.

## Failure modes

| Failure | What it looks like | What to do |
|---|---|---|
| Over-engineering | a new subsystem, layer or token scheme for a small job | groom against what the project already has (docs, patterns, tests); cut what the ticket didn't need |
| Laundering a false claim | the ticket says "X is a security hole"; the plan designs the fix and spreads it into sibling tasks | the false-assertion label: check the claim first, then plan |
| Caught on paper, followed in code | the plan flags the wrong premise and the change acts on it anyway | review the diff against the plan's findings, not just the plan |
| Knowledge nobody wrote down | the agent "fixes" a missing setup step with a command that would overwrite something | a groom can only find what's written; put the gotcha in the docs or a check |
