import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

import redis
from sqlalchemy.orm import Session


ROOT_DIR = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT_DIR / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.core.config import settings  # noqa: E402
from app.db.session import Base, SessionLocal, engine  # noqa: E402
from app.models import ChatMessage, ChatSession, ChatTask, Ticket, ToolCallLog  # noqa: E402
from services.mcp_client import CustomerServiceMCPClient  # noqa: E402


class CustomerServiceWorker:
    def __init__(self) -> None:
        Base.metadata.create_all(bind=engine)
        self.redis = redis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            db=settings.redis_db,
            decode_responses=True,
        )
        self.mcp_client = CustomerServiceMCPClient()

    def run_forever(self) -> None:
        print(f"[worker] waiting for tasks from Redis List: {settings.redis_task_queue}")
        while True:
            try:
                _, payload = self.redis.brpop(settings.redis_task_queue, timeout=0)
                task_payload = json.loads(payload)
                self.process_task(task_payload)
            except KeyboardInterrupt:
                print("[worker] stopped by user")
                break
            except Exception as exc:
                print(f"[worker] unexpected loop error: {exc}")
                time.sleep(1)

    def process_task(self, payload: dict[str, Any]) -> None:
        task_id = payload["task_id"]
        session_id = int(payload["session_id"])
        user_message_id = int(payload["user_message_id"])
        question = payload["content"]
        print(f"[worker] received task={task_id} session={session_id}")

        db = SessionLocal()
        try:
            task = db.get(ChatTask, task_id)
            if not task:
                raise ValueError(f"task not found in database: {task_id}")

            self._update_task_state(
                db,
                task,
                status="PROCESSING",
                category=None,
                result=None,
                error_message=None,
            )

            classify_result = self._call_tool(
                db,
                task_id,
                "classify_question",
                {"question": question},
                lambda: self.mcp_client.classify_question(question),
            )
            category = classify_result["category"]

            knowledge_result = self._call_tool(
                db,
                task_id,
                "search_knowledge_base",
                {"question": question, "category": category},
                lambda: self.mcp_client.search_knowledge_base(question, category),
            )
            knowledge_hits = knowledge_result.get("hits", [])

            transfer_result = self._call_tool(
                db,
                task_id,
                "transfer_to_human",
                {"question": question, "category": category},
                lambda: self.mcp_client.transfer_to_human(question, category),
            )
            need_transfer = bool(transfer_result.get("need_transfer"))
            ticket_id = None

            if need_transfer:
                ticket_data = self._call_tool(
                    db,
                    task_id,
                    "create_ticket",
                    {
                        "session_id": session_id,
                        "task_id": task_id,
                        "question": question,
                        "category": category,
                    },
                    lambda: self.mcp_client.create_ticket(session_id, task_id, question, category),
                )
                ticket = Ticket(
                    task_id=task_id,
                    session_id=session_id,
                    title=ticket_data["title"],
                    description=ticket_data["description"],
                    status=ticket_data.get("status", "OPEN"),
                )
                db.add(ticket)
                db.flush()
                ticket_id = ticket.id

            reply_result = self._call_tool(
                db,
                task_id,
                "generate_reply",
                {"question": question, "category": category, "knowledge_hits": knowledge_hits},
                lambda: self.mcp_client.generate_reply(question, category, knowledge_hits),
            )
            reply = reply_result["reply"]

            assistant_message = ChatMessage(
                session_id=session_id,
                role="ASSISTANT",
                content=reply,
                task_id=task_id,
            )
            db.add(assistant_message)

            final_status = "TRANSFERRED" if need_transfer else "SUCCESS"
            self._update_task_state(
                db,
                task,
                status=final_status,
                category=category,
                knowledge_hit=json.dumps(knowledge_hits, ensure_ascii=False),
                result=reply,
                transferred=need_transfer,
                ticket_id=ticket_id,
                error_message=None,
            )

            session = db.get(ChatSession, session_id)
            if session:
                session.last_message = reply
                session.updated_at = datetime.utcnow()

            db.commit()
            self._write_session_cache(session_id, reply, task_id, final_status)
            print(f"[worker] finished task={task_id} status={final_status}")
        except Exception as exc:
            db.rollback()
            self._mark_failed(task_id, session_id, user_message_id, str(exc))
            print(f"[worker] failed task={task_id}: {exc}")
        finally:
            db.close()

    def _call_tool(
        self,
        db: Session,
        task_id: str,
        tool_name: str,
        input_data: dict[str, Any],
        call: Callable[[], dict[str, Any]],
    ) -> dict[str, Any]:
        try:
            output = call()
            db.add(
                ToolCallLog(
                    task_id=task_id,
                    tool_name=tool_name,
                    input_json=json.dumps(input_data, ensure_ascii=False),
                    output_json=json.dumps(output, ensure_ascii=False),
                    success=True,
                )
            )
            db.flush()
            print(f"[worker] tool={tool_name} success")
            return output
        except Exception as exc:
            db.add(
                ToolCallLog(
                    task_id=task_id,
                    tool_name=tool_name,
                    input_json=json.dumps(input_data, ensure_ascii=False),
                    output_json=None,
                    success=False,
                    error_message=str(exc),
                )
            )
            db.flush()
            raise

    def _update_task_state(self, db: Session, task: ChatTask, **fields: Any) -> None:
        now = datetime.utcnow()
        task.updated_at = now
        for key, value in fields.items():
            if hasattr(task, key) and value is not None:
                setattr(task, key, value)
        db.flush()

        state = {
            "task_id": task.id,
            "session_id": task.session_id,
            "user_message_id": task.user_message_id,
            "status": task.status,
            "category": task.category or "",
            "knowledge_hit": task.knowledge_hit or "",
            "result": task.result or "",
            "error_message": task.error_message or "",
            "transferred": task.transferred,
            "ticket_id": task.ticket_id or "",
            "created_at": task.created_at.isoformat(),
            "updated_at": task.updated_at.isoformat(),
        }
        self._hmset(self._task_key(task.id), state)
        self._write_session_cache(task.session_id, "", task.id, task.status)

    def _mark_failed(self, task_id: str, session_id: int, user_message_id: int, error_message: str) -> None:
        db = SessionLocal()
        try:
            task = db.get(ChatTask, task_id)
            if task:
                task.status = "FAILED"
                task.error_message = error_message
                task.updated_at = datetime.utcnow()
                db.commit()
                created_at = task.created_at.isoformat()
                updated_at = task.updated_at.isoformat()
            else:
                created_at = ""
                updated_at = datetime.utcnow().isoformat()

            self._hmset(
                self._task_key(task_id),
                {
                    "task_id": task_id,
                    "session_id": session_id,
                    "user_message_id": user_message_id,
                    "status": "FAILED",
                    "error_message": error_message,
                    "updated_at": updated_at,
                    "created_at": created_at,
                },
            )
            self._write_session_cache(session_id, "", task_id, "FAILED")
        finally:
            db.close()

    def _write_session_cache(self, session_id: int, last_message: str, task_id: str, task_status: str) -> None:
        data = {
            "session_id": session_id,
            "last_task_id": task_id,
            "last_task_status": task_status,
            "updated_at": datetime.utcnow().isoformat(),
        }
        if last_message:
            data["last_message"] = last_message
        self._hmset(self._session_key(session_id), data)

    def _hmset(self, key: str, data: dict[str, Any]) -> None:
        # hmset keeps compatibility with the Windows Redis 3.x package used by some teammates.
        normalized = {field: self._serialize(value) for field, value in data.items() if value is not None}
        self.redis.hmset(key, normalized)

    def _task_key(self, task_id: str) -> str:
        return f"{settings.redis_key_prefix}:task:{task_id}"

    def _session_key(self, session_id: int) -> str:
        return f"{settings.redis_key_prefix}:session:{session_id}"

    @staticmethod
    def _serialize(value: Any) -> str:
        if isinstance(value, bool):
            return json.dumps(value)
        return str(value)


def main() -> None:
    CustomerServiceWorker().run_forever()


if __name__ == "__main__":
    main()
