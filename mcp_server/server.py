from mcp.server.fastmcp import FastMCP

from tools.customer_service_tools import (
    classify_question_tool,
    create_ticket_tool,
    generate_reply_tool,
    search_knowledge_base_tool,
    transfer_to_human_tool,
)

mcp = FastMCP("middleware-customer-service-mcp")


@mcp.tool()
def classify_question(question: str) -> dict:
    """Classify a customer question by rule-based keywords."""
    return classify_question_tool(question)


@mcp.tool()
def search_knowledge_base(question: str, category: str) -> dict:
    """Search the local course customer-service knowledge base."""
    return search_knowledge_base_tool(question, category)


@mcp.tool()
def generate_reply(question: str, category: str, knowledge_hits: list[dict]) -> dict:
    """Generate a template-based customer-service reply."""
    return generate_reply_tool(question, category, knowledge_hits)


@mcp.tool()
def create_ticket(session_id: int, task_id: str, question: str, category: str) -> dict:
    """Create ticket data for a question that needs manual follow-up."""
    return create_ticket_tool(session_id, task_id, question, category)


@mcp.tool()
def transfer_to_human(question: str, category: str) -> dict:
    """Decide whether a question should be transferred to a human agent."""
    return transfer_to_human_tool(question, category)


if __name__ == "__main__":
    mcp.run()
