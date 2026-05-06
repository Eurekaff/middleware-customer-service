import sys
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from mcp_server.tools.customer_service_tools import (  # noqa: E402
    classify_question_tool,
    create_ticket_tool,
    generate_reply_tool,
    search_knowledge_base_tool,
    transfer_to_human_tool,
)


class CustomerServiceMCPClient:
    """Local MCP tool wrapper.

    The MCP Server entrypoint remains in mcp_server/server.py. For the course demo,
    the Worker calls the same tool functions directly to keep the local chain stable.
    """

    def classify_question(self, question: str) -> dict[str, Any]:
        return classify_question_tool(question)

    def search_knowledge_base(self, question: str, category: str) -> dict[str, Any]:
        return search_knowledge_base_tool(question, category)

    def generate_reply(self, question: str, category: str, knowledge_hits: list[dict[str, Any]]) -> dict[str, Any]:
        return generate_reply_tool(question, category, knowledge_hits)

    def create_ticket(self, session_id: int, task_id: str, question: str, category: str) -> dict[str, Any]:
        return create_ticket_tool(session_id, task_id, question, category)

    def transfer_to_human(self, question: str, category: str) -> dict[str, Any]:
        return transfer_to_human_tool(question, category)
