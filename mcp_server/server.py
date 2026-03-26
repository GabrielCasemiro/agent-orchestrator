"""MCP stdio server for the agent orchestrator.

Spawned by Claude Code via stdio; communicates with the FastAPI backend over HTTP.
"""

import os
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

import httpx
from mcp.server.fastmcp import FastMCP, Context

# ---------------------------------------------------------------------------
# Configuration from environment
# ---------------------------------------------------------------------------
ORCHESTRATOR_API_URL = os.environ.get("ORCHESTRATOR_API_URL", "http://localhost:8000")
AGENT_NAME = os.environ["AGENT_NAME"]
AGENT_ROLE = os.environ.get("AGENT_ROLE", "generalist")
AGENT_PROJECT = os.environ["AGENT_PROJECT"]

# Module-level HTTP client
http_client: httpx.AsyncClient | None = None


# ---------------------------------------------------------------------------
# Lifespan – register on startup, deregister on shutdown
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(server: FastMCP) -> AsyncIterator[dict]:
    global http_client
    http_client = httpx.AsyncClient(base_url=ORCHESTRATOR_API_URL, timeout=30.0)

    # Register this agent with the orchestrator API
    resp = await http_client.post(
        "/api/v1/agents",
        json={"name": AGENT_NAME, "role": AGENT_ROLE, "project": AGENT_PROJECT},
    )
    resp.raise_for_status()
    data = resp.json()
    agent_id = data["id"]

    yield {"agent_id": agent_id, "project": AGENT_PROJECT}

    # Deregister on shutdown
    try:
        await http_client.delete(f"/api/v1/agents/{agent_id}")
    except Exception:
        pass  # best-effort cleanup
    await http_client.aclose()
    http_client = None


# ---------------------------------------------------------------------------
# MCP server instance
# ---------------------------------------------------------------------------
mcp = FastMCP("agent-orchestrator", lifespan=lifespan)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _lifespan_ctx(ctx: Context) -> dict:
    """Convenience accessor for the lifespan context dict."""
    return ctx.request_context.lifespan_context


async def _resolve_agent_id(name: str, project: str) -> str:
    """Resolve an agent name to its ID within the given project."""
    resp = await http_client.get("/api/v1/agents", params={"project": project})
    resp.raise_for_status()
    agents = resp.json()
    for agent in agents:
        if agent["name"] == name:
            return agent["id"]
    raise ValueError(f"Agent '{name}' not found in project '{project}'")


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------
@mcp.tool()
async def send_message(
    content: str, ctx: Context, recipient_name: str | None = None
) -> str:
    """Send a message to the project channel, optionally directed at a specific agent."""
    try:
        lc = _lifespan_ctx(ctx)
        agent_id = lc["agent_id"]
        project = lc["project"]

        recipient_id = None
        if recipient_name:
            recipient_id = await _resolve_agent_id(recipient_name, project)

        payload: dict = {
            "sender_id": agent_id,
            "project": project,
            "content": content,
        }
        if recipient_id:
            payload["recipient_id"] = recipient_id

        resp = await http_client.post("/api/v1/messages", json=payload)
        resp.raise_for_status()

        target = f" to {recipient_name}" if recipient_name else ""
        return f"Message sent{target} successfully."
    except Exception as exc:
        return f"Error sending message: {exc}"


@mcp.tool()
async def get_messages(ctx: Context, limit: int = 20) -> str:
    """Retrieve recent messages from the project channel."""
    try:
        lc = _lifespan_ctx(ctx)
        project = lc["project"]

        resp = await http_client.get(
            "/api/v1/messages", params={"project": project, "limit": limit}
        )
        resp.raise_for_status()
        messages = resp.json()

        if not messages:
            return "No messages found."

        lines: list[str] = []
        for msg in messages:
            sender = msg.get("sender_name", msg.get("sender_id", "unknown"))
            recipient = msg.get("recipient_name") or msg.get("recipient_id")
            target = f" -> {recipient}" if recipient else ""
            lines.append(f"[{msg.get('created_at', '')}] {sender}{target}: {msg['content']}")

        return "\n".join(lines)
    except Exception as exc:
        return f"Error retrieving messages: {exc}"


@mcp.tool()
async def create_task(
    assignee_name: str, title: str, ctx: Context, description: str = ""
) -> str:
    """Create a task and assign it to a specific agent by name."""
    try:
        lc = _lifespan_ctx(ctx)
        agent_id = lc["agent_id"]
        project = lc["project"]

        assignee_id = await _resolve_agent_id(assignee_name, project)

        payload = {
            "project": project,
            "creator_id": agent_id,
            "assignee_id": assignee_id,
            "title": title,
            "description": description,
        }

        resp = await http_client.post("/api/v1/tasks", json=payload)
        resp.raise_for_status()
        task = resp.json()

        return f"Task created: {task['id']} — '{title}' assigned to {assignee_name}."
    except Exception as exc:
        return f"Error creating task: {exc}"


@mcp.tool()
async def get_my_tasks(ctx: Context) -> str:
    """Retrieve all tasks assigned to this agent."""
    try:
        lc = _lifespan_ctx(ctx)
        agent_id = lc["agent_id"]

        resp = await http_client.get(f"/api/v1/tasks/agent/{agent_id}")
        resp.raise_for_status()
        tasks = resp.json()

        if not tasks:
            return "No tasks assigned."

        lines: list[str] = []
        for t in tasks:
            lines.append(
                f"- [{t.get('status', 'unknown')}] {t['id']}: {t['title']}"
                + (f" — {t['description']}" if t.get("description") else "")
            )

        return "\n".join(lines)
    except Exception as exc:
        return f"Error retrieving tasks: {exc}"


@mcp.tool()
async def update_task(task_id: str, status: str, ctx: Context, result: str = "") -> str:
    """Update the status (and optionally the result) of a task."""
    try:
        payload: dict = {"status": status}
        if result:
            payload["result"] = result

        resp = await http_client.patch(f"/api/v1/tasks/{task_id}", json=payload)
        resp.raise_for_status()

        return f"Task {task_id} updated to '{status}'."
    except Exception as exc:
        return f"Error updating task: {exc}"


@mcp.tool()
async def list_agents(ctx: Context) -> str:
    """List all agents currently registered in the project."""
    try:
        lc = _lifespan_ctx(ctx)
        project = lc["project"]

        resp = await http_client.get("/api/v1/agents", params={"project": project})
        resp.raise_for_status()
        agents = resp.json()

        if not agents:
            return "No agents registered."

        lines: list[str] = []
        for a in agents:
            status_icon = "🟢" if a.get("status") == "online" else "⚫"
            lines.append(f"- {status_icon} {a['name']} ({a.get('status', 'unknown')}, role: {a.get('role', 'unknown')}, id: {a['id']})")

        return "\n".join(lines)
    except Exception as exc:
        return f"Error listing agents: {exc}"


@mcp.tool()
async def broadcast_status(status: str, ctx: Context) -> str:
    """Broadcast a status update to the entire project channel."""
    try:
        lc = _lifespan_ctx(ctx)
        agent_id = lc["agent_id"]
        project = lc["project"]

        payload = {
            "sender_id": agent_id,
            "project": project,
            "content": f"[STATUS] {status}",
        }

        resp = await http_client.post("/api/v1/messages", json=payload)
        resp.raise_for_status()

        return f"Status broadcast: {status}"
    except Exception as exc:
        return f"Error broadcasting status: {exc}"


@mcp.tool()
async def log_activity(content: str, ctx: Context, task_id: str | None = None) -> str:
    """Log what you're doing right now. Use this to report progress during task execution. If working on a task, include the task_id."""
    try:
        lc = _lifespan_ctx(ctx)
        payload: dict = {
            "agent_id": lc["agent_id"],
            "project": lc["project"],
            "content": content,
        }
        if task_id:
            payload["task_id"] = task_id

        resp = await http_client.post("/api/v1/activities", json=payload)
        resp.raise_for_status()

        return f"Activity logged."
    except Exception as exc:
        return f"Error logging activity: {exc}"


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    mcp.run()
