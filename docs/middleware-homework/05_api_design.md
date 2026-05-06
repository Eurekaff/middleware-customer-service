# 后端 API 设计

## 1. API 总览

后端 API 统一使用 `/api` 前缀，数据格式为 JSON。

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/api/health` | 健康检查 |
| POST | `/api/sessions` | 创建客服会话 |
| GET | `/api/sessions` | 查询会话列表 |
| GET | `/api/sessions/{session_id}` | 查询会话详情 |
| PATCH | `/api/sessions/{session_id}/status` | 更新会话状态 |
| DELETE | `/api/sessions/{session_id}` | 删除会话及关联数据 |
| POST | `/api/sessions/{session_id}/messages` | 发送用户消息并创建任务 |
| GET | `/api/tasks/{task_id}` | 查询任务状态和结果 |
| GET | `/api/admin/tasks` | 查询任务列表 |
| GET | `/api/admin/tool-logs` | 查询 MCP 工具调用日志 |
| GET | `/api/admin/middleware-status` | 查询 Redis、SQLite 和工作流演示状态 |

## 2. GET /api/health

### 2.1 说明

用于检查后端服务是否启动。

### 2.2 示例请求

```bash
curl http://localhost:8000/api/health
```

### 2.3 示例响应

```json
{
  "status": "ok",
  "service": "middleware-customer-service"
}
```

## 3. POST /api/sessions

### 3.1 说明

创建新的客服会话。

### 3.2 请求参数

```json
{
  "title": "课程咨询"
}
```

`title` 可选，后端可使用默认标题。

### 3.3 示例响应

```json
{
  "id": 1,
  "title": "课程咨询",
  "status": "ACTIVE",
  "last_message": "",
  "created_at": "2026-05-06T10:00:00",
  "updated_at": "2026-05-06T10:00:00"
}
```

## 4. GET /api/sessions

### 4.1 说明

查询客服会话列表，按更新时间倒序返回。

### 4.2 示例请求

```bash
curl http://localhost:8000/api/sessions
```

### 4.3 示例响应

```json
[
  {
    "id": 1,
    "title": "课程咨询",
    "status": "ACTIVE",
    "last_message": "我想退款，怎么处理？",
    "created_at": "2026-05-06T10:00:00",
    "updated_at": "2026-05-06T10:01:00"
  }
]
```

## 5. GET /api/sessions/{session_id}

### 5.1 说明

查询指定会话详情，包含消息列表。

### 5.2 示例请求

```bash
curl http://localhost:8000/api/sessions/1
```

### 5.3 示例响应

```json
{
  "id": 1,
  "title": "课程咨询",
  "status": "ACTIVE",
  "last_message": "我想退款，怎么处理？",
  "messages": [
    {
      "id": 1,
      "session_id": 1,
      "role": "USER",
      "content": "我想退款，怎么处理？",
      "task_id": "9a64b2f4-32f0-4f43-89cb-b3a6e2e7c001",
      "created_at": "2026-05-06T10:01:00"
    }
  ],
  "created_at": "2026-05-06T10:00:00",
  "updated_at": "2026-05-06T10:01:00"
}
```

## 6. POST /api/sessions/{session_id}/messages

### 6.1 说明

用户发送消息。后端保存用户消息、创建任务、写入 Redis 任务状态、将任务 JSON 写入 Redis List，并立即返回 `task_id`。

如果会话状态为 `CLOSED`，该接口返回 400，避免继续向已关闭会话发送消息。

### 6.2 请求参数

```json
{
  "content": "我买了课程但是一直打不开，应该怎么办？"
}
```

### 6.3 示例请求

```bash
curl -X POST http://localhost:8000/api/sessions/1/messages \
  -H "Content-Type: application/json" \
  -d "{\"content\":\"我买了课程但是一直打不开，应该怎么办？\"}"
```

### 6.4 示例响应

```json
{
  "task_id": "9a64b2f4-32f0-4f43-89cb-b3a6e2e7c001",
  "session_id": 1,
  "user_message_id": 1,
  "status": "PENDING"
}
```

## 7. PATCH /api/sessions/{session_id}/status

### 7.1 说明

更新会话状态，用于课堂演示中的会话管理。

### 7.2 请求参数

```json
{
  "status": "CLOSED"
}
```

`status` 只允许 `ACTIVE` 或 `CLOSED`。

### 7.3 示例请求

```bash
curl -X PATCH http://localhost:8000/api/sessions/1/status \
  -H "Content-Type: application/json" \
  -d "{\"status\":\"CLOSED\"}"
```

## 8. DELETE /api/sessions/{session_id}

### 8.1 说明

删除会话及其关联的消息、任务、工具调用日志、工单和 Redis 缓存状态。

### 8.2 示例请求

```bash
curl -X DELETE http://localhost:8000/api/sessions/1
```

### 8.3 示例响应

```json
{
  "status": "deleted",
  "session_id": 1
}
```

## 9. GET /api/tasks/{task_id}

### 9.1 说明

查询任务状态和处理结果。后端优先读取 Redis 中的任务状态，如 Redis 中无数据，则回退查询 SQLite。

### 9.2 示例请求

```bash
curl http://localhost:8000/api/tasks/9a64b2f4-32f0-4f43-89cb-b3a6e2e7c001
```

### 9.3 示例响应

```json
{
  "task_id": "9a64b2f4-32f0-4f43-89cb-b3a6e2e7c001",
  "session_id": 1,
  "user_message_id": 1,
  "status": "SUCCESS",
  "category": "技术问题",
  "knowledge_hit": [
    {
      "title": "课程打不开处理建议",
      "content": "请检查网络、浏览器缓存和账号权限。"
    }
  ],
  "result": "您的问题属于技术问题，建议先检查网络、清理浏览器缓存并重新登录。",
  "transferred": false,
  "ticket_id": null,
  "error_message": null,
  "created_at": "2026-05-06T10:01:00",
  "updated_at": "2026-05-06T10:01:05"
}
```

## 10. GET /api/admin/tasks

### 10.1 说明

查询任务列表，便于课堂演示任务状态流转。

### 10.2 示例请求

```bash
curl http://localhost:8000/api/admin/tasks
```

### 10.3 示例响应

```json
[
  {
    "task_id": "9a64b2f4-32f0-4f43-89cb-b3a6e2e7c001",
    "session_id": 1,
    "status": "SUCCESS",
    "category": "技术问题",
    "result": "您的问题属于技术问题，建议先检查网络、清理浏览器缓存并重新登录。",
    "created_at": "2026-05-06T10:01:00",
    "updated_at": "2026-05-06T10:01:05"
  }
]
```

## 11. GET /api/admin/tool-logs

### 11.1 说明

查询 MCP 工具调用日志，便于展示 Worker 调用了哪些工具。

### 11.2 示例请求

```bash
curl http://localhost:8000/api/admin/tool-logs
```

### 11.3 示例响应

```json
[
  {
    "id": 1,
    "task_id": "9a64b2f4-32f0-4f43-89cb-b3a6e2e7c001",
    "tool_name": "classify_question",
    "input_json": "{\"question\":\"我买了课程但是一直打不开，应该怎么办？\"}",
    "output_json": "{\"category\":\"技术问题\"}",
    "success": true,
    "error_message": null,
    "created_at": "2026-05-06T10:01:01"
  }
]
```

## 12. GET /api/admin/middleware-status

### 12.1 说明

查询后台演示页所需的中间件状态。该接口用于课堂展示 Redis 队列、Redis 状态缓存、SQLite 持久化统计和整体工作流。

### 12.2 示例请求

```bash
curl http://localhost:8000/api/admin/middleware-status
```

### 12.3 示例响应

```json
{
  "redis": {
    "connected": true,
    "error": "",
    "queue_name": "customer_service:task_queue",
    "queue_length": 0,
    "queue_preview": [],
    "task_cache_keys": [
      "customer_service:task:9a64b2f4-32f0-4f43-89cb-b3a6e2e7c001"
    ],
    "session_cache_keys": [
      "customer_service:session:1"
    ]
  },
  "sqlite": {
    "sessions": 1,
    "messages": 2,
    "tasks": 1,
    "tool_logs": 4,
    "tickets": 0
  },
  "workflow": [
    "FastAPI 保存用户消息并创建 PENDING 任务",
    "Redis List 保存待处理任务",
    "Worker 使用 BRPOP 阻塞消费任务",
    "Worker 调用 MCP 工具完成分类、检索、回复和转人工判断",
    "SQLite 持久化消息、任务、工单和工具调用日志",
    "Redis Hash 缓存任务状态，前端轮询展示处理结果"
  ]
}
```

该接口只用于演示和调试，不参与用户发送消息的核心处理链路。
