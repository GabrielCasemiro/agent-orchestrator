#!/bin/bash
# Agent runner — keeps a Claude Code agent alive and reactive.
# Polls the orchestrator API for new tasks/messages and re-invokes claude.
#
# Usage: agent-runner.sh <agent-name> <project-dir>
# Example: agent-runner.sh backend ~/projects/my-api
#
# Environment variables:
#   ORCHESTRATOR_API_URL  API base URL (default: http://localhost:8000)
#   POLL_INTERVAL         Seconds between polls (default: 10)

set -e

AGENT_NAME="${1:?Usage: agent-runner.sh <agent-name> <project-dir>}"
PROJECT_DIR="${2:?Usage: agent-runner.sh <agent-name> <project-dir>}"
API_URL="${ORCHESTRATOR_API_URL:-http://localhost:8000}"
POLL_INTERVAL="${POLL_INTERVAL:-10}"

cd "$PROJECT_DIR"

# Get project name from .mcp.json
AGENT_PROJECT=$(python3 -c "import json; print(json.load(open('.mcp.json'))['mcpServers']['orchestrator']['env']['AGENT_PROJECT'])")

AGENT_ID=""
LAST_MSG_COUNT=0
LAST_TASK_IDS=""
IDLE_SINCE=$(date +%s)

log() {
  echo "[$(date +%H:%M:%S)] [$AGENT_NAME] $1"
}

get_agent_id() {
  local agents
  agents=$(curl -sf "${API_URL}/api/v1/agents?project=${AGENT_PROJECT}" 2>/dev/null || echo "[]")
  AGENT_ID=$(echo "$agents" | python3 -c "
import sys, json
agents = json.load(sys.stdin)
for a in agents:
    if a['name'] == '${AGENT_NAME}':
        print(a['id'])
        break
" 2>/dev/null || echo "")
}

get_pending_tasks() {
  if [ -z "$AGENT_ID" ]; then echo ""; return; fi
  curl -sf "${API_URL}/api/v1/tasks/agent/${AGENT_ID}" 2>/dev/null | python3 -c "
import sys, json
tasks = json.load(sys.stdin)
pending = [t for t in tasks if t['status'] in ('pending', 'in_progress')]
for t in pending:
    print(f\"{t['id']}|{t['title']}|{t['status']}\")
" 2>/dev/null || echo ""
}

get_new_messages() {
  local msgs
  msgs=$(curl -sf "${API_URL}/api/v1/messages?project=${AGENT_PROJECT}&limit=10" 2>/dev/null || echo "[]")
  local count
  count=$(echo "$msgs" | python3 -c "import sys,json; print(len(json.load(sys.stdin)))" 2>/dev/null || echo "0")

  if [ "$count" -gt "$LAST_MSG_COUNT" ] && [ "$LAST_MSG_COUNT" -gt 0 ]; then
    echo "$msgs" | python3 -c "
import sys, json
msgs = json.load(sys.stdin)
recent = msgs[${LAST_MSG_COUNT}:]
for m in recent:
    rid = m.get('recipient_id') or ''
    sid = m.get('sender_id', '')
    if sid != '${AGENT_ID}':
        print(f\"{m['content']}\")
" 2>/dev/null || echo ""
  fi
  LAST_MSG_COUNT=$count
}

run_claude() {
  local prompt="$1"
  log "Invoking claude..."
  claude --dangerously-skip-permissions -p "$prompt" 2>&1 | while IFS= read -r line; do
    echo "  $line"
  done
  log "Claude finished. Resuming watch..."
  IDLE_SINCE=$(date +%s)
}

# ── Startup ────────────────────────────────────────
log "Starting agent runner for '${AGENT_NAME}' in project '${AGENT_PROJECT}'"
log "Polling every ${POLL_INTERVAL}s at ${API_URL}"

# Initial run — connect and check in
run_claude "Read your CLAUDE.md. Call list_agents() and get_my_tasks(). If you have pending tasks, start working on them. Otherwise, call broadcast_status('available and waiting for tasks'). When you finish each task, call update_task with the result."

# ── Main loop ──────────────────────────────────────
while true; do
  sleep "$POLL_INTERVAL"

  # Refresh agent ID (in case of re-registration)
  get_agent_id

  if [ -z "$AGENT_ID" ]; then
    log "Not registered yet, retrying..."
    continue
  fi

  # Check for new tasks
  TASKS=$(get_pending_tasks)
  if [ -n "$TASKS" ]; then
    TASK_IDS=$(echo "$TASKS" | cut -d'|' -f1 | sort)
    if [ "$TASK_IDS" != "$LAST_TASK_IDS" ]; then
      LAST_TASK_IDS="$TASK_IDS"
      TASK_SUMMARY=$(echo "$TASKS" | head -3 | sed 's/|/ — /g' | tr '\n' '; ')
      log "New/updated tasks detected: $TASK_SUMMARY"
      run_claude "You have new tasks. Call get_my_tasks() to see what needs to be done. Work on each pending task. Use update_task() when complete. If you need another agent, use send_message() or create_task(). Broadcast your status as you go."
    fi
  fi

  # Check for new messages
  NEW_MSGS=$(get_new_messages)
  if [ -n "$NEW_MSGS" ]; then
    MSG_PREVIEW=$(echo "$NEW_MSGS" | head -3 | tr '\n' ' | ')
    log "New messages: $MSG_PREVIEW"
    run_claude "You have new messages. Call get_messages() to read them. If a message requests an action, execute it. If someone created a task for you, call get_my_tasks() and work on it. Reply using send_message()."
  fi

  # Periodic check-in every 5 minutes of idle
  NOW=$(date +%s)
  IDLE_TIME=$((NOW - IDLE_SINCE))
  if [ "$IDLE_TIME" -gt 300 ]; then
    log "Idle for 5min, checking in..."
    run_claude "Check in: call get_my_tasks() and get_messages(limit=5). If anything is pending, work on it. Otherwise, just broadcast_status('idle, waiting for tasks')."
    IDLE_SINCE=$(date +%s)
  fi
done
