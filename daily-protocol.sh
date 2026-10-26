#!/bin/bash

# This script is used to run the daily protocol in a detached screen session.
# It will be executed in the background every day at 12:00 PM with cron.

set -e
cd "$(dirname "$0")"

./git-pull.sh

SESSION="pynumstore_screen"
VENV="venv"
PYTHON_SCRIPT="python_scripts/updater.py"

if ! command -v screen >/dev/null 2>&1; then
    echo "Error: screen is not installed."
    exit 1
fi

if [ ! -d "$VENV" ]; then
    python3 -m venv "$VENV"
fi

if screen -list | grep -q "\.${SESSION}[[:space:]]"; then
    echo "The session '$SESSION' already exists."
    echo "To reattach to it: screen -r $SESSION"
    exit 1
fi

screen -S "$SESSION" -dm bash -c "
    source '$VENV/bin/activate'
    echo 'Python environment activated.'
    python --version
    echo ''

    if [ -f '$PYTHON_SCRIPT' ]; then
        python -u '$PYTHON_SCRIPT' --daily-protocol
    else
        echo 'No file $PYTHON_SCRIPT found.'
    fi

    echo ''
    echo 'Execution finished.'
    exit
"

echo "Session '$SESSION' launched."
echo "To reattach to it: screen -r $SESSION"
