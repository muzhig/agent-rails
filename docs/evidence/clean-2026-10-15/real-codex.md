# Real-model Codex check

Installed pinned Codex 0.160.0 reports `Logged in using ChatGPT`, but a real model was **not reached**. Two minimal exec probes failed during local app-server initialization with a read-only filesystem error. A normal interactive launch (no hook-trust bypass) failed opening `/home/agent/.codex/state_5.sqlite`; it never reached a project/hook approval prompt. This is an environment blocker, not evidence of an agent-rails defect or invalid login. The CLI's “database appears to be damaged” wording does not prove corruption; its technical error is inability to open the database.

Prepared separate fresh git repo `/tmp/agent-rails-real-codex` with ten markdown posts, `docs/guide.md`, and the kit installed by `scripts/install`.

- Real-model task prompt: **not run**, because prerequisite real-model connectivity could not be established due to local startup failure.
- Normal project trust and hook approval: **not completed**, interactive CLI failed before approval prompt.
- Real-model Stop hook block: **not run**, same startup blocker.
- Model response (finish remaining posts versus argue): **not run**, same startup blocker.
- Real-model Stop cap: **not run**, same startup blocker.
- Real-model `apply_patch` reaching PreToolUse guard: **not run**, same startup blocker; no claim inferred from scripted tests.

No hook-trust bypass was used. No auth tokens were read or copied, and no global configuration was changed. Commands and observed output are in `real-codex.txt`.
