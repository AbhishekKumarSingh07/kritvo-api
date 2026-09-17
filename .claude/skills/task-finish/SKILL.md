---
name: task-finish
description: Finish the current Kritvo task: run checks, update changelog, plan and status, commit, and open a pull request.
disable-model-invocation: true
---

Finish the task on the current branch. The task ID is in the branch name.

1. Run the checks for every app touched (see Commands in `CLAUDE.md`) and `npx markdownlint-cli2` on changed Markdown files. Fix failures before continuing.
2. Walk through `docs/engineering/DEFINITION_OF_DONE.md` and report each item as done or not.
3. If any endpoint, schema or field changed, run `uv run kritvo-openapi` and confirm the change is backward-compatible; list what `kritvo-web` must do next.
4. Compare the change with the HLD and LLD. If behaviour now differs from the docs, stop and propose `/doc-change` or an ADR instead of leaving them out of sync.
5. Add a line to `CHANGELOG.md` under **Unreleased** (Added, Changed, Fixed, Security or Removed) ending with the task ID.
6. Set the task to **Done** in `docs/planning/TASKS.md` (or **In progress** if this PR is partial).
7. Commit with a Conventional Commit message ending with the task ID. Show me the message first.
8. Ask before pushing. After I agree, push and open a PR with `gh pr create`, using `.github/pull_request_template.md`, the same title as the commit, and `Closes #<issue>`.
9. Remind me to run `/status-update` if this ends my session.
