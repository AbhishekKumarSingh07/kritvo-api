#!/usr/bin/env bash
# One-time GitHub setup for both Kritvo repositories.
#
# Run from the kritvo-api repository root AFTER both repositories are pushed:
#   gh auth login
#   gh auth refresh -s project      # needed for the project board
#   scripts/bootstrap-github.sh                 # web repo defaults to <owner>/kritvo-web
#   WEB_REPO=owner/other-name scripts/bootstrap-github.sh
#
# Safe to re-run: existing labels, milestones, issues and tags are skipped.
set -euo pipefail

command -v gh >/dev/null || { echo "Install the GitHub CLI first: https://cli.github.com" >&2; exit 1; }
cd "$(git rev-parse --show-toplevel)"

API_REPO="$(gh repo view --json nameWithOwner -q .nameWithOwner)"
OWNER="${API_REPO%%/*}"
WEB_REPO="${WEB_REPO:-$OWNER/kritvo-web}"
ME="$(gh api user -q .login)"
echo "==> API repository: $API_REPO"
echo "==> Web repository: $WEB_REPO"
echo "==> Signed in as:   $ME"

warn() { echo "  ! $*" >&2; }
lower() { printf %s "$1" | tr '[:upper:]' '[:lower:]'; }

gh repo view "$WEB_REPO" >/dev/null 2>&1 || { echo "Cannot see $WEB_REPO. Push kritvo-web first or set WEB_REPO." >&2; exit 1; }
grep -q YOUR_GITHUB_USERNAME .github/CODEOWNERS && warn "kritvo-api CODEOWNERS still has YOUR_GITHUB_USERNAME; replace with @$ME and commit."

setup_repo() { # repo
  local repo="$1"
  echo "==> $repo: settings (squash merge only, PR title as commit, delete merged branches)"
  gh repo edit "$repo" --enable-squash-merge --enable-merge-commit=false \
    --enable-rebase-merge=false --delete-branch-on-merge --enable-issues >/dev/null
  gh api -X PATCH "repos/$repo" -f squash_merge_commit_title=PR_TITLE -f squash_merge_commit_message=PR_BODY >/dev/null

  echo "==> $repo: labels"
  while IFS='|' read -r name color desc; do
    gh label create "$name" --repo "$repo" --color "$color" --description "$desc" --force >/dev/null
  done <<'LABELS'
task|0E8A16|Planned task from kritvo-api docs/planning/TASKS.md
type:feat|1D76DB|New behaviour
type:fix|D73A4A|Bug fix
type:refactor|C5DEF5|No behaviour change
type:perf|FBCA04|Performance or operations
type:security|B60205|Security work
type:test|BFD4F2|Tests only
type:docs|0075CA|Documentation
type:chore|EDEDED|Housekeeping
type:ci|5319E7|Pipeline
type:business|F9D0C4|Company, legal, sales or partner work
risk:high|B60205|High risk
risk:medium|FBCA04|Medium risk
risk:low|0E8A16|Low risk
also:api|C2E0C6|Also needs a change in kritvo-api
also:web|BFDADC|Also needs a change in kritvo-web
blocked|000000|Waiting on something
needs-decision|D93F0B|Needs a decision or ADR
claude-review|7057FF|Request an automated Claude review
dependencies|0366D6|Dependency updates
LABELS

  echo "==> $repo: milestones"
  local ms desc existing
  existing="$(gh api "repos/$repo/milestones?state=all&per_page=100" -q '.[].title')"
  while IFS='|' read -r ms desc; do
    if printf '%s\n' "$existing" | grep -qxF "$ms"; then echo "  = $ms"
    else gh api "repos/$repo/milestones" -f title="$ms" -f description="$desc" >/dev/null && echo "  + $ms"; fi
  done <<'MILESTONES'
Phase 0 - Foundations|Name, company, WhatsApp verification, design partner, repo setup
Phase 1 - MVP|Core platform live at Rahul Electricals
Phase 2 - First customers|10 paying outside tenants
Phase 3 - Repeatable growth|50 paying tenants, more industry templates
MILESTONES
}

protect_main() { # repo checks-json
  local repo="$1" checks="$2"
  echo "==> $repo: branch protection for main"
  if ! gh api -X PUT "repos/$repo/branches/main/protection" --input - >/dev/null <<JSON
{
  "required_status_checks": { "strict": true, "contexts": $checks },
  "enforce_admins": true,
  "required_pull_request_reviews": null,
  "restrictions": null,
  "required_linear_history": true,
  "allow_force_pushes": false,
  "allow_deletions": false,
  "required_conversation_resolution": true
}
JSON
  then
    warn "Branch protection failed for $repo. Private repositories need GitHub Pro, Team or Enterprise."
    warn "Until then, follow the PR-only workflow by discipline."
  fi
}

setup_repo "$API_REPO"
setup_repo "$WEB_REPO"

echo "==> Issues from docs/planning/TASKS.md (skips Done and existing)"
created_urls=()
trim() { local s="$1"; s="${s#"${s%%[![:space:]]*}"}"; printf %s "${s%"${s##*[![:space:]]}"}"; }

issue_exists() { # repo id
  [[ "$(gh issue list --repo "$1" --state all --search "\"$2\" in:title" --json title \
        -q "[.[] | select(.title | startswith(\"$2:\"))] | length")" != "0" ]]
}

create_issue() { # repo id title type risk deps milestone extra-label
  local repo="$1" id="$2" title="$3" type="$4" risk="$5" deps="$6" ms="$7" extra="$8" ref labels body url
  if issue_exists "$repo" "$id"; then echo "  = $id ($repo)"; return; fi
  if [[ "$id" == BIZ-* ]]; then ref="HLD sections 1.4 and 13"; else ref="LLD section 14"; fi
  labels="task,type:$type"
  [[ -n "$risk" ]] && labels="$labels,risk:$(lower "$risk")"
  [[ -n "$extra" ]] && labels="$labels,$extra"
  body="**Task:** $id
**Plan:** $API_REPO → docs/planning/TASKS.md
**Design reference:** $ref (in $API_REPO)
**Depends on:** ${deps:-None}

Acceptance criteria: see the design reference. Start with \`/task-start $id\` in Claude Code."
  url="$(gh issue create --repo "$repo" --title "$id: $title" --body "$body" --label "$labels" --milestone "$ms")"
  created_urls+=("$url")
  echo "  + $id ($repo)"
}

# Business tasks: | ID | Title | Depends on | Status | Notes |
while IFS='|' read -r _ id title deps status _; do
  id="$(trim "$id")"; title="$(trim "$title")"; deps="$(trim "$deps")"; status="$(trim "$status")"
  [[ "$status" == "Done" ]] && continue
  [[ "$deps" == "—" ]] && deps=""
  create_issue "$API_REPO" "$id" "$title" "business" "" "$deps" "Phase 0 - Foundations" ""
done < <(grep -E '^\| BIZ-[0-9]{3} ' docs/planning/TASKS.md)

# Engineering tasks: | ID | Title | Repo | Type | Depends on | Risk | Status |
while IFS='|' read -r _ id title repo type deps risk status _; do
  id="$(trim "$id")"; title="$(trim "$title")"; repo="$(trim "$repo")"; type="$(trim "$type")"
  deps="$(trim "$deps")"; risk="$(trim "$risk")"; status="$(trim "$status")"
  [[ "$status" == "Done" ]] && continue
  [[ "$deps" == "—" ]] && deps=""
  primary="${repo%% *}"; extra=""
  case "$repo" in
    "api + web") extra="also:web" ;;
    "web + api") extra="also:api" ;;
  esac
  target="$API_REPO"; [[ "$primary" == "web" ]] && target="$WEB_REPO"
  ms="Phase 1 - MVP"; [[ "$id" == "TASK-000" ]] && ms="Phase 0 - Foundations"
  create_issue "$target" "$id" "$title" "$type" "$risk" "$deps" "$ms" "$extra"
done < <(grep -E '^\| TASK-[0-9]{3} ' docs/planning/TASKS.md)

echo "==> Project board 'Kritvo Roadmap' (both repositories)"
if ! gh project list --owner "$OWNER" >/dev/null 2>&1; then
  warn "Cannot list projects. Run: gh auth refresh -s project   (then re-run this script)"
else
  num="$(gh project list --owner "$OWNER" --format json -q '.projects[] | select(.title=="Kritvo Roadmap") | .number' | head -1)"
  if [[ -z "$num" ]]; then
    num="$(gh project create --owner "$OWNER" --title "Kritvo Roadmap" --format json -q .number)"
    echo "  + project #$num"
    for r in "$API_REPO" "$WEB_REPO"; do
      gh project link "$num" --owner "$OWNER" --repo "$r" >/dev/null 2>&1 \
        || warn "Link project #$num to $r from the project's settings page."
    done
  else
    echo "  = project #$num"
  fi
  for url in "${created_urls[@]:-}"; do
    [[ -n "$url" ]] && gh project item-add "$num" --owner "$OWNER" --url "$url" >/dev/null && echo "  + added $url"
  done
fi

protect_main "$API_REPO" '["ci", "docs-lint", "pr-title", "gitleaks"]'
protect_main "$WEB_REPO" '["ci", "pr-title", "gitleaks"]'

echo "==> Document version tags (kritvo-api)"
for pair in "hld-v2.0:HLD 2.0 - Kritvo rewrite" "lld-v1.2:LLD 1.2 - two repositories"; do
  tag="${pair%%:*}"; msg="${pair#*:}"
  if ! git rev-parse -q --verify "refs/tags/$tag" >/dev/null; then
    git tag -a "$tag" -m "$msg"
    echo "  + $tag (local)"
  fi
  if git ls-remote --exit-code --tags origin "refs/tags/$tag" >/dev/null 2>&1; then
    echo "  = $tag on GitHub"
  elif git push origin "$tag" >/dev/null 2>&1; then
    echo "  + $tag pushed"
  else
    warn "Could not push $tag. Run: git push origin $tag"
  fi
done

cat <<'MSG'

==> Done. Manual steps left:
  1. Secrets (each repository: Settings > Secrets and variables > Actions):
       ANTHROPIC_API_KEY     - both repos, for the claude-review workflow (optional)
       GITLEAKS_LICENSE      - both repos, only if they belong to an organization
       API_REPO_READ_TOKEN   - kritvo-web only, for the API contract check (fine-grained token,
                               read-only "Contents" on kritvo-api); then set the repository
                               variable API_CONTRACT_CHECK=true in kritvo-web
  2. Project board: add "In review" and "Blocked" to the Status field; add a "Repository" column.
  3. Claude.ai project: connect both repositories and select the files listed in docs/README.md.
MSG
