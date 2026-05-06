import json
from pathlib import Path
from typing import Any


KNOWLEDGE_BASE_PATH = Path(__file__).resolve().parents[2] / "backend" / "data" / "knowledge_base.json"


def classify_question_tool(question: str) -> dict[str, str]:
    normalized = question.strip()
    if _contains_any(normalized, ["人工", "投诉", "没人处理", "太差"]):
        return {"category": "投诉或转人工", "reason": "命中投诉或人工处理相关关键词"}
    if _contains_any(normalized, ["退款", "退钱", "价格", "费用"]):
        return {"category": "售后退款问题", "reason": "命中退款或费用相关关键词"}
    if _contains_any(normalized, ["无法登录", "打不开", "报错", "不能使用"]):
        return {"category": "技术问题", "reason": "命中技术故障相关关键词"}
    if _contains_any(normalized, ["怎么购买", "多少钱", "功能"]):
        return {"category": "售前咨询", "reason": "命中购买或功能咨询相关关键词"}
    return {"category": "一般问题", "reason": "未命中明确分类关键词"}


def search_knowledge_base_tool(question: str, category: str) -> dict[str, list[dict[str, Any]]]:
    records = _load_knowledge_base()
    hits: list[dict[str, Any]] = []
    for item in records:
        if item.get("category") == category:
            hits.append(_public_knowledge_item(item))
            continue
        keywords = item.get("keywords", [])
        if any(keyword in question for keyword in keywords):
            hits.append(_public_knowledge_item(item))

    if not hits:
        hits = [
            {
                "category": "一般问题",
                "title": "通用客服处理建议",
                "content": "已收到您的问题，系统会根据问题内容给出初步建议。若无法解决，可继续补充具体情况。",
            }
        ]

    return {"hits": hits[:3]}


def generate_reply_tool(question: str, category: str, knowledge_hits: list[dict[str, Any]]) -> dict[str, Any]:
    if knowledge_hits:
        suggestions = "；".join(hit.get("content", "") for hit in knowledge_hits if hit.get("content"))
        reply = f"您的问题已识别为“{category}”。{suggestions}"
        used_knowledge = True
    else:
        reply = f"您的问题已识别为“{category}”。请补充更多信息，客服系统会继续为您处理。"
        used_knowledge = False

    if category == "投诉或转人工":
        reply += " 当前问题建议转人工客服继续跟进。"

    return {
        "reply": reply,
        "used_knowledge": used_knowledge,
        "source_question": question,
    }


def create_ticket_tool(session_id: int, task_id: str, question: str, category: str) -> dict[str, Any]:
    return {
        "session_id": session_id,
        "task_id": task_id,
        "title": f"{category}处理工单",
        "description": f"用户问题：{question}",
        "status": "OPEN",
    }


def transfer_to_human_tool(question: str, category: str) -> dict[str, Any]:
    need_transfer = category == "投诉或转人工" or _contains_any(question, ["人工", "投诉", "没人处理", "太差"])
    reason = "问题包含投诉或人工客服相关关键词" if need_transfer else "规则判断可先由机器人自动回复"
    return {"need_transfer": need_transfer, "reason": reason}


def _load_knowledge_base() -> list[dict[str, Any]]:
    with KNOWLEDGE_BASE_PATH.open("r", encoding="utf-8") as file:
        return json.load(file)


def _public_knowledge_item(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "category": item.get("category", ""),
        "title": item.get("title", ""),
        "content": item.get("content", ""),
    }


def _contains_any(text: str, keywords: list[str]) -> bool:
    return any(keyword in text for keyword in keywords)
