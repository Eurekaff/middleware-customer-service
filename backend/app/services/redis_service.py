import json
from datetime import datetime
from typing import Any

import redis

from app.core.config import settings


class RedisService:
    """Redis is used as middleware for queueing tasks and caching recent state."""

    def __init__(self) -> None:
        self.client = redis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            db=settings.redis_db,
            decode_responses=True,
        )

    def task_key(self, task_id: str) -> str:
        return f"{settings.redis_key_prefix}:task:{task_id}"

    def session_key(self, session_id: int) -> str:
        return f"{settings.redis_key_prefix}:session:{session_id}"

    def set_task_status(self, task_id: str, data: dict[str, Any]) -> None:
        normalized = {key: self._serialize(value) for key, value in data.items() if value is not None}
        self.client.hmset(self.task_key(task_id), normalized)

    def get_task_status(self, task_id: str) -> dict[str, str]:
        return self.client.hgetall(self.task_key(task_id))

    def enqueue_task(self, task: dict[str, Any]) -> None:
        # Redis List is the lightweight message queue between FastAPI and Worker.
        self.client.lpush(settings.redis_task_queue, json.dumps(task, ensure_ascii=False))

    def set_session_state(self, session_id: int, data: dict[str, Any]) -> None:
        normalized = {key: self._serialize(value) for key, value in data.items() if value is not None}
        self.client.hmset(self.session_key(session_id), normalized)

    @staticmethod
    def _serialize(value: Any) -> str:
        if isinstance(value, datetime):
            return value.isoformat()
        if isinstance(value, (dict, list, bool)):
            return json.dumps(value, ensure_ascii=False)
        return str(value)


redis_service = RedisService()
