#!/bin/bash
# Connects a project directory to the orchestrator by generating .mcp.json and CLAUDE.md.
#
# Usage:
#   ./connect.sh <project-name> <agent-name> <agent-role> [target-dir]
#
# Example:
#   ./connect.sh my-app backend backend ~/projects/my-app
#   ./connect.sh my-app frontend frontend ~/projects/my-app
#
# Roles: backend, frontend, devops, generalist

set -e

PROJECT="${1:?Usage: ./connect.sh <project> <agent-name> <role> [target-dir]}"
AGENT_NAME="${2:?Usage: ./connect.sh <project> <agent-name> <role> [target-dir]}"
AGENT_ROLE="${3:-generalist}"
TARGET_DIR="${4:-.}"
ORCHESTRATOR_DIR="$(cd "$(dirname "$0")" && pwd)"
SERVER_PY="${ORCHESTRATOR_DIR}/mcp_server/server.py"
VENV_PYTHON="${ORCHESTRATOR_DIR}/mcp_server/.venv/bin/python"

if [ ! -f "$VENV_PYTHON" ]; then
  echo "Error: MCP server venv not found. Run 'make install' in ${ORCHESTRATOR_DIR} first."
  exit 1
fi

mkdir -p "$TARGET_DIR"

# ── .mcp.json ──────────────────────────────────────
cat > "${TARGET_DIR}/.mcp.json" <<EOF
{
  "mcpServers": {
    "orchestrator": {
      "command": "${VENV_PYTHON}",
      "args": ["${SERVER_PY}"],
      "env": {
        "AGENT_NAME": "${AGENT_NAME}",
        "AGENT_ROLE": "${AGENT_ROLE}",
        "AGENT_PROJECT": "${PROJECT}",
        "ORCHESTRATOR_API_URL": "http://localhost:8000"
      }
    }
  }
}
EOF

# ── CLAUDE.md ──────────────────────────────────────
# Append orchestrator instructions if not already present
MARKER="<!-- orchestrator-connected -->"
if [ -f "${TARGET_DIR}/CLAUDE.md" ] && grep -q "$MARKER" "${TARGET_DIR}/CLAUDE.md"; then
  echo "CLAUDE.md already has orchestrator instructions — skipping."
else
  cat >> "${TARGET_DIR}/CLAUDE.md" <<EOF

${MARKER}
## Agent Orchestrator

You are agent **${AGENT_NAME}** (role: ${AGENT_ROLE}) in project **${PROJECT}**.
You are part of a multi-agent team. Other agents may be working on the same project simultaneously.

### Rules
- At the START of every conversation, call \`list_agents\` to see who else is online and \`get_my_tasks\` to check for pending work.
- Before starting significant work, call \`broadcast_status("description of what you're doing")\` so others know.
- When you need another agent to do something, use \`create_task(assignee_name, title, description)\` instead of trying to do it yourself.
- When you finish an assigned task, call \`update_task(task_id, "completed", "brief result")\`. If you fail, call \`update_task(task_id, "failed", "reason")\`.
- Use \`send_message(content, recipient_name)\` to communicate with a specific agent, or \`send_message(content)\` to broadcast to all.
- Check \`get_messages()\` periodically to see if anyone has sent you messages.
- **IMPORTANT**: While working on a task, call \`log_activity(content, task_id)\` frequently to report what you're doing. This is visible in the dashboard. Log at least: when you start, key decisions, files changed, and when you finish.
- Check \`get_my_tasks()\` before wrapping up to make sure nothing is pending.

### Available Tools
| Tool | Purpose |
|------|---------|
| \`list_agents()\` | See who's online |
| \`send_message(content, recipient_name?)\` | Send a message (broadcast or targeted) |
| \`get_messages(limit=20)\` | Read recent messages |
| \`create_task(assignee_name, title, description)\` | Assign work to another agent |
| \`get_my_tasks()\` | Check tasks assigned to you |
| \`update_task(task_id, status, result?)\` | Update task status: pending/in_progress/completed/failed |
| \`broadcast_status(status)\` | Announce what you're doing |
| \`log_activity(content, task_id?)\` | Log progress on current work (visible in dashboard task detail) |

### Bug Fix Loop
When you receive a task from QA reporting a bug (title starts with "Fix:"):
1. Read the bug description carefully
2. Fix the issue
3. Run tests to confirm the fix
4. \`update_task(task_id, "completed", "Fixed: [what you did]")\`
5. \`create_task("qa", "Re-validate: [original feature]", "Fix applied by ${AGENT_NAME}: [description]. Please re-test.")\`
6. \`send_message("Fix applied for [bug]. Sent back to QA for re-validation.", "architect")\`

### Decision Making
- If you have a technical doubt or need to choose between approaches, **do NOT block waiting for a response**. Instead:
  1. Take the decision that seems most reasonable
  2. \`log_activity("DECISION: [what you chose] — REASON: [why]", task_id)\`
  3. \`send_message("Decided to do [X] because [Y]. Let me know if you disagree.", "architect")\`
  4. Keep working immediately
EOF
fi

echo "Created ${TARGET_DIR}/.mcp.json"
echo "Updated ${TARGET_DIR}/CLAUDE.md"
echo ""
echo "  Project: ${PROJECT}"
echo "  Agent:   ${AGENT_NAME} (${AGENT_ROLE})"
echo ""
echo "Open Claude Code in ${TARGET_DIR} — it will auto-connect and know how to collaborate."
