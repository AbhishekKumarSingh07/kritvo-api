# Definition of done

A task is done when all of these are true:

- [ ] Acceptance criteria in the task are met and demonstrated (test, screenshot or short note in the PR).
- [ ] Tests added or updated; all CI checks pass.
- [ ] Tenant isolation tests pass for any new table.
- [ ] No secrets, no debug leftovers, no commented-out code.
- [ ] Errors, logs and user-facing strings follow the standards (Hindi and English where user-facing).
- [ ] `CHANGELOG.md` Unreleased section updated.
- [ ] `docs/planning/TASKS.md` status updated.
- [ ] Docs updated if behaviour differs from HLD or LLD (with version bump) or an ADR was needed.
- [ ] `.env.example` updated if configuration changed.
- [ ] PR title follows the convention and the PR closes its issue.
