#!/bin/bash
# Sets up a default agent team for a project.
# Creates agent directories and connects them to the orchestrator.
#
# Usage: ./setup-team.sh <project-name> <project-dir>
# Example: ./setup-team.sh my-app ~/code/my-app
#
# This creates:
#   <project-dir>/.agents/architect   (interactive — generalist)
#   <project-dir>/.agents/backend     (autonomous — backend)
#   <project-dir>/.agents/frontend    (autonomous — frontend)
#   <project-dir>/.agents/security    (autonomous — security)
#   <project-dir>/.agents/qa          (autonomous — generalist)
#   <project-dir>/.agents/devops      (autonomous — devops)
#
# Agents that match a top-level directory (e.g., backend/, frontend/)
# are connected directly to that directory instead of .agents/.

set -e

PROJECT="${1:?Usage: ./setup-team.sh <project-name> <project-dir>}"
PROJECT_DIR="${2:?Usage: ./setup-team.sh <project-name> <project-dir>}"
ORCHESTRATOR_DIR="$(cd "$(dirname "$0")" && pwd)"
CONNECT="${ORCHESTRATOR_DIR}/connect.sh"

PROJECT_DIR="$(cd "$PROJECT_DIR" 2>/dev/null && pwd || echo "$PROJECT_DIR")"

# Default team: name → role
declare -a TEAM=(
  "architect:generalist"
  "backend:backend"
  "frontend:frontend"
  "security:security"
  "qa:generalist"
  "devops:devops"
)

echo "Setting up team for project '${PROJECT}' in ${PROJECT_DIR}"
echo ""

for entry in "${TEAM[@]}"; do
  NAME="${entry%%:*}"
  ROLE="${entry##*:}"

  # If a top-level directory matches the agent name, use it directly
  if [ -d "${PROJECT_DIR}/${NAME}" ]; then
    TARGET="${PROJECT_DIR}/${NAME}"
  else
    TARGET="${PROJECT_DIR}/.agents/${NAME}"
    mkdir -p "$TARGET"
  fi

  echo "→ ${NAME} (${ROLE}) → ${TARGET}"
  "$CONNECT" "$PROJECT" "$NAME" "$ROLE" "$TARGET"
  echo ""
done

echo "┌─────────────────────────────────────────────────┐"
echo "│ Team ready! Connected 6 agents to '${PROJECT}'"
echo "├─────────────────────────────────────────────────┤"
echo "│ Run:  make start ${PROJECT}                     "
echo "└─────────────────────────────────────────────────┘"
