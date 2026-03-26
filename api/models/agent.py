from datetime import datetime, timezone
from uuid import uuid4

from pydantic import BaseModel, Field


class AgentCreate(BaseModel):
    name: str
    role: str
    project: str


class Agent(AgentCreate):
    id: str = Field(default_factory=lambda: str(uuid4()))
    status: str = "online"
    last_heartbeat: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
