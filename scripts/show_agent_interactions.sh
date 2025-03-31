#!/bin/bash

# Script to display agent interactions from the log files
# Usage: ./show_agent_interactions.sh [log_file]

LOG_DIR="output/logs"
LOG_FILE=""

if [ -n "$1" ]; then
  LOG_FILE="$1"
else
  # Get the most recent log file
  LOG_FILE=$(ls -t $LOG_DIR/agent_interactions_*.log 2>/dev/null | head -1)
  if [ -z "$LOG_FILE" ]; then
    echo "No agent interaction logs found"
    exit 1
  fi
fi

echo "Displaying agent interactions from: $LOG_FILE"
echo "----------------------------------------"
echo ""

# Display only agent interactions from the log file
cat "$LOG_FILE" | grep -E "\[(.*)\].*→.*\|" --color=never

echo ""
echo "----------------------------------------"
echo "Note: To see latest interactions, run with: tail -f $LOG_FILE | grep -E '\[(.*)\].*→.*\|' --color=never" 