import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI


ROOT_DIR = Path(__file__).resolve().parents[2]
load_dotenv(ROOT_DIR / ".env")


@dataclass
class LLMResult:
    ok: bool
    data: dict[str, Any]
    error: str | None = None


class LLMClient:
    def __init__(self) -> None:
        self.enabled = _is_truthy(os.getenv("LLM_ENABLE", "false"))
        self.api_key = os.getenv("LLM_API_KEY", "")
        self.base_url = os.getenv("LLM_BASE_URL") or None
        self.model = os.getenv("LLM_MODEL", "")
        self.timeout = float(os.getenv("LLM_TIMEOUT_SECONDS", "20"))
        if not self.api_key or not self.model:
            self.enabled = False

        self._client: OpenAI | None = None
        if self.enabled:
            self._client = OpenAI(api_key=self.api_key, base_url=self.base_url, timeout=self.timeout)

    def complete_json(self, system_prompt: str, user_prompt: str) -> LLMResult:
        if not self.enabled or self._client is None:
            return LLMResult(ok=False, data={}, error="LLM is disabled or not configured")

        try:
            response = self._client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.2,
            )
            content = response.choices[0].message.content or ""
            return LLMResult(ok=True, data=_parse_json_object(content))
        except Exception as exc:
            return LLMResult(ok=False, data={}, error=str(exc))


def get_llm_client() -> LLMClient:
    return LLMClient()


def _parse_json_object(content: str) -> dict[str, Any]:
    cleaned = content.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`").strip()
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:].strip()
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start >= 0 and end >= start:
        cleaned = cleaned[start : end + 1]
    parsed = json.loads(cleaned)
    if not isinstance(parsed, dict):
        raise ValueError("LLM output is not a JSON object")
    return parsed


def _is_truthy(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "on"}
