from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class SessionCreate(BaseModel):
    title: str | None = None


class SessionStatusUpdate(BaseModel):
    status: str


class MessageCreate(BaseModel):
    content: str


class MessageRead(BaseModel):
    id: int
    session_id: int
    role: str
    content: str
    task_id: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SessionRead(BaseModel):
    id: int
    title: str
    status: str
    last_message: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SessionDetail(SessionRead):
    messages: list[MessageRead]


class MessageTaskCreated(BaseModel):
    task_id: str
    session_id: int
    user_message_id: int
    status: str


class TaskRead(BaseModel):
    task_id: str
    session_id: int
    user_message_id: int
    status: str
    category: str | None = None
    knowledge_hit: Any = None
    result: str | None = None
    transferred: bool = False
    ticket_id: int | None = None
    error_message: str | None = None
    created_at: str | datetime | None = None
    updated_at: str | datetime | None = None


class AdminTaskRead(BaseModel):
    task_id: str
    session_id: int
    status: str
    category: str | None = None
    result: str | None = None
    created_at: datetime
    updated_at: datetime


class ToolCallLogRead(BaseModel):
    id: int
    task_id: str
    tool_name: str
    input_json: str
    output_json: str | None
    success: bool
    error_message: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
