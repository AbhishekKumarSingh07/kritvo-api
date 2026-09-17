# Git workflow

## Repositories

| Repository | Holds | Issues for |
| --- | --- | --- |
| `kritvo-api` | Backend, `openapi/`, `infra/`, all `docs/` | Business tasks (BIZ) and API tasks |
| `kritvo-web` | Office app, PWA, portal | Web tasks |

Clone both side by side, for example `~/code/kritvo/kritvo-api` and `~/code/kritvo/kritvo-web`. The web repository expects `../kritvo-api` to exist.

### Changes that touch both repositories

1. Change the API first, backward-compatibly (add fields and endpoints; do not remove or rename). Regenerate and commit `openapi/openapi.json` in the same PR.
2. Merge the API PR.
3. In `kritvo-web`, pull the latest `kritvo-api`, run `pnpm gen:api`, make the UI change, and open the web PR.
4. Both PRs use the same task ID in the title. The web PR says `Refs <owner>/kritvo-api#<issue>` (or `Closes <owner>/kritvo-api#<issue>` if it finishes the task).
5. Remove old API fields only in a later API PR, after the web app has stopped using them.

## Branches

- `main` is always releasable and protected: changes arrive only through pull requests with passing checks.
- Work branches: `<type>/TASK-###-short-name` (engineering) or `docs/BIZ-###-short-name` (business docs).
- Delete branches after merge (GitHub does this automatically once configured).

## Commits and pull request titles

Conventional Commits, ending with the task ID:

```text
<type>(<scope>): <summary in imperative mood> (TASK-###)

feat(api): add tenant RLS helpers (TASK-002)
docs(arch): bump LLD to 1.2 with queue decision (TASK-004)
fix(web): keep outbox after token refresh failure (TASK-017)
```

| Type | Use for |
| --- | --- |
| `feat` | New behaviour |
| `fix` | Bug fix |
| `refactor` | Code change with no behaviour change |
| `perf` | Performance |
| `security` | Security hardening |
| `test` | Tests only |
| `docs` | Documentation only |
| `ci`, `build`, `chore` | Pipeline, build, housekeeping |

Scopes in `kritvo-api`: a module name (`identity`, `jobs`, `inventory`, `wa` …), `api` for cross-cutting code, `infra`, `arch`, `adr`, `plan`, `repo`.
Scopes in `kritvo-web`: `office`, `pwa`, `portal`, `ui`, `api-client`, `repo`.

Pull requests are **squash-merged**, so the PR title becomes the single commit on `main`. CI checks the title format.

## Pull requests

- Link the issue with `Closes #123`.
- Fill in the template, including documentation impact.
- Add the `claude-review` label to request an automated Claude review (costs API credits).
- Merge only when all required checks pass.

## Releases

- Each repository tags its own releases on `main` with Semantic Versioning: `v0.1.0` (first pilot build), `v0.2.0`, and so on. Record in the web release notes which API version it needs.
- Before tagging, move the `CHANGELOG.md` Unreleased entries under the new version heading.
- Create the GitHub release from the tag: `gh release create v0.1.0 --notes-from-tag` or paste the changelog section.

## Document versions and rollback

HLD and LLD have a **Version** row and a **Revision history** table. CI fails a PR that changes either file without adding a new Version row.

Document tags live only in `kritvo-api`. After a document change is merged, tag it:

```bash
git switch main && git pull
git tag -a hld-v2.1 -m "HLD 2.1: <what changed>"
git push origin hld-v2.1
```

Look back, compare, share or restore with the helper script (it wraps the git commands shown after it):

```bash
scripts/doc-version.sh list    docs/architecture/HLD.md            # versions, tags and commits
scripts/doc-version.sh show    docs/architecture/HLD.md hld-v2.0   # print an old version
scripts/doc-version.sh diff    docs/architecture/HLD.md hld-v2.0   # what changed since then
scripts/doc-version.sh export  docs/architecture/HLD.md hld-v2.0   # save to tmp/ to upload to Claude
scripts/doc-version.sh restore docs/architecture/HLD.md hld-v2.0   # bring old text back on a new branch
```

Plain git equivalents:

```bash
git log --oneline --follow -- docs/architecture/HLD.md
git show hld-v2.0:docs/architecture/HLD.md
git diff hld-v2.0 HEAD -- docs/architecture/HLD.md
git restore --source=hld-v2.0 -- docs/architecture/HLD.md   # then bump Version and open a PR
```

Rollback never rewrites history: restoring an old version creates a new commit and a new version number (for example 2.3 restoring the content of 2.0), with the reason in the Revision history.

On GitHub, open the file, click **History**, pick a commit, and use **Browse files** to read or link that exact version.

## Sharing a version with Claude

- **Claude.ai project:** the GitHub integration shows the synced branch; press **Sync now** after merging. For an older version, run `scripts/doc-version.sh export ...` and upload the file from `tmp/` to the chat.
- **Claude Code:** in `kritvo-api`, ask it to run `scripts/doc-version.sh show <file> <tag>`. In `kritvo-web`, Claude reads the current docs from `../kritvo-api/docs`; for an old version, run the script in `kritvo-api` and export it.
- **Claude Docs (live drafts):** use them for collaborative drafting only. When a draft is final, copy it into the repository through a `/doc-change` PR; the repository version is the one that counts.
