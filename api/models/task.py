from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class TaskCreate(BaseModel):
    project: str
    creator_id: str
    assignee_id: str
    title: str
    description: str = ""


class TaskUpdate(BaseModel):
    status: Optional[str] = None
    result: Optional[str] = None


class Task(TaskCreate):
    id: str = Field(default_factory=lambda: str(uuid4()))
    status: str = "pending"
    result: str = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
