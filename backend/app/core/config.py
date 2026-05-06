from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    backend_host: str = "127.0.0.1"
    backend_port: int = 8000
    database_url: str = "sqlite:///./app.db"

    redis_host: str = "127.0.0.1"
    redis_port: int = 6379
    redis_db: int = 0
    redis_task_queue: str = "customer_service:task_queue"
    redis_key_prefix: str = "customer_service"

    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]

    model_config = SettingsConfigDict(env_file="../.env", env_file_encoding="utf-8", extra="ignore")


def _normalize_sqlite_url(database_url: str) -> str:
    prefix = "sqlite:///"
    if not database_url.startswith(prefix):
        return database_url

    db_path = database_url[len(prefix) :]
    if db_path.startswith("/") or ":" in Path(db_path).drive:
        return database_url
    return f"{prefix}{(BACKEND_DIR / db_path).as_posix()}"


@lru_cache
def get_settings() -> Settings:
    loaded = Settings()
    loaded.database_url = _normalize_sqlite_url(loaded.database_url)
    return loaded


settings = get_settings()
