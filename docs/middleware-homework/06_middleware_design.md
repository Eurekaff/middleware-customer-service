# 中间件设计

## 1. Redis 在系统中的作用

本项目使用 Redis 作为核心中间件，主要承担任务队列、任务状态缓存和会话状态缓存三类职责。Redis 不替代 SQLite 的持久化职责，而是用于提升任务流转和状态查询的效率。

## 2. Redis 作为任务队列

### 2.1 Key 设计

任务队列使用 Redis List：

```text
customer_service:task_queue
```

后端在用户发送消息后，将任务 JSON 写入该 List。Worker 使用阻塞读取命令从队列中消费任务。

### 2.2 入队设计

后端完成以下操作后再将任务入队：

1. 保存用户消息到 `chat_message`；
2. 创建 `chat_task` 记录；
3. 写入 Redis 任务状态 Hash；
4. 将任务 JSON 写入 Redis List。

任务 JSON 示例：

```json
{
  "task_id": "9a64b2f4-32f0-4f43-89cb-b3a6e2e7c001",
  "session_id": 1,
  "user_message_id": 1,
  "content": "我想退款，怎么处理？"
}
```

### 2.3 出队设计

Worker 使用 `BRPOP customer_service:task_queue 0` 阻塞等待任务。当队列为空时，Worker 不需要频繁轮询，可以降低 CPU 空转。

## 3. Redis 作为任务状态缓存

### 3.1 Key 设计

每个任务使用独立 Hash 保存状态：

```text
customer_service:task:{task_id}
```

### 3.2 字段设计

```text
task_id
session_id
user_message_id
status
category
result
error_message
created_at
updated_at
knowledge_hit
transferred
ticket_id
```

其中 `knowledge_hit` 用于前端展示知识库命中结果，`transferred` 用于标记是否转人工，`ticket_id` 用于关联自动创建的工单。

### 3.3 状态更新时机

- 后端创建任务时写入 `PENDING`；
- Worker 取出任务后更新为 `PROCESSING`；
- Worker 成功生成回复后更新为 `SUCCESS`；
- Worker 判断需要人工处理时更新为 `TRANSFERRED`；
- Worker 处理异常时更新为 `FAILED`。

## 4. Redis 作为会话状态缓存

### 4.1 Key 设计

```text
customer_service:session:{session_id}
```

### 4.2 字段设计

```text
session_id
last_message
last_task_id
last_task_status
updated_at
```

该缓存用于展示会话最近状态。SQLite 仍然保存完整会话历史。

## 5. Worker 异步消费机制

Worker 独立于后端运行。后端创建任务后立即返回，不等待客服处理完成。Worker 后台处理任务，处理完成后更新 Redis 和 SQLite。

处理流程如下：

1. `BRPOP` 获取任务；
2. 更新任务状态为 `PROCESSING`；
3. 调用 MCP 工具完成处理；
4. 保存工具调用日志；
5. 保存机器人回复；
6. 更新任务状态为 `SUCCESS`、`TRANSFERRED` 或 `FAILED`；
7. 继续等待下一个任务。

这种设计可以避免用户请求被耗时处理阻塞，也能清楚展示中间件在异步工作流中的作用。

## 6. 失败处理机制

Worker 需要捕获单个任务处理过程中的异常，避免一个任务失败导致整个 Worker 进程退出。

失败时需要完成：

- 将 `chat_task.status` 更新为 `FAILED`；
- 将错误信息写入 `chat_task.error_message`；
- 将 Redis 任务状态更新为 `FAILED`；
- 尽量保存失败工具调用日志；
- 打印错误日志，方便课堂演示。

本项目暂不实现复杂重试机制。后续可以增加重试次数、死信队列和失败告警。

## 7. 为什么选择 Redis List

本项目选择 Redis List 而不是 Kafka 或 RabbitMQ，原因如下：

1. Redis 部署简单，本地运行成本低；
2. Redis List 支持 `LPUSH`、`BRPOP` 等命令，可以满足轻量级队列需求；
3. 项目重点是展示中间件作用，不需要高吞吐日志流和复杂消费者组；
4. Kafka 对环境要求较高，不适合本课程项目的最小可运行目标；
5. RabbitMQ 功能更完整，但会增加安装、交换机、队列绑定等额外概念。

因此，Redis List 更适合本项目的课程演示目标。

## 8. 与 SQLite 的职责边界

Redis 保存“最近状态”和“待处理任务”，SQLite 保存“完整事实记录”。当前端查询任务状态时，后端优先读取 Redis；如果 Redis 中没有对应状态，再回退到 SQLite。这样既能体现缓存作用，也能保证数据最终可查。

## 9. 后台中间件演示接口

为了方便课堂演示，后端提供：

```text
GET /api/admin/middleware-status
```

该接口返回以下信息：

- Redis 是否连接成功；
- `customer_service:task_queue` 队列长度；
- 最近任务状态缓存 key；
- 最近会话状态缓存 key；
- SQLite 中会话、消息、任务、工具日志和工单数量；
- 完整工作流说明。

前端后台页 `/admin` 会调用该接口，将 Redis、Worker、MCP、SQLite 和前后端轮询的作用集中展示，便于答辩时说明各中间件在链路中的职责。
