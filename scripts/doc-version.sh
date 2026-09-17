#!/usr/bin/env bash
# Read, compare, export or restore earlier versions of a document.
#
# Usage (paths from the repository root):
#   scripts/doc-version.sh list    <file>
#   scripts/doc-version.sh show    <file> <tag-or-commit>
#   scripts/doc-version.sh diff    <file> <tag-or-commit>
#   scripts/doc-version.sh export  <file> <tag-or-commit>
#   scripts/doc-version.sh restore <file> <tag-or-commit>
#
# Examples:
#   scripts/doc-version.sh list docs/architecture/HLD.md
#   scripts/doc-version.sh diff docs/architecture/LLD.md lld-v1.1
#   scripts/doc-version.sh export docs/architecture/HLD.md hld-v2.0
set -euo pipefail

usage() { sed -n '2,15p' "$0" | sed 's/^# \{0,1\}//'; exit 1; }

cmd="${1:-}"
file="${2:-}"
ref="${3:-}"
[[ -z "$cmd" || -z "$file" ]] && usage

cd "$(git rev-parse --show-toplevel)"

case "$(basename "$file")" in
  HLD.md) prefix="hld" ;;
  LLD.md) prefix="lld" ;;
  *) prefix="" ;;
esac

version_in() { awk -F'|' '/^\| \*\*Version\*\* \|/ && !found { gsub(/ /, "", $3); print $3; found = 1 }'; }
need_ref() { [[ -n "$ref" ]] || { echo "This command needs a tag or commit." >&2; usage; }; }

case "$cmd" in
  list)
    [[ -f "$file" ]] && echo "Current version: $(version_in < "$file")"
    if [[ -n "$prefix" ]]; then
      echo
      echo "Tags:"
      git tag --list "${prefix}-v*" --sort=-v:refname | while read -r t; do
        printf '  %-12s %s  Version %s\n' "$t" \
          "$(git log -1 --format=%ad --date=short "$t")" \
          "$({ git show "$t:$file" 2>/dev/null || true; } | version_in)"
      done
    fi
    echo
    echo "Commits that changed $file:"
    git log --follow --format='  %h  %ad  %s' --date=short -- "$file"
    ;;
  show)
    need_ref
    git show "$ref:$file"
    ;;
  diff)
    need_ref
    git diff "$ref" -- "$file"
    ;;
  export)
    need_ref
    mkdir -p tmp
    out="tmp/$(basename "$file" .md)@${ref//\//-}.md"
    git show "$ref:$file" > "$out"
    echo "Wrote $out (tmp/ is not committed). Upload it to a Claude chat to discuss that version."
    ;;
  restore)
    need_ref
    if [[ -n "$(git status --porcelain)" ]]; then
      echo "Working tree has uncommitted changes. Commit or stash them first." >&2
      exit 1
    fi
    name="$(basename "$file" .md | tr '[:upper:]' '[:lower:]')"
    branch="docs/restore-${name}-${ref//\//-}"
    git switch -c "$branch"
    git restore --source="$ref" -- "$file"
    echo "Restored $file from $ref on branch $branch."
    echo "Next: set a NEW Version number, add a Revision history row"
    echo "(\"Restores the content of $ref because ...\"), commit, and open a PR."
    ;;
  *)
    usage
    ;;
esac
