#!/bin/bash

# Script to display agent interactions from logs
# Usage: ./show_agents.sh [follow] [latest|all]

FOLLOW=0
if [[ "$1" == "follow" ]]; then
  FOLLOW=1
  shift
fi

MODE="latest"
if [[ "$1" == "all" ]]; then
  MODE="all"
fi

LOG_DIR="output/logs"

# Determine which log file to use
if [[ "$MODE" == "all" ]]; then
  # Use the consolidated log that contains all interactions
  LOGFILE="$LOG_DIR/agent_interactions.log"
  
  if [ ! -f "$LOGFILE" ]; then
    echo "Consolidated agent interaction log not found."
    echo "Run test_agent_logging.py to initialize it or run an investigation first."
    exit 1
  fi
else
  # Use the most recent investigation log
  LOGFILE=$(ls -t $LOG_DIR/agent_interactions_*.log 2>/dev/null | head -1)
  
  if [ -z "$LOGFILE" ]; then
    echo "No agent interaction logs found"
    exit 1
  fi
fi

echo "====================================================="
echo "  Kubernetes Agent Interactions Log Viewer"
echo "====================================================="
echo ""
echo "Showing agent interactions from: $LOGFILE"
echo "-----------------------------------------------------"

if [ $FOLLOW -eq 1 ]; then
  # Follow the log file in real-time (like tail -f)
  echo "Showing live agent interactions (Ctrl+C to exit)..."
  tail -f "$LOGFILE" | grep -E "AGENT (INTERACTION|ACTION)" --color=auto
else
  # Just display the current contents
  echo "Showing current agent interactions..."
  grep -E "AGENT (INTERACTION|ACTION)" "$LOGFILE" --color=auto
fi

echo ""
echo "-----------------------------------------------------"
echo "Usage:"
echo "  ./show_agents.sh           - Show latest log"
echo "  ./show_agents.sh follow    - Follow latest log"
echo "  ./show_agents.sh all       - Show all interactions"
echo "  ./show_agents.sh follow all - Follow all interactions" 