---
name: doc-version
description: Find, compare, export or restore an earlier version of a Kritvo document using git history and doc tags.
disable-model-invocation: true
argument-hint: "[file] [list|show|diff|export|restore] [tag-or-commit]"
---

Work with document history: $ARGUMENTS

Use `scripts/doc-version.sh`:

- `list <file>` — tags and commits that touched the file, with the Version row at each tag.
- `show <file> <ref>` — print the file at that tag or commit.
- `diff <file> <ref>` — changes from that ref to the current file.
- `export <file> <ref>` — write `tmp/<name>@<ref>.md` for upload to a Claude.ai chat.
- `restore <file> <ref>` — create a branch and bring back the old content.

For a restore: never rewrite history. After restoring, bump the Version to a new number, add a Revision history row saying which version was restored and why, then continue with `/task-finish`.
Summarise differences in plain language before proposing any restore.
