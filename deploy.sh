#!/usr/bin/env bash
# deploy.sh — one-command go-live for the UK Equity Research tracker.
#
# Automates everything that doesn't require interactive auth:
#   1. sanity-checks git identity + repo state
#   2. creates the initial commit (if none exists yet)
#   3. pushes to GitHub (credential manager may pop up and ask you to log in)
#   4. polls the GitHub API and prints the exact remaining click-path
#      (Settings -> Pages -> Source: GitHub Actions; then run the workflow)
#
# Usage:  bash deploy.sh https://github.com/<you>/<repo>.git
# Safe to re-run: it skips steps that are already done.
set -euo pipefail

REPO_URL="${1:-}"
cd "$(dirname "$0")"

bold() { printf '\n\033[1m== %s ==\033[0m\n' "$1"; }
fail() { printf '\033[31mERROR: %s\033[0m\n' "$1" >&2; exit 1; }
ok()   { printf '  \033[32mok:\033[0m %s\n' "$1"; }

bold "1. Git identity"
[ -n "$(git config user.name)" ] && [ -n "$(git config user.email)" ] \
  || fail "set an identity first:
  git config user.name \"Your Name\"
  git config user.email \"you@example.com\""
ok "author: $(git config user.name) <$(git config user.email)>"

bold "2. Commit"
if git rev-parse HEAD >/dev/null 2>&1; then
  ok "commit exists: $(git log --oneline -1)"
else
  git add -A
  git commit -m "Initial commit: audit-ready UK equity research tracker"
  ok "created initial commit"
fi

bold "3. Remote"
[ -n "$REPO_URL" ] || fail "pass the repo URL:  bash deploy.sh https://github.com/<you>/<repo>.git
(create the empty repo first at https://github.com/new — do NOT add a README)"
if git remote get-url origin >/dev/null 2>&1; then
  git remote set-url origin "$REPO_URL"
  ok "origin updated: $REPO_URL"
else
  git remote add origin "$REPO_URL"
  ok "origin added: $REPO_URL"
fi

bold "4. Push"
BRANCH="$(git branch --show-current)"
git push -u origin "$BRANCH"
ok "pushed $BRANCH to origin"

bold "5. Verify + remaining clicks"
SLUG="${REPO_URL#*github.com/}"; SLUG="${SLUG%.git}"
sleep 3
HTTP="$(curl -s -o /dev/null -w '%{http_code}' "https://api.github.com/repos/$SLUG")"
[ "$HTTP" = "200" ] || fail "repo $SLUG not visible on GitHub (HTTP $HTTP) — create it at https://github.com/new and re-run"
ok "repo exists: https://github.com/$SLUG"
PAGES="$(curl -s "https://api.github.com/repos/$SLUG/pages" | sed -n 's/.*"status": *"\([a-z_]*\)".*/\1/p' | head -1)"
GH_USER="${SLUG%%/*}"; GH_REPO="${SLUG#*/}"
SITE_URL="https://$GH_USER.github.io/$GH_REPO/"
if [ "$PAGES" = "built" ]; then
  CNAME="$(curl -s "https://api.github.com/repos/$SLUG/pages" | sed -n 's/.*"cname": *"\([^"]*\)".*/\1/p')"
  echo "  Pages is LIVE:  ${CNAME:+https://$CNAME/}"
  [ -n "$CNAME" ] || echo "  Site URL:       $SITE_URL"
else
  cat <<EOF
  Three clicks left (I can't press these for you):
    1. https://github.com/$SLUG/settings/pages  ->  Source: "GitHub Actions"
    2. https://github.com/$SLUG/actions  ->  "Deploy dashboard"  ->  "Run workflow"
    3. wait ~2 min; your site appears under Settings -> Pages
  Re-run this script any time to re-check.
EOF
fi
