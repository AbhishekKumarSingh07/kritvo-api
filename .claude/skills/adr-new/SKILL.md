---
name: adr-new
description: Create the next numbered Architecture Decision Record for Kritvo from the template and add it to the index.
disable-model-invocation: true
argument-hint: "[decision title]"
---

Create an ADR titled: $ARGUMENTS

1. Find the highest number in `docs/adr/` and use the next one, zero-padded to four digits.
2. Copy `docs/adr/0000-template.md` to `docs/adr/NNNN-<kebab-title>.md` and fill in context, decision, alternatives (at least one) and consequences from our discussion and the design docs. Status: Proposed.
3. If it supersedes an ADR, set the old ADR's status line to `Superseded by ADR-NNNN` and change nothing else in it.
4. Add a row to the table in `docs/adr/README.md`.
5. List which HLD or LLD sections must change and offer to run `/doc-change`.
