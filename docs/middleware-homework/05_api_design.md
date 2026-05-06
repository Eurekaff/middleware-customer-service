# 后端 API 设计

## 1. API 总览

后端 API 统一使用 `/api` 前缀，数据格式为 JSON。

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/api/health` | 健康检查 |
| POST | `/api/sessions` | 创建客服会话 |
| GET | `/api/sessions` | 查询会话列表 |
| GET | `/api/sessions/{session_id}` | 查询会话详情 |
| POST | `/api/sessions/{session_id}/messages` | 发送用户消息并创建任务 |
| GET | `/api/tasks/{task_id}` | 查询任务状态和结果 |
| GET | `/api/admin/tasks` | 查询任务列表 |
| GET | `/api/admin/tool-logs` | 查询 MCP 工具调用日志 |

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

## 7. GET /api/tasks/{task_id}

### 7.1 说明

查询任务状态和处理结果。后端优先读取 Redis 中的任务状态，如 Redis 中无数据，则回退查询 SQLite。

### 7.2 示例请求

```bash
curl http://localhost:8000/api/tasks/9a64b2f4-32f0-4f43-89cb-b3a6e2e7c001
```

### 7.3 示例响应

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

## 8. GET /api/admin/tasks

### 8.1 说明

查询任务列表，便于课堂演示任务状态流转。

### 8.2 示例请求

```bash
curl http://localhost:8000/api/admin/tasks
```

### 8.3 示例响应

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

## 9. GET /api/admin/tool-logs

### 9.1 说明

查询 MCP 工具调用日志，便于展示 Worker 调用了哪些工具。

### 9.2 示例请求

```bash
curl http://localhost:8000/api/admin/tool-logs
```

### 9.3 示例响应

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
