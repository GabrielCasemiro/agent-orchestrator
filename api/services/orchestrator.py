from datetime import datetime, timezone, timedelta
from typing import Any, Optional

from models.activity import Activity, ActivityCreate
from models.agent import Agent, AgentCreate
from models.message import Message, MessageCreate
from models.task import Task, TaskCreate, TaskUpdate
from repositories.base import ActivityRepository, AgentRepository, MessageRepository, TaskRepository
from ws.manager import ConnectionManager


def _serialize(data: dict[str, Any]) -> dict[str, Any]:
    """Convert datetime values to ISO format strings for JSON serialization."""
    result = {}
    for key, value in data.items():
        if isinstance(value, datetime):
            result[key] = value.isoformat()
        else:
            result[key] = value
    return result


class OrchestratorService:
    def __init__(
        self,
        agent_repo: AgentRepository,
        message_repo: MessageRepository,
        task_repo: TaskRepository,
        activity_repo: ActivityRepository,
        ws_manager: ConnectionManager,
    ) -> None:
        self.agent_repo = agent_repo
        self.message_repo = message_repo
        self.task_repo = task_repo
        self.activity_repo = activity_repo
        self.ws_manager = ws_manager

    async def register_agent(self, data: AgentCreate) -> Agent:
        existing = self.agent_repo.find_by_name_and_project(data.name, data.project)
        if existing:
            existing.status = "online"
            existing.role = data.role
            existing.last_heartbeat = datetime.now(timezone.utc)
            await self.ws_manager.broadcast(
                existing.project,
                {"type": "agent_joined", "agent": _serialize(existing.model_dump())},
            )
            return existing
        agent = self.agent_repo.create(data)
        await self.ws_manager.broadcast(
            agent.project,
            {"type": "agent_joined", "agent": _serialize(agent.model_dump())},
        )
        return agent

    async def deregister_agent(self, agent_id: str) -> bool:
        agent = self.agent_repo.set_offline(agent_id)
        if agent is None:
            return False
        await self.ws_manager.broadcast(
            agent.project,
            {"type": "agent_left", "agent_id": agent_id},
        )
        return True

    def heartbeat(self, agent_id: str) -> Optional[Agent]:
        return self.agent_repo.heartbeat(agent_id)

    def list_agents(self, project: str) -> list[Agent]:
        agents = self.agent_repo.list_by_project(project)
        now = datetime.now(timezone.utc)
        for agent in agents:
            if agent.last_heartbeat and (now - agent.last_heartbeat) < timedelta(minutes=5):
                agent.status = "online"
            else:
                agent.status = "offline"
        return agents

    async def send_message(self, data: MessageCreate) -> Message:
        msg = self.message_repo.create(data)
        await self.ws_manager.broadcast(
            msg.project,
            {"type": "new_message", "message": _serialize(msg.model_dump())},
        )
        return msg

    def get_messages(self, project: str, limit: int = 50) -> list[Message]:
        return self.message_repo.list_by_project(project, limit)

    async def create_task(self, data: TaskCreate) -> Task:
        task = self.task_repo.create(data)
        await self.ws_manager.broadcast(
            task.project,
            {"type": "new_task", "task": _serialize(task.model_dump())},
        )
        return task

    def list_tasks(self, project: str) -> list[Task]:
        return self.task_repo.list_by_project(project)

    def get_agent_tasks(self, assignee_id: str) -> list[Task]:
        return self.task_repo.list_by_assignee(assignee_id)

    async def update_task(self, task_id: str, update: TaskUpdate) -> Optional[Task]:
        task = self.task_repo.update(task_id, update)
        if task is not None:
            await self.ws_manager.broadcast(
                task.project,
                {"type": "task_updated", "task": _serialize(task.model_dump())},
            )
        return task

    # ── Activity log ──────────────────────────────────

    async def log_activity(self, data: ActivityCreate) -> Activity:
        activity = self.activity_repo.create(data)
        await self.ws_manager.broadcast(
            data.project,
            {"type": "new_activity", "activity": _serialize(activity.model_dump())},
        )
        return activity

    def get_activities(self, project: str, limit: int = 100) -> list[Activity]:
        return self.activity_repo.list_by_project(project, limit)

    def get_task_activities(self, task_id: str) -> list[Activity]:
        return self.activity_repo.list_by_task(task_id)

    # ── Export ────────────────────────────────────────

    def export_project(self, project: str) -> str:
        agents = self.list_agents(project)
        messages = self.message_repo.list_by_project(project, limit=500)
        tasks = self.task_repo.list_by_project(project)
        activities = self.activity_repo.list_by_project(project, limit=500)

        agent_map = {a.id: a.name for a in agents}

        def name(agent_id: str) -> str:
            return agent_map.get(agent_id, agent_id[:8])

        lines: list[str] = []
        lines.append(f"# Project: {project}")
        lines.append("")

        # Agents
        lines.append("## Agents")
        for a in agents:
            lines.append(f"- **{a.name}** ({a.role}) — {a.status}")
        lines.append("")

        # Tasks
        lines.append("## Tasks")
        for t in sorted(tasks, key=lambda t: t.created_at):
            lines.append(f"### [{t.status.upper()}] {t.title}")
            lines.append(f"- ID: `{t.id}`")
            lines.append(f"- Assigned to: **{name(t.assignee_id)}** by **{name(t.creator_id)}**")
            lines.append(f"- Created: {t.created_at.strftime('%H:%M:%S')}")
            if t.description:
                lines.append(f"- Description: {t.description}")
            if t.result:
                lines.append(f"- Result: {t.result}")
            # Task activities
            task_acts = [a for a in activities if a.task_id == t.id]
            if task_acts:
                lines.append("- Activity log:")
                for act in task_acts:
                    lines.append(f"  - `{act.timestamp.strftime('%H:%M:%S')}` **{name(act.agent_id)}**: {act.content}")
            lines.append("")

        # Messages
        lines.append("## Messages")
        sorted_msgs = sorted(messages, key=lambda m: m.timestamp)
        for m in sorted_msgs:
            recipient = f" → **{name(m.recipient_id)}**" if m.recipient_id else ""
            lines.append(f"- `{m.timestamp.strftime('%H:%M:%S')}` **{name(m.sender_id)}**{recipient}: {m.content}")
        lines.append("")

        return "\n".join(lines)
