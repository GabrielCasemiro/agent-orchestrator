#!/bin/bash
# Launches the orchestrator + all agents for a project.
# Reads the project manifest created by connect.sh.
#
# Usage: ./start.sh <project-name>
# Example: ./start.sh my-app
#
# The architect agent (role: generalist) opens as interactive.
# All other agents run via agent-runner.sh (autonomous).

set -e

PROJECT="${1:?Usage: ./start.sh <project-name>}"
ORCHESTRATOR_DIR="$(cd "$(dirname "$0")" && pwd)"
RUNNER="${ORCHESTRATOR_DIR}/agent-runner.sh"
MANIFEST="${ORCHESTRATOR_DIR}/projects/${PROJECT}.txt"
API_URL="${ORCHESTRATOR_API_URL:-http://localhost:8000}"

if [ ! -f "$MANIFEST" ]; then
  echo "Error: No manifest found for project '${PROJECT}'."
  echo "Run connect.sh first to register agents."
  echo "Expected: ${MANIFEST}"
  exit 1
fi

# Parse manifest — separate interactive (architect) from autonomous agents
ARCHITECT_NAME=""
ARCHITECT_DIR=""
AUTONOMOUS=()

while IFS=' ' read -r name role dir; do
  [ -z "$name" ] && continue
  if [ "$name" = "architect" ]; then
    ARCHITECT_NAME="$name"
    ARCHITECT_DIR="$dir"
  else
    AUTONOMOUS+=("${name} ${role} ${dir}")
  fi
done < "$MANIFEST"

TOTAL_AUTONOMOUS=${#AUTONOMOUS[@]}
TOTAL=$((TOTAL_AUTONOMOUS + ([ -n "$ARCHITECT_NAME" ] && echo 1 || echo 0)))

# ── Start infrastructure ────────────────────────────
echo "Starting orchestrator API + dashboard..."

osascript -e "
tell application \"Terminal\"
    activate
    do script \"cd ${ORCHESTRATOR_DIR} && make api\"
end tell
"
sleep 2

osascript -e "
tell application \"Terminal\"
    do script \"cd ${ORCHESTRATOR_DIR} && make dashboard\"
end tell
"

# Wait for API
echo "Waiting for API..."
for i in $(seq 1 15); do
  if curl -sf ${API_URL}/ > /dev/null 2>&1; then
    echo "API is up!"
    break
  fi
  sleep 1
done

# ── Launch autonomous agents ────────────────────────
echo "Launching autonomous agents..."

for entry in "${AUTONOMOUS[@]}"; do
  read -r name role dir <<< "$entry"
  echo "  Starting ${name} (${role}) → ${dir}"
  osascript -e "
tell application \"Terminal\"
    do script \"${RUNNER} ${name} ${dir}\"
end tell
"
  sleep 1
done

# ── Wait for agents to register ─────────────────────
if [ "$TOTAL_AUTONOMOUS" -gt 0 ]; then
  echo "Waiting for agents to register..."
  for i in $(seq 1 30); do
    COUNT=$(curl -sf "${API_URL}/api/v1/agents?project=${PROJECT}" 2>/dev/null | python3 -c "import sys,json; print(len(json.load(sys.stdin)))" 2>/dev/null || echo "0")
    echo "  ${COUNT}/${TOTAL_AUTONOMOUS} agents registered..."
    if [ "$COUNT" -ge "$TOTAL_AUTONOMOUS" ]; then
      echo "All autonomous agents online!"
      break
    fi
    sleep 2
  done
fi

# ── Open architect (interactive) ────────────────────
if [ -n "$ARCHITECT_NAME" ]; then
  echo "Opening architect (interactive)..."
  osascript -e "
tell application \"Terminal\"
    do script \"cd ${ARCHITECT_DIR} && claude --dangerously-skip-permissions\"
end tell
"
fi

# ── Summary ─────────────────────────────────────────
echo ""
echo "┌─────────────────────────────────────────────────┐"
echo "│          ${PROJECT} ORCHESTRATOR READY"
echo "├─ Infrastructure ────────────────────────────────┤"
echo "│ API          → http://localhost:8000             │"
echo "│ Dashboard    → http://localhost:3000             │"
echo "├─ Autonomous Agents ─────────────────────────────┤"
for entry in "${AUTONOMOUS[@]}"; do
  read -r name role dir <<< "$entry"
  printf "│ %-12s → %-36s│\n" "$name" "$dir"
done
if [ -n "$ARCHITECT_NAME" ]; then
  echo "├─ Interactive ─────────────────────────────────┤"
  printf "│ %-12s → YOUR TERMINAL %-22s│\n" "$ARCHITECT_NAME" ""
fi
echo "└─────────────────────────────────────────────────┘"
echo ""
echo "Dashboard: http://localhost:3000 → project: ${PROJECT}"
[ -n "$ARCHITECT_NAME" ] && echo "Talk to the architect terminal to give orders."
