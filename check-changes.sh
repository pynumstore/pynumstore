#!/bin/bash

# This script is used to check changes of the last update

set -e

VENV="venv"
PROJECT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

cd "$PROJECT_DIR"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    echo "Error: This is not a Git repository."
fi

if [ ! -d "$VENV" ]; then
    python3 -m venv "$VENV"
fi

source "$VENV/bin/activate"
echo "Python environment activated."
python --version
echo ""

read -p "Do you want to open the log file? (y/n) : " res

if [ "$res" = "y" ]; then
    nano "logs/lupdater.log"
    echo "The log file has been opened..."
fi