# Contributing

1. Pick or create a GitHub issue (Task template) with a `TASK-###` or `BIZ-###` ID from `docs/planning/TASKS.md`.
2. Create a branch: `git switch -c feat/TASK-002-tenant-rls`.
3. Make small commits using Conventional Commits, ending with the task ID.
4. If the API changes, regenerate `openapi/openapi.json` and keep the change backward-compatible.
5. Open a pull request with the template filled in and `Closes #<issue>`.
6. Wait for CI; add the `claude-review` label if you want an AI review.
7. Squash-merge. The PR title becomes the commit on `main`.

Full rules: [docs/engineering/GIT_WORKFLOW.md](docs/engineering/GIT_WORKFLOW.md) and [docs/engineering/DEFINITION_OF_DONE.md](docs/engineering/DEFINITION_OF_DONE.md).
