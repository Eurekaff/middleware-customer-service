# 系统架构设计

## 1. 系统总体架构

本系统采用前后端分离和异步任务处理架构。前端通过 HTTP API 调用后端，后端负责会话、消息和任务创建。Redis 作为中间件，承担任务队列、任务状态缓存和会话最近状态缓存。Worker 进程从 Redis List 中阻塞读取任务，调用 MCP Server 暴露的工具完成客服处理，并将结果写入 SQLite。

## 2. 各模块职责

### 2.1 前端 Vue

- 提供聊天页面；
- 展示会话列表；
- 提交用户问题；
- 根据 `task_id` 轮询任务状态；
- 展示机器人回复、分类结果、知识库命中和转人工结果；
- 提供后台演示页查看任务和工具日志。

### 2.2 后端 FastAPI

- 提供 REST API；
- 创建和查询客服会话；
- 保存用户消息；
- 创建任务记录；
- 写入 Redis 任务状态；
- 将任务 JSON 写入 Redis List；
- 查询任务和工具调用日志。

### 2.3 Redis

- `customer_service:task_queue`：Redis List，保存待处理任务；
- `customer_service:task:{task_id}`：Redis Hash，保存任务最新状态；
- `customer_service:session:{session_id}`：Redis Hash，保存会话最近状态。

### 2.4 Worker

- 使用 `BRPOP` 阻塞读取 Redis List；
- 将任务状态更新为 `PROCESSING`；
- 调用 MCP 工具；
- 保存工具调用日志；
- 保存机器人消息；
- 更新任务最终状态。

### 2.5 MCP Server

- 封装智能客服工具能力；
- 提供分类、知识库检索、回复生成、工单创建和转人工判断工具；
- 当前使用规则和模板实现；
- 后续可替换为真实 LLM API 调用。

### 2.6 SQLite

- 持久化保存会话、消息、任务、工具调用日志和工单；
- 作为演示查询和结果验证的数据来源。

## 3. 系统架构图

```mermaid
flowchart LR
    User["用户浏览器"] --> Frontend["Vue 3 前端"]
    Frontend -->|HTTP API| Backend["FastAPI 后端"]
    Backend -->|保存会话/消息/任务| SQLite[("SQLite 数据库")]
    Backend -->|LPUSH 任务| RedisQueue[("Redis List\ncustomer_service:task_queue")]
    Backend -->|写任务状态| RedisStatus[("Redis Hash\n任务/会话状态")]
    Worker["Worker 进程"] -->|BRPOP| RedisQueue
    Worker -->|读写状态| RedisStatus
    Worker -->|调用工具| MCP["MCP Server"]
    MCP --> Tools["客服工具\n分类/检索/回复/工单/转人工"]
    Worker -->|保存结果和日志| SQLite
    Frontend -->|轮询任务状态| Backend
    Backend -->|查询状态和结果| RedisStatus
    Backend -->|必要时查询持久化结果| SQLite
```

## 4. 用户发送消息后的处理流程

```mermaid
sequenceDiagram
    participant U as 用户
    participant F as 前端
    participant B as FastAPI 后端
    participant R as Redis
    participant W as Worker
    participant M as MCP Server
    participant D as SQLite

    U->>F: 输入并发送问题
    F->>B: POST /api/sessions/{id}/messages
    B->>D: 保存用户消息
    B->>D: 创建 chat_task
    B->>R: 写入 task Hash，状态 PENDING
    B->>R: LPUSH 任务到 Redis List
    B-->>F: 返回 task_id
    F->>B: 轮询 GET /api/tasks/{task_id}
    W->>R: BRPOP 读取任务
    W->>R: 更新状态 PROCESSING
    W->>D: 更新 chat_task
    W->>M: 调用 classify_question
    W->>M: 调用 search_knowledge_base
    W->>M: 调用 transfer_to_human
    W->>M: 调用 generate_reply 或 create_ticket
    W->>D: 保存工具调用日志
    W->>D: 保存机器人消息和任务结果
    W->>R: 更新状态 SUCCESS/TRANSFERRED/FAILED
    F->>B: 继续轮询任务状态
    B-->>F: 返回最终处理结果
    F->>B: 刷新会话详情
```

## 5. 任务状态流转图

```mermaid
stateDiagram-v2
    [*] --> PENDING: 后端创建任务
    PENDING --> PROCESSING: Worker 取出任务
    PROCESSING --> SUCCESS: 工具调用成功并生成回复
    PROCESSING --> TRANSFERRED: 判断需要人工处理或创建工单
    PROCESSING --> FAILED: 处理异常
    SUCCESS --> [*]
    TRANSFERRED --> [*]
    FAILED --> [*]
```

## 6. 架构设计说明

本架构通过 Redis List 将后端请求和客服处理过程解耦。后端只负责快速响应用户提交，耗时处理由 Worker 完成。Redis Hash 保存任务状态，使前端可以通过轮询快速看到任务进度。SQLite 保存完整历史，便于课堂展示和结果验证。MCP Server 将工具能力独立封装，体现 AI 工具调用中间层的设计思想。
