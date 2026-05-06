from datetime import datetime
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, selectinload

from app.db.session import get_db
from app.models import ChatMessage, ChatSession, ChatTask, ToolCallLog
from app.schemas.chat import (
    AdminTaskRead,
    MessageCreate,
    MessageTaskCreated,
    SessionCreate,
    SessionDetail,
    SessionRead,
    TaskRead,
    ToolCallLogRead,
)
from app.services.redis_service import redis_service
from app.utils.json import loads_optional

router = APIRouter()


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "middleware-customer-service"}


@router.post("/sessions", response_model=SessionRead)
def create_session(payload: SessionCreate, db: Session = Depends(get_db)) -> ChatSession:
    title = payload.title or "新客服会话"
    session = ChatSession(title=title, last_message="")
    db.add(session)
    db.commit()
    db.refresh(session)
    redis_service.set_session_state(
        session.id,
        {
            "session_id": session.id,
            "last_message": session.last_message,
            "last_task_id": "",
            "last_task_status": "",
            "updated_at": session.updated_at,
        },
    )
    return session


@router.get("/sessions", response_model=list[SessionRead])
def list_sessions(db: Session = Depends(get_db)) -> list[ChatSession]:
    return db.query(ChatSession).order_by(ChatSession.updated_at.desc()).all()


@router.get("/sessions/{session_id}", response_model=SessionDetail)
def get_session(session_id: int, db: Session = Depends(get_db)) -> ChatSession:
    session = (
        db.query(ChatSession)
        .options(selectinload(ChatSession.messages))
        .filter(ChatSession.id == session_id)
        .first()
    )
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    session.messages.sort(key=lambda message: message.created_at)
    return session


@router.post("/sessions/{session_id}/messages", response_model=MessageTaskCreated)
def send_message(session_id: int, payload: MessageCreate, db: Session = Depends(get_db)) -> MessageTaskCreated:
    content = payload.content.strip()
    if not content:
        raise HTTPException(status_code=400, detail="Message content cannot be empty")

    session = db.get(ChatSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    task_id = str(uuid4())
    now = datetime.utcnow()
    user_message = ChatMessage(session_id=session_id, role="USER", content=content, task_id=task_id)
    db.add(user_message)
    db.flush()

    task = ChatTask(
        id=task_id,
        session_id=session_id,
        user_message_id=user_message.id,
        status="PENDING",
        created_at=now,
        updated_at=now,
    )
    session.last_message = content
    if session.title in {"新客服会话", "新建会话"}:
        session.title = _generate_session_title(content)
    session.updated_at = now
    db.add(task)
    db.commit()
    db.refresh(task)

    task_state = {
        "task_id": task.id,
        "session_id": session_id,
        "user_message_id": user_message.id,
        "status": "PENDING",
        "category": "",
        "result": "",
        "error_message": "",
        "created_at": task.created_at,
        "updated_at": task.updated_at,
    }
    redis_service.set_task_status(task.id, task_state)
    redis_service.set_session_state(
        session_id,
        {
            "session_id": session_id,
            "last_message": content,
            "last_task_id": task.id,
            "last_task_status": "PENDING",
            "updated_at": task.updated_at,
        },
    )
    redis_service.enqueue_task(
        {
            "task_id": task.id,
            "session_id": session_id,
            "user_message_id": user_message.id,
            "content": content,
        }
    )
    return MessageTaskCreated(
        task_id=task.id,
        session_id=session_id,
        user_message_id=user_message.id,
        status="PENDING",
    )


@router.get("/tasks/{task_id}", response_model=TaskRead)
def get_task(task_id: str, db: Session = Depends(get_db)) -> TaskRead:
    cached = redis_service.get_task_status(task_id)
    if cached:
        return TaskRead(
            task_id=cached.get("task_id", task_id),
            session_id=int(cached.get("session_id", 0)),
            user_message_id=int(cached.get("user_message_id", 0)),
            status=cached.get("status", "UNKNOWN"),
            category=cached.get("category") or None,
            knowledge_hit=loads_optional(cached.get("knowledge_hit")),
            result=cached.get("result") or None,
            transferred=loads_optional(cached.get("transferred")) or False,
            ticket_id=int(cached["ticket_id"]) if cached.get("ticket_id") else None,
            error_message=cached.get("error_message") or None,
            created_at=cached.get("created_at"),
            updated_at=cached.get("updated_at"),
        )

    task = db.get(ChatTask, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return _task_to_read(task)


@router.get("/admin/tasks", response_model=list[AdminTaskRead])
def list_tasks(db: Session = Depends(get_db)) -> list[AdminTaskRead]:
    tasks = db.query(ChatTask).order_by(ChatTask.created_at.desc()).all()
    return [
        AdminTaskRead(
            task_id=task.id,
            session_id=task.session_id,
            status=task.status,
            category=task.category,
            result=task.result,
            created_at=task.created_at,
            updated_at=task.updated_at,
        )
        for task in tasks
    ]


@router.get("/admin/tool-logs", response_model=list[ToolCallLogRead])
def list_tool_logs(db: Session = Depends(get_db)) -> list[ToolCallLog]:
    return db.query(ToolCallLog).order_by(ToolCallLog.created_at.desc()).all()


def _task_to_read(task: ChatTask) -> TaskRead:
    return TaskRead(
        task_id=task.id,
        session_id=task.session_id,
        user_message_id=task.user_message_id,
        status=task.status,
        category=task.category,
        knowledge_hit=loads_optional(task.knowledge_hit),
        result=task.result,
        transferred=task.transferred,
        ticket_id=task.ticket_id,
        error_message=task.error_message,
        created_at=task.created_at,
        updated_at=task.updated_at,
    )


def _generate_session_title(content: str) -> str:
    compact = " ".join(content.strip().split())
    if not compact:
        return "新客服会话"
    return compact[:18] + ("..." if len(compact) > 18 else "")
