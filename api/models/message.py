from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class MessageCreate(BaseModel):
    sender_id: str
    project: str
    content: str
    recipient_id: Optional[str] = None


class Message(MessageCreate):
    id: str = Field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
