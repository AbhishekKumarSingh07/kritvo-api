# Documentation index

All Kritvo design, planning and status documents live here, in `kritvo-api`. The UI repository `kritvo-web` points to this folder instead of keeping copies. `main` is the source of truth; Claude Docs, chat drafts and exported files are working copies.

| Folder | Contents | Changes how |
| --- | --- | --- |
| `architecture/` | [HLD](architecture/HLD.md), [LLD](architecture/LLD.md), [one-page summary](architecture/ARCHITECTURE.md), `archive/` of superseded designs | PR with version bump (`/doc-change`) |
| `adr/` | Architecture Decision Records ([index](adr/README.md)) | New ADR per decision (`/adr-new`); accepted ADRs are never edited |
| `product/` | [Project context](product/PROJECT_CONTEXT.md) for Claude and new team members | Normal PR |
| `engineering/` | [Coding standards](engineering/CODING_STANDARDS.md), [Git workflow](engineering/GIT_WORKFLOW.md), [Definition of done](engineering/DEFINITION_OF_DONE.md) | Normal PR |
| `planning/` | [Task plan](planning/TASKS.md) for both repositories | `/status-update` and task PRs |
| `status/` | [Current status](status/STATUS.md) and monthly `worklog/` | `/status-update` at the end of each session |
| `reviews/` | Design and code review records for both repositories ([how](reviews/README.md)) | One file per review |
| `setup/` | [Setup guide](setup/SETUP_GUIDE.md) | Normal PR |

## Document versions

- HLD and LLD carry a **Version** row and a **Revision history** table. Minor versions (2.0 → 2.1) add detail or fix mistakes; major versions (2.x → 3.0) change a decision and must reference an ADR.
- Each approved version is tagged in `kritvo-api`: `hld-v2.0`, `lld-v1.2`.
- To read, compare or restore an old version, use `scripts/doc-version.sh` (see [Git workflow](engineering/GIT_WORKFLOW.md#document-versions-and-rollback)).

## Files synced to the Claude.ai project

Add both repositories through the project's GitHub integration and press **Sync now** after each merge.

- From `kritvo-api`: `README.md`, `CLAUDE.md`, `CHANGELOG.md`, `docs/architecture/` (without `archive/`), `docs/adr/`, `docs/product/`, `docs/engineering/`, `docs/planning/`, `docs/status/STATUS.md`.
- From `kritvo-web`: `README.md`, `CLAUDE.md`, `CHANGELOG.md`.

Leave out `docs/architecture/archive/` so old designs do not mix with current ones.
