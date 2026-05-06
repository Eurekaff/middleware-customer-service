# MCP 工具设计

## 1. MCP Server 的职责

MCP Server 作为 AI 工具调用中间层，负责将智能客服需要的工具能力封装成统一接口。Worker 不直接实现分类、检索、回复生成和工单创建逻辑，而是通过 MCP 工具完成。

本项目当前使用规则和模板模拟智能处理能力，不接入真实大模型 API。这样可以保证本地演示稳定，同时保留后续扩展为真实 LLM 调用的代码结构。

## 2. MCP 工具列表

| 工具名称 | 作用 |
| --- | --- |
| `classify_question` | 根据关键词对用户问题分类 |
| `search_knowledge_base` | 根据分类和问题内容检索本地知识库 |
| `generate_reply` | 根据分类和知识库命中结果生成客服回复 |
| `create_ticket` | 为需要人工处理的问题创建工单信息 |
| `transfer_to_human` | 判断问题是否需要转人工 |

## 3. classify_question

### 3.1 输入

```json
{
  "question": "我想退款，怎么处理？"
}
```

### 3.2 输出

```json
{
  "category": "售后退款问题",
  "reason": "命中关键词：退款"
}
```

### 3.3 规则

- 包含“退款、退钱、价格、费用” -> 售后退款问题；
- 包含“无法登录、打不开、报错、不能使用” -> 技术问题；
- 包含“人工、投诉、没人处理、太差” -> 投诉或转人工；
- 包含“怎么购买、多少钱、功能” -> 售前咨询；
- 其他 -> 一般问题。

## 4. search_knowledge_base

### 4.1 输入

```json
{
  "question": "我买了课程但是一直打不开，应该怎么办？",
  "category": "技术问题"
}
```

### 4.2 输出

```json
{
  "hits": [
    {
      "title": "课程打不开处理建议",
      "content": "请检查网络、浏览器缓存和账号权限。"
    }
  ]
}
```

### 4.3 实现方式

知识库保存在 `backend/data/knowledge_base.json`。MCP 工具按分类和关键词匹配返回候选内容。为了减少重复维护，Worker 和 MCP 工具均使用同一份知识库文件。

## 5. generate_reply

### 5.1 输入

```json
{
  "question": "我想退款，怎么处理？",
  "category": "售后退款问题",
  "knowledge_hits": [
    {
      "title": "退款流程说明",
      "content": "请在订单页面提交退款申请。"
    }
  ]
}
```

### 5.2 输出

```json
{
  "reply": "您的问题属于售后退款问题。请在订单页面提交退款申请，系统会根据课程使用情况进行审核。",
  "used_knowledge": true
}
```

### 5.3 实现方式

当前通过模板拼接生成回复。后续接入真实大模型时，可将分类、知识库结果和用户问题组合为 Prompt，由 LLM 生成更自然的回复。

## 6. create_ticket

### 6.1 输入

```json
{
  "session_id": 1,
  "task_id": "9a64b2f4-32f0-4f43-89cb-b3a6e2e7c001",
  "question": "我已经反馈三次了，没人处理，我要人工客服。",
  "category": "投诉或转人工"
}
```

### 6.2 输出

```json
{
  "title": "投诉或转人工处理工单",
  "description": "用户反馈：我已经反馈三次了，没人处理，我要人工客服。",
  "status": "OPEN"
}
```

### 6.3 实现方式

MCP 工具只生成工单信息，实际入库由 Worker 完成。这样可以保持数据库操作集中在 Worker，避免 MCP Server 直接依赖业务数据库。

## 7. transfer_to_human

### 7.1 输入

```json
{
  "question": "我已经反馈三次了，没人处理，我要人工客服。",
  "category": "投诉或转人工"
}
```

### 7.2 输出

```json
{
  "need_transfer": true,
  "reason": "问题包含人工或投诉相关关键词"
}
```

### 7.3 实现方式

当前按分类和关键词判断是否转人工。后续可以增加规则权重、历史投诉次数、用户等级等条件。

## 8. MCP 工具调用流程

```mermaid
sequenceDiagram
    participant W as Worker
    participant M as MCP Server

    W->>M: classify_question(question)
    M-->>W: category
    W->>M: search_knowledge_base(question, category)
    M-->>W: hits
    W->>M: transfer_to_human(question, category)
    M-->>W: need_transfer
    alt 需要转人工
        W->>M: create_ticket(session_id, task_id, question, category)
        M-->>W: ticket data
    else 自动回复
        W->>M: generate_reply(question, category, hits)
        M-->>W: reply
    end
```

## 9. 后续接入真实大模型的扩展方式

后续如果需要接入真实 LLM，可在 `generate_reply` 中替换模板逻辑：

1. 保留工具输入输出结构；
2. 增加 LLM API 配置，如 `OPENAI_API_KEY`，但不提交真实密钥；
3. 将用户问题、分类和知识库命中结果组织为 Prompt；
4. 调用真实模型生成回复；
5. 将模型返回内容作为 `reply` 输出；
6. 在 `tool_call_log` 中记录工具输入输出，便于追踪。

问题分类和转人工判断也可以逐步替换为模型判断，但课程演示阶段使用规则实现更稳定。
