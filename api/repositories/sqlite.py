"""SQLite-backed repository implementations.

Drop-in replacement for the in-memory repos. Data persists across API restarts.
"""

import sqlite3
from datetime import datetime, timezone
from typing import Optional

from models.activity import Activity, ActivityCreate
from models.agent import Agent, AgentCreate
from models.message import Message, MessageCreate
from models.task import Task, TaskCreate, TaskUpdate
from repositories.base import (
    ActivityRepository,
    AgentRepository,
    MessageRepository,
    TaskRepository,
)

from uuid import uuid4


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _parse_dt(s: str) -> datetime:
    return datetime.fromisoformat(s)


class SQLiteDB:
    """Shared SQLite connection with schema init."""

    def __init__(self, db_path: str = "orchestrator.db") -> None:
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL")
        self._init_schema()

    def _init_schema(self) -> None:
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS agents (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                role TEXT NOT NULL,
                project TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'online',
                last_heartbeat TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS messages (
                id TEXT PRIMARY KEY,
                sender_id TEXT NOT NULL,
                project TEXT NOT NULL,
                content TEXT NOT NULL,
                recipient_id TEXT,
                timestamp TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                project TEXT NOT NULL,
                creator_id TEXT NOT NULL,
                assignee_id TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT NOT NULL DEFAULT '',
                status TEXT NOT NULL DEFAULT 'pending',
                result TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS activities (
                id TEXT PRIMARY KEY,
                agent_id TEXT NOT NULL,
                project TEXT NOT NULL,
                task_id TEXT,
                content TEXT NOT NULL,
                timestamp TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_agents_project ON agents(project);
            CREATE INDEX IF NOT EXISTS idx_messages_project ON messages(project);
            CREATE INDEX IF NOT EXISTS idx_tasks_project ON tasks(project);
            CREATE INDEX IF NOT EXISTS idx_tasks_assignee ON tasks(assignee_id);
            CREATE INDEX IF NOT EXISTS idx_activities_project ON activities(project);
            CREATE INDEX IF NOT EXISTS idx_activities_task ON activities(task_id);
        """)
        self.conn.commit()


class SQLiteAgentRepository(AgentRepository):
    def __init__(self, db: SQLiteDB) -> None:
        self.conn = db.conn

    def create(self, agent: AgentCreate) -> Agent:
        now = _now()
        agent_id = str(uuid4())
        self.conn.execute(
            "INSERT INTO agents (id, name, role, project, status, last_heartbeat) VALUES (?, ?, ?, ?, 'online', ?)",
            (agent_id, agent.name, agent.role, agent.project, now),
        )
        self.conn.commit()
        return Agent(
            id=agent_id,
            name=agent.name,
            role=agent.role,
            project=agent.project,
            status="online",
            last_heartbeat=_parse_dt(now),
        )

    def get(self, id: str) -> Optional[Agent]:
        row = self.conn.execute("SELECT * FROM agents WHERE id = ?", (id,)).fetchone()
        if row is None:
            return None
        return self._row_to_agent(row)

    def find_by_name_and_project(self, name: str, project: str) -> Optional[Agent]:
        row = self.conn.execute(
            "SELECT * FROM agents WHERE name = ? AND project = ?", (name, project)
        ).fetchone()
        if row is None:
            return None
        return self._row_to_agent(row)

    def list_by_project(self, project: str) -> list[Agent]:
        rows = self.conn.execute(
            "SELECT * FROM agents WHERE project = ? ORDER BY name", (project,)
        ).fetchall()
        return [self._row_to_agent(r) for r in rows]

    def delete(self, id: str) -> bool:
        cur = self.conn.execute("DELETE FROM agents WHERE id = ?", (id,))
        self.conn.commit()
        return cur.rowcount > 0

    def set_offline(self, id: str) -> Optional[Agent]:
        self.conn.execute("UPDATE agents SET status = 'offline' WHERE id = ?", (id,))
        self.conn.commit()
        return self.get(id)

    def heartbeat(self, id: str) -> Optional[Agent]:
        now = _now()
        self.conn.execute(
            "UPDATE agents SET last_heartbeat = ?, status = 'online' WHERE id = ?",
            (now, id),
        )
        self.conn.commit()
        return self.get(id)

    @staticmethod
    def _row_to_agent(row: sqlite3.Row) -> Agent:
        return Agent(
            id=row["id"],
            name=row["name"],
            role=row["role"],
            project=row["project"],
            status=row["status"],
            last_heartbeat=_parse_dt(row["last_heartbeat"]),
        )


class SQLiteMessageRepository(MessageRepository):
    def __init__(self, db: SQLiteDB) -> None:
        self.conn = db.conn

    def create(self, message: MessageCreate) -> Message:
        now = _now()
        msg_id = str(uuid4())
        self.conn.execute(
            "INSERT INTO messages (id, sender_id, project, content, recipient_id, timestamp) VALUES (?, ?, ?, ?, ?, ?)",
            (msg_id, message.sender_id, message.project, message.content, message.recipient_id, now),
        )
        self.conn.commit()
        return Message(
            id=msg_id,
            sender_id=message.sender_id,
            project=message.project,
            content=message.content,
            recipient_id=message.recipient_id,
            timestamp=_parse_dt(now),
        )

    def list_by_project(self, project: str, limit: int = 50) -> list[Message]:
        rows = self.conn.execute(
            "SELECT * FROM messages WHERE project = ? ORDER BY timestamp DESC LIMIT ?",
            (project, limit),
        ).fetchall()
        return [self._row_to_message(r) for r in rows]

    @staticmethod
    def _row_to_message(row: sqlite3.Row) -> Message:
        return Message(
            id=row["id"],
            sender_id=row["sender_id"],
            project=row["project"],
            content=row["content"],
            recipient_id=row["recipient_id"],
            timestamp=_parse_dt(row["timestamp"]),
        )


class SQLiteTaskRepository(TaskRepository):
    def __init__(self, db: SQLiteDB) -> None:
        self.conn = db.conn

    def create(self, task: TaskCreate) -> Task:
        now = _now()
        task_id = str(uuid4())
        self.conn.execute(
            "INSERT INTO tasks (id, project, creator_id, assignee_id, title, description, status, result, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, 'pending', '', ?, ?)",
            (task_id, task.project, task.creator_id, task.assignee_id, task.title, task.description, now, now),
        )
        self.conn.commit()
        return Task(
            id=task_id,
            project=task.project,
            creator_id=task.creator_id,
            assignee_id=task.assignee_id,
            title=task.title,
            description=task.description,
            status="pending",
            result="",
            created_at=_parse_dt(now),
            updated_at=_parse_dt(now),
        )

    def get(self, id: str) -> Optional[Task]:
        row = self.conn.execute("SELECT * FROM tasks WHERE id = ?", (id,)).fetchone()
        if row is None:
            return None
        return self._row_to_task(row)

    def list_by_project(self, project: str) -> list[Task]:
        rows = self.conn.execute(
            "SELECT * FROM tasks WHERE project = ? ORDER BY created_at", (project,)
        ).fetchall()
        return [self._row_to_task(r) for r in rows]

    def list_by_assignee(self, assignee_id: str) -> list[Task]:
        rows = self.conn.execute(
            "SELECT * FROM tasks WHERE assignee_id = ? ORDER BY created_at", (assignee_id,)
        ).fetchall()
        return [self._row_to_task(r) for r in rows]

    def update(self, id: str, update: TaskUpdate) -> Optional[Task]:
        task = self.get(id)
        if task is None:
            return None
        now = _now()
        updates = update.model_dump(exclude_none=True)
        if not updates:
            return task
        set_clause = ", ".join(f"{k} = ?" for k in updates)
        values = list(updates.values()) + [now, id]
        self.conn.execute(
            f"UPDATE tasks SET {set_clause}, updated_at = ? WHERE id = ?",
            values,
        )
        self.conn.commit()
        return self.get(id)

    @staticmethod
    def _row_to_task(row: sqlite3.Row) -> Task:
        return Task(
            id=row["id"],
            project=row["project"],
            creator_id=row["creator_id"],
            assignee_id=row["assignee_id"],
            title=row["title"],
            description=row["description"],
            status=row["status"],
            result=row["result"],
            created_at=_parse_dt(row["created_at"]),
            updated_at=_parse_dt(row["updated_at"]),
        )


class SQLiteActivityRepository(ActivityRepository):
    def __init__(self, db: SQLiteDB) -> None:
        self.conn = db.conn

    def create(self, activity: ActivityCreate) -> Activity:
        now = _now()
        act_id = str(uuid4())
        self.conn.execute(
            "INSERT INTO activities (id, agent_id, project, task_id, content, timestamp) VALUES (?, ?, ?, ?, ?, ?)",
            (act_id, activity.agent_id, activity.project, activity.task_id, activity.content, now),
        )
        self.conn.commit()
        return Activity(
            id=act_id,
            agent_id=activity.agent_id,
            project=activity.project,
            task_id=activity.task_id,
            content=activity.content,
            timestamp=_parse_dt(now),
        )

    def list_by_project(self, project: str, limit: int = 100) -> list[Activity]:
        rows = self.conn.execute(
            "SELECT * FROM activities WHERE project = ? ORDER BY timestamp LIMIT ?",
            (project, limit),
        ).fetchall()
        return [self._row_to_activity(r) for r in rows]

    def list_by_task(self, task_id: str) -> list[Activity]:
        rows = self.conn.execute(
            "SELECT * FROM activities WHERE task_id = ? ORDER BY timestamp",
            (task_id,),
        ).fetchall()
        return [self._row_to_activity(r) for r in rows]

    @staticmethod
    def _row_to_activity(row: sqlite3.Row) -> Activity:
        return Activity(
            id=row["id"],
            agent_id=row["agent_id"],
            project=row["project"],
            task_id=row["task_id"],
            content=row["content"],
            timestamp=_parse_dt(row["timestamp"]),
        )
