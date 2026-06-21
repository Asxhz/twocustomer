#!/usr/bin/env bash
# Create a GitHub repo from demo-broken-site/ and push it, so you can connect it
# in TwoCustomer and fix it. Requires the `gh` CLI (gh auth login) — or set
# GH_REPO to an existing empty repo URL and we'll push with git.
#
# Usage:
#   scripts/push_demo_repo.sh                # creates <user>/lumina-demo via gh
#   GH_REPO=https://github.com/you/x.git scripts/push_demo_repo.sh   # push to existing
set -euo pipefail
DIR="$(cd "$(dirname "$0")/../demo-broken-site" && pwd)"
cd "$DIR"

if [ ! -d .git ]; then
  git init -q
  git add -A
  git -c user.email=demo@twocustomer.app -c user.name=TwoCustomer commit -qm "Lumina demo (broken hero)"
  git branch -M main
fi

if [ -n "${GH_REPO:-}" ]; then
  git remote remove origin 2>/dev/null || true
  git remote add origin "$GH_REPO"
  git push -u origin main
  echo "Pushed to $GH_REPO"
elif command -v gh >/dev/null 2>&1; then
  gh repo create lumina-demo --public --source=. --remote=origin --push
  echo "Created + pushed. Connect this repo URL in TwoCustomer /admin/settings."
else
  echo "No gh CLI and no GH_REPO set. Either: brew install gh && gh auth login,"
  echo "or create an empty repo and re-run with GH_REPO=<git url>."
  exit 1
fi
