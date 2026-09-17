---
name: task-start
description: Start work on a Kritvo task (TASK-### or BIZ-###) with the right branch, context and plan.
disable-model-invocation: true
argument-hint: "[TASK-###]"
arguments: [task]
---

Start task $task.

1. Read the task's row in `docs/planning/TASKS.md` and its details in `docs/architecture/LLD.md` section 14 (or HLD sections 1.4 and 13 for BIZ tasks). Read only the design sections the task needs.
2. Check the task's **Repo** column. If it is `web`, stop and tell me to run this in `kritvo-web`. Otherwise run `gh issue list --search "$task in:title" --state all` to find the issue; if none exists, offer to create it with the Task template.
3. Check dependencies in `docs/planning/TASKS.md`. If any dependency is not Done, stop and report it.
4. Make sure the working tree is clean and `main` is up to date: `git switch main && git pull --ff-only`.
5. Create the branch `<type>/$task-<short-name>` using the task's type.
6. Set the task's status to **In progress** in `docs/planning/TASKS.md`.
7. Write a short plan: files to touch, tests to add, risks, and any conflict between the task and the current docs. Wait for my go-ahead before writing code.
