#!/bin/bash

# This script is used to push changes to the Git repository.
# It will:
# 1. Commit all changes with a timestamped message.
# 2. Push the changes to the remote repository.

set -e
cd "$(dirname "$0")"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    echo "Error: This is not a Git repository."
    exit 1
fi

COMMIT_MSG="$(date '+%Y-%m-%d %H:%M:%S') Update"

git add -A

if git diff --cached --quiet; then
    echo "Error: No changes to commit."
    exit 0
fi

git commit -m "$COMMIT_MSG"

git push

echo "Push completed successfully : $COMMIT_MSG"
