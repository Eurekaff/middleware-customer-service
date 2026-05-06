from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class ChatSession(Base):
    __tablename__ = "chat_session"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(100), default="新客服会话")
    status: Mapped[str] = mapped_column(String(20), default="ACTIVE")
    last_message: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    messages: Mapped[list["ChatMessage"]] = relationship(back_populates="session", cascade="all, delete-orphan")
    tasks: Mapped[list["ChatTask"]] = relationship(back_populates="session", cascade="all, delete-orphan")


class ChatMessage(Base):
    __tablename__ = "chat_message"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("chat_session.id"), index=True)
    role: Mapped[str] = mapped_column(String(20))
    content: Mapped[str] = mapped_column(Text)
    task_id: Mapped[str | None] = mapped_column(String(64), index=True, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    session: Mapped[ChatSession] = relationship(back_populates="messages")


class ChatTask(Base):
    __tablename__ = "chat_task"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, index=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("chat_session.id"), index=True)
    user_message_id: Mapped[int] = mapped_column(ForeignKey("chat_message.id"), index=True)
    status: Mapped[str] = mapped_column(String(20), default="PENDING", index=True)
    category: Mapped[str | None] = mapped_column(String(50), nullable=True)
    knowledge_hit: Mapped[str | None] = mapped_column(Text, nullable=True)
    result: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    transferred: Mapped[bool] = mapped_column(Boolean, default=False)
    ticket_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    session: Mapped[ChatSession] = relationship(back_populates="tasks")


class ToolCallLog(Base):
    __tablename__ = "tool_call_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    task_id: Mapped[str] = mapped_column(ForeignKey("chat_task.id"), index=True)
    tool_name: Mapped[str] = mapped_column(String(100))
    input_json: Mapped[str] = mapped_column(Text)
    output_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    success: Mapped[bool] = mapped_column(Boolean, default=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Ticket(Base):
    __tablename__ = "ticket"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    task_id: Mapped[str] = mapped_column(ForeignKey("chat_task.id"), index=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("chat_session.id"), index=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default="OPEN")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
