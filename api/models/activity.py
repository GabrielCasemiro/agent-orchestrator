from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class ActivityCreate(BaseModel):
    agent_id: str
    project: str
    task_id: Optional[str] = None
    content: str


class Activity(ActivityCreate):
    id: str = Field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
