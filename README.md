# Agent Orchestrator

Multi-agent coordination system for [Claude Code](https://docs.anthropic.com/en/docs/claude-code). Run multiple Claude Code instances that communicate, delegate tasks, and observe each other's work — with a real-time dashboard.

## How it works

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│ Claude Code  │     │ Claude Code  │     │ Claude Code  │
│  (backend)   │     │  (frontend)  │     │    (qa)      │
└──────┬───────┘     └──────┬───────┘     └──────┬───────┘
       │ MCP stdio          │ MCP stdio          │ MCP stdio
       ▼                    ▼                    ▼
┌─────────────────────────────────────────────────────────┐
│                    MCP Server                            │
│         (translates tools → HTTP calls)                  │
└──────────────────────────┬──────────────────────────────┘
                           │ HTTP
                           ▼
┌─────────────────────────────────────────────────────────┐
│                    FastAPI Backend                        │
│         (state management, WebSocket events)             │
│                   SQLite persistence                     │
└──────────────────────────┬──────────────────────────────┘
                           │ WebSocket
                           ▼
┌─────────────────────────────────────────────────────────┐
│                  Next.js Dashboard                        │
│        (real-time agents, messages, task board)           │
└─────────────────────────────────────────────────────────┘
```

Each Claude Code instance gets 8 MCP tools:

| Tool | Purpose |
|------|---------|
| `list_agents()` | See who's online in the project |
| `send_message(content, recipient_name?)` | Send a message (broadcast or targeted) |
| `get_messages(limit)` | Read recent project messages |
| `create_task(assignee_name, title, description)` | Assign work to another agent |
| `get_my_tasks()` | Check tasks assigned to me |
| `update_task(task_id, status, result?)` | Update task status |
| `broadcast_status(status)` | Announce what you're doing |
| `log_activity(content, task_id?)` | Log progress (visible in dashboard) |

## Quick Start

### 1. Install

```bash
git clone https://github.com/YOUR_USER/orchestrator.git
cd orchestrator
make install
```

Requires: Python 3.12+, Node.js 18+, [uv](https://docs.astral.sh/uv/)

### 2. Start the orchestrator

```bash
make dev
```

This starts:
- **API** on `http://localhost:8000` (FastAPI + SQLite)
- **Dashboard** on `http://localhost:3000` (Next.js)

### 3. Connect your project

From the orchestrator directory, run:

```bash
./connect.sh my-project backend backend ~/code/my-api
./connect.sh my-project frontend frontend ~/code/my-frontend
```

This generates two files in each target directory:
- `.mcp.json` — gives Claude Code the orchestrator tools
- `CLAUDE.md` — tells the agent who it is and how to collaborate

### 4. Launch Claude Code

Open Claude Code in each connected directory. Each instance automatically registers as an agent and can communicate with the others.

```bash
# Terminal 1
cd ~/code/my-api && claude

# Terminal 2
cd ~/code/my-frontend && claude
```

### 5. Open the dashboard

Go to `http://localhost:3000` and type your project name (e.g., `my-project`) in the project field.

## Autonomous agents with agent-runner

For fully autonomous agents that react to tasks and messages without manual intervention:

```bash
./agent-runner.sh backend ~/code/my-api
./agent-runner.sh frontend ~/code/my-frontend
```

The runner:
- Starts Claude Code with `--dangerously-skip-permissions`
- Polls the API every 10s for new tasks/messages
- Re-invokes Claude Code when something arrives
- Checks in every 5 minutes when idle

Environment variables:
- `ORCHESTRATOR_API_URL` — API base URL (default: `http://localhost:8000`)
- `POLL_INTERVAL` — seconds between polls (default: `10`)

## Recommended team setup

| Agent | Role | Description |
|-------|------|-------------|
| **architect** | generalist | Interactive — you talk to this one. Plans features, creates tasks, reviews work |
| **backend** | backend | Autonomous — works on API/server code |
| **frontend** | frontend | Autonomous — works on client-side code |
| **qa** | generalist | Autonomous — tests what others built, reports bugs |
| **devops** | devops | Autonomous — deploys, monitors, rolls back |

The architect should be **interactive** (plain `claude`), while the rest run via `agent-runner.sh`.

## Task lifecycle

```
architect creates tasks
       ↓
agents work autonomously
       ↓
architect creates QA task
       ↓
QA validates ──→ PASSED → creates deploy task for devops
       │
       └──→ FAILED → creates "Fix:" task for responsible agent
                          ↓
                   agent fixes + creates "Re-validate:" task for QA
                          ↓
                   QA re-tests (loop until passed)
                          ↓
                       PASSED → deploy
```

## Dashboard features

- **Agent list** — online/offline status with role badges
- **Message feed** — real-time color-coded messages between agents
- **Task board** — kanban view (Queued → Running → Done / Failed)
- **Task detail** — click any task to see its activity log
- **Export** — copies full project history as markdown to clipboard

## Project structure

```
orchestrator/
├── api/                    # FastAPI backend
│   ├── models/             # Pydantic models
│   ├── repositories/       # Storage layer (memory + SQLite)
│   ├── services/           # Business logic
│   ├── routers/            # REST endpoints
│   └── ws/                 # WebSocket manager
├── mcp_server/             # MCP stdio server
├── dashboard/              # Next.js real-time dashboard
├── connect.sh              # Connect a project directory
├── agent-runner.sh         # Autonomous agent daemon
└── Makefile
```

## Configuration

### Storage

Default: SQLite (`orchestrator.db` in the `api/` directory). Data persists across restarts.

```bash
# Use in-memory storage (data lost on restart)
STORAGE=memory make api

# Custom database path
DB_PATH=/path/to/my.db make api
```

### API URL

If running the API on a different host/port:

```bash
ORCHESTRATOR_API_URL=http://my-server:8000 ./agent-runner.sh backend ~/code/my-api
```

The same variable is available in `.mcp.json` for each connected agent.

## License

MIT
