import json
from pathlib import Path
from typing import Any

try:
    from tools.llm_client import get_llm_client
except ModuleNotFoundError:
    from mcp_server.tools.llm_client import get_llm_client


KNOWLEDGE_BASE_PATH = Path(__file__).resolve().parents[2] / "backend" / "data" / "knowledge_base.json"
ALLOWED_CATEGORIES = ["技术问题", "售后退款问题", "投诉或转人工", "售前咨询", "商品咨询", "问候闲聊", "一般问题"]


def classify_question_tool(question: str) -> dict[str, Any]:
    rule_result = _rule_classify_question(question)
    llm = get_llm_client()
    if not llm.enabled:
        return {**rule_result, "llm_used": False, "fallback_used": True}

    prompt = {
        "question": question,
        "rule_category": rule_result["category"],
        "rule_reason": rule_result["reason"],
        "allowed_categories": ALLOWED_CATEGORIES,
        "output_format": {"category": "只能从 allowed_categories 中选择", "reason": "简短说明判断依据"},
    }
    system = (
        "你是客服问题分类助手。你必须只返回 JSON，不要输出 Markdown。"
        "category 字段只能从给定分类列表中选择。"
    )
    llm_result = llm.complete_json(system, json.dumps(prompt, ensure_ascii=False))
    if llm_result.ok:
        category = str(llm_result.data.get("category", "")).strip()
        if category in ALLOWED_CATEGORIES:
            return {
                "category": category,
                "reason": str(llm_result.data.get("reason") or "大模型结合规则结果完成分类"),
                "rule_category": rule_result["category"],
                "rule_reason": rule_result["reason"],
                "llm_used": True,
                "fallback_used": False,
            }

    return {
        **rule_result,
        "llm_used": False,
        "fallback_used": True,
        "llm_error": llm_result.error or "大模型分类结果不在允许分类内",
    }


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
    fallback = _rule_generate_reply(question, category, knowledge_hits)
    llm = get_llm_client()
    if not llm.enabled:
        return {**fallback, "llm_used": False, "fallback_used": True}

    prompt = {
        "question": question,
        "category": category,
        "knowledge_hits": knowledge_hits,
        "need_transfer": category == "投诉或转人工",
        "requirements": [
            "回复必须简洁、礼貌、可执行",
            "优先基于知识库内容，不要编造不存在的政策",
            "如果需要人工处理，说明系统建议创建工单或转人工",
            "回复控制在 150 字以内",
        ],
        "output_format": {"reply": "客服回复文本"},
    }
    system = "你是课程平台客服助手。你必须只返回 JSON，不要输出 Markdown。"
    llm_result = llm.complete_json(system, json.dumps(prompt, ensure_ascii=False))
    if llm_result.ok:
        reply = str(llm_result.data.get("reply", "")).strip()
        if reply:
            return {
                "reply": reply,
                "used_knowledge": bool(knowledge_hits),
                "source_question": question,
                "llm_used": True,
                "fallback_used": False,
            }

    return {
        **fallback,
        "llm_used": False,
        "fallback_used": True,
        "llm_error": llm_result.error or "大模型回复为空",
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
    rule_result = _rule_transfer_to_human(question, category)
    llm = get_llm_client()
    if not llm.enabled:
        return {**rule_result, "llm_used": False, "fallback_used": True}

    prompt = {
        "question": question,
        "category": category,
        "rule_need_transfer": rule_result["need_transfer"],
        "rule_reason": rule_result["reason"],
        "output_format": {"need_transfer": "布尔值", "reason": "简短说明判断依据"},
    }
    system = "你是客服转人工判断助手。你必须只返回 JSON，不要输出 Markdown。"
    llm_result = llm.complete_json(system, json.dumps(prompt, ensure_ascii=False))
    if llm_result.ok and isinstance(llm_result.data.get("need_transfer"), bool):
        return {
            "need_transfer": llm_result.data["need_transfer"],
            "reason": str(llm_result.data.get("reason") or "大模型结合规则结果完成判断"),
            "rule_need_transfer": rule_result["need_transfer"],
            "rule_reason": rule_result["reason"],
            "llm_used": True,
            "fallback_used": False,
        }

    return {
        **rule_result,
        "llm_used": False,
        "fallback_used": True,
        "llm_error": llm_result.error or "大模型转人工结果格式不正确",
    }


def _rule_classify_question(question: str) -> dict[str, str]:
    normalized = question.strip()
    if _contains_any(normalized, ["你好", "您好", "在吗", "早上好", "下午好", "晚上好", "hello", "hi"]):
        return {"category": "问候闲聊", "reason": "命中问候或寒暄相关关键词"}
    if _contains_any(normalized, ["人工", "投诉", "没人处理", "太差"]):
        return {"category": "投诉或转人工", "reason": "命中投诉或人工处理相关关键词"}
    if _contains_any(normalized, ["退款", "退钱", "价格", "费用"]):
        return {"category": "售后退款问题", "reason": "命中退款或费用相关关键词"}
    if _contains_any(normalized, ["无法登录", "打不开", "报错", "不能使用"]):
        return {"category": "技术问题", "reason": "命中技术故障相关关键词"}
    if _contains_any(normalized, ["怎么购买", "多少钱", "功能"]):
        return {"category": "售前咨询", "reason": "命中购买或功能咨询相关关键词"}
    if _contains_any(normalized, ["商品", "产品", "课程", "服务", "套餐", "适合", "介绍"]):
        return {"category": "商品咨询", "reason": "命中商品或课程咨询相关关键词"}
    return {"category": "一般问题", "reason": "未命中明确分类关键词"}


def _rule_generate_reply(question: str, category: str, knowledge_hits: list[dict[str, Any]]) -> dict[str, Any]:
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


def _rule_transfer_to_human(question: str, category: str) -> dict[str, Any]:
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
