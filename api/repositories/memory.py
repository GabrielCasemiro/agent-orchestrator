from datetime import datetime, timezone
from typing import Optional

from models.activity import Activity, ActivityCreate
from models.agent import Agent, AgentCreate
from models.message import Message, MessageCreate
from models.task import Task, TaskCreate, TaskUpdate
from repositories.base import ActivityRepository, AgentRepository, MessageRepository, TaskRepository


class InMemoryAgentRepository(AgentRepository):
    def __init__(self) -> None:
        self._data: dict[str, Agent] = {}

    def create(self, agent: AgentCreate) -> Agent:
        new_agent = Agent(**agent.model_dump())
        self._data[new_agent.id] = new_agent
        return new_agent

    def get(self, id: str) -> Optional[Agent]:
        return self._data.get(id)

    def find_by_name_and_project(self, name: str, project: str) -> Optional[Agent]:
        for a in self._data.values():
            if a.name == name and a.project == project:
                return a
        return None

    def list_by_project(self, project: str) -> list[Agent]:
        return [a for a in self._data.values() if a.project == project]

    def delete(self, id: str) -> bool:
        if id in self._data:
            del self._data[id]
            return True
        return False

    def set_offline(self, id: str) -> Optional[Agent]:
        agent = self._data.get(id)
        if agent is None:
            return None
        agent.status = "offline"
        return agent

    def heartbeat(self, id: str) -> Optional[Agent]:
        agent = self._data.get(id)
        if agent is None:
            return None
        agent.last_heartbeat = datetime.now(timezone.utc)
        agent.status = "online"
        return agent


class InMemoryMessageRepository(MessageRepository):
    def __init__(self) -> None:
        self._data: dict[str, Message] = {}

    def create(self, message: MessageCreate) -> Message:
        new_message = Message(**message.model_dump())
        self._data[new_message.id] = new_message
        return new_message

    def list_by_project(self, project: str, limit: int = 50) -> list[Message]:
        messages = [m for m in self._data.values() if m.project == project]
        messages.sort(key=lambda m: m.timestamp, reverse=True)
        return messages[:limit]


class InMemoryTaskRepository(TaskRepository):
    def __init__(self) -> None:
        self._data: dict[str, Task] = {}

    def create(self, task: TaskCreate) -> Task:
        new_task = Task(**task.model_dump())
        self._data[new_task.id] = new_task
        return new_task

    def get(self, id: str) -> Optional[Task]:
        return self._data.get(id)

    def list_by_project(self, project: str) -> list[Task]:
        return [t for t in self._data.values() if t.project == project]

    def list_by_assignee(self, assignee_id: str) -> list[Task]:
        return [t for t in self._data.values() if t.assignee_id == assignee_id]

    def update(self, id: str, update: TaskUpdate) -> Optional[Task]:
        task = self._data.get(id)
        if task is None:
            return None
        update_data = update.model_dump(exclude_none=True)
        for key, value in update_data.items():
            setattr(task, key, value)
        task.updated_at = datetime.now(timezone.utc)
        return task


class InMemoryActivityRepository(ActivityRepository):
    def __init__(self) -> None:
        self._data: dict[str, Activity] = {}

    def create(self, activity: ActivityCreate) -> Activity:
        new_activity = Activity(**activity.model_dump())
        self._data[new_activity.id] = new_activity
        return new_activity

    def list_by_project(self, project: str, limit: int = 100) -> list[Activity]:
        activities = [a for a in self._data.values() if a.project == project]
        activities.sort(key=lambda a: a.timestamp)
        return activities[-limit:]

    def list_by_task(self, task_id: str) -> list[Activity]:
        activities = [a for a in self._data.values() if a.task_id == task_id]
        activities.sort(key=lambda a: a.timestamp)
        return activities
