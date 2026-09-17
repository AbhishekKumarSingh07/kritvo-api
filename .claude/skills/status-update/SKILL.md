---
name: status-update
description: Record what was done in this Kritvo work session in the monthly worklog and refresh STATUS.md.
disable-model-invocation: true
---

Update the project status for today.

1. Collect today's work from both repositories: `git log --since=midnight --oneline --all` here and `git -C ../kritvo-web log --since=midnight --oneline --all`; open PRs with `gh pr list --author @me` and `gh pr list --author @me --repo <owner>/kritvo-web`; and what we did in this session.
2. Add an entry at the top of `docs/status/worklog/<YYYY-MM>.md` (create the file from the previous month's format if needed) with **Done**, **Decisions**, **Next** and **Links** (PRs, issues, tags).
3. Refresh `docs/status/STATUS.md`: last-updated date, phase, summary, next three actions, blocked items, pending decisions, latest document versions and tags.
4. Update the Status column in `docs/planning/TASKS.md` from the issues in both repositories (`gh issue list --state all --search "TASK- in:title"`, and the same with `--repo <owner>/kritvo-web`); list what changed.
5. Commit on the current branch as `docs(plan): status update <YYYY-MM-DD> (<task-id>)` or, if on `main`, create `docs/status-<YYYY-MM-DD>` and open a small PR with that same title. `<task-id>` is the task worked on in this session, or `BIZ-000` if none — the commit message and PR title must end with a task ID or the pr-title check fails. Ask before pushing.
