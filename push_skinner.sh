#!/bin/bash
# push_skinner.sh — One-shot commit + push of the Skinner baseline.
# Run with:  bash push_skinner.sh
# You will be prompted for your GitHub username + Personal Access Token
# (or, if you've set up gh auth login, it'll just work silently).

set -e  # exit on any error

cd "$(dirname "$0")"

echo "==> Step 1: clearing any stale lock file"
rm -f .git/index.lock

echo "==> Step 2: checking remote"
if ! git remote get-url origin >/dev/null 2>&1; then
  echo "    adding github.com/GrobeStreet/pasv as origin"
  git remote add origin https://github.com/GrobeStreet/pasv.git
else
  echo "    origin already configured: $(git remote get-url origin)"
fi

echo "==> Step 3: staging code/baselines/"
git add code/baselines/

echo "==> Step 4: status check"
git status --short

echo "==> Step 5: committing (skips if nothing new to commit)"
if git diff --cached --quiet; then
  echo "    nothing staged — skipping commit"
else
  git commit -m "Add Skinner 2012 MDP cutoff baseline in code/baselines/"
fi

echo "==> Step 6: pushing to GitHub main"
git push -u origin main

echo ""
echo "DONE. Verify at: https://github.com/GrobeStreet/pasv/tree/main/code/baselines"
