from abc import ABC, abstractmethod
from typing import Optional

from models.activity import Activity, ActivityCreate
from models.agent import Agent, AgentCreate
from models.message import Message, MessageCreate
from models.task import Task, TaskCreate, TaskUpdate


class AgentRepository(ABC):
    @abstractmethod
    def create(self, agent: AgentCreate) -> Agent:
        ...

    @abstractmethod
    def get(self, id: str) -> Optional[Agent]:
        ...

    @abstractmethod
    def list_by_project(self, project: str) -> list[Agent]:
        ...

    @abstractmethod
    def find_by_name_and_project(self, name: str, project: str) -> Optional[Agent]:
        ...

    @abstractmethod
    def delete(self, id: str) -> bool:
        ...

    @abstractmethod
    def set_offline(self, id: str) -> Optional[Agent]:
        ...

    @abstractmethod
    def heartbeat(self, id: str) -> Optional[Agent]:
        ...


class MessageRepository(ABC):
    @abstractmethod
    def create(self, message: MessageCreate) -> Message:
        ...

    @abstractmethod
    def list_by_project(self, project: str, limit: int = 50) -> list[Message]:
        ...


class TaskRepository(ABC):
    @abstractmethod
    def create(self, task: TaskCreate) -> Task:
        ...

    @abstractmethod
    def get(self, id: str) -> Optional[Task]:
        ...

    @abstractmethod
    def list_by_project(self, project: str) -> list[Task]:
        ...

    @abstractmethod
    def list_by_assignee(self, assignee_id: str) -> list[Task]:
        ...

    @abstractmethod
    def update(self, id: str, update: TaskUpdate) -> Optional[Task]:
        ...


class ActivityRepository(ABC):
    @abstractmethod
    def create(self, activity: ActivityCreate) -> Activity:
        ...

    @abstractmethod
    def list_by_project(self, project: str, limit: int = 100) -> list[Activity]:
        ...

    @abstractmethod
    def list_by_task(self, task_id: str) -> list[Activity]:
        ...
