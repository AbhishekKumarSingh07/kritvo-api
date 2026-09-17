---
paths:
  - "docs/**/*.md"
  - "*.md"
---

# Documentation rules

- `docs/architecture/HLD.md` and `LLD.md`: any change must bump the **Version** row, update **Last updated**, and add a row to **Revision history**. Use `/doc-change`.
- A changed decision needs an ADR; accepted ADRs are never edited except their status line.
- Never edit `docs/architecture/archive/`.
- Write plainly: lead with the answer, short sentences, tables for comparisons, Mermaid for flows.
- Wrap file paths in backticks inside `CLAUDE.md` so they are not imported into context.
- Keep `docs/planning/TASKS.md` and `docs/status/STATUS.md` consistent with GitHub issues.
