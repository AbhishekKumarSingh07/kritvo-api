---
name: doc-change
description: Change the Kritvo HLD or LLD safely with a version bump, revision history, ADR check and tag instructions.
disable-model-invocation: true
argument-hint: "[HLD|LLD] [what to change]"
---

Change a design document: $ARGUMENTS

1. Work on a branch named `docs/<task-id>-<short-name>`; ask for the task ID if it is not clear.
2. Read only the sections affected. Make the change in `docs/architecture/HLD.md` or `docs/architecture/LLD.md`.
3. Decide the new version: minor (x.y+1) for added detail or corrections; major (x+1.0) if a decision changed. A major change needs an ADR; run `/adr-new` first if none exists.
4. Update the **Version** and **Last updated** rows, and add a **Revision history** row: version, date, one-line change, ADRs.
5. If the change affects the other document, `docs/architecture/ARCHITECTURE.md`, `CLAUDE.md` or `docs/planning/TASKS.md`, update them in the same branch.
6. Add a `CHANGELOG.md` line under **Unreleased → Changed**.
7. Commit as `docs(arch): <summary> (<task-id>)` and follow `/task-finish` from step 7.
8. After the PR is merged, tell me the tag command: `git tag -a hld-vX.Y -m "<summary>" && git push origin hld-vX.Y` (or `lld-v...`), and remind me to press **Sync now** in the Claude.ai project.
