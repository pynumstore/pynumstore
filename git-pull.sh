#!/bin/bash

# This script is used to pull changes from the Git repository.

set -e
cd "$(dirname "$0")"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    echo "Error: This is not a Git repository."
    exit 1
fi

git pull

echo "Pull completed successfully"
