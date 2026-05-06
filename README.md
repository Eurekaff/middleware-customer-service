# 基于 MCP 协议与 Redis 的智能客服工作流系统

本项目是中间件技术课程大作业，目标是实现一个本地可运行的智能客服工作流系统，用于展示 Redis、Worker、MCP Server、SQLite 和前后端分离 Web 应用在客服任务处理链路中的作用。

项目已完成本地联调和课程验收演示链路。当前版本支持用户提问、后端创建任务、Redis 入队、Worker 异步消费、MCP 工具处理、SQLite 持久化、Redis 状态更新和前端展示最终回复。

## 1. 技术栈

前端：

- Vue 3
- Vite
- Axios

后端：

- FastAPI
- SQLAlchemy
- SQLite
- redis-py

中间件：

- Redis
- Redis List 轻量任务队列
- Redis Hash 任务状态缓存

异步与工具层：

- 独立 Worker 进程
- MCP Server
- Python MCP SDK

## 2. 项目目录

```text
middleware-customer-service/
├── README.md
├── .env.example
├── docker-compose.yml
├── docs/
│   └── middleware-homework/
├── backend/
│   ├── requirements.txt
│   ├── main.py
│   ├── app/
│   └── data/
├── worker/
├── mcp_server/
└── frontend/
```

## 3. 当前已实现功能

已实现：

- 课程设计文档；
- 项目目录骨架；
- Redis 配置文件；
- FastAPI 后端应用；
- SQLAlchemy 数据模型；
- SQLite 自动建表；
- 会话创建和查询；
- 用户消息保存；
- 客服任务创建；
- Redis 任务状态 Hash 写入；
- Redis List 任务入队；
- 任务状态查询；
- 后台任务列表和工具日志 API；
- MCP Server 入口；
- MCP 工具规则实现；
- MCP 工具可选大模型辅助判断和回复；
- Worker 使用 Redis `BRPOP` 消费任务；
- Worker 调用 MCP 工具并写入工具日志；
- Worker 写入机器人回复、工单和任务结果；
- Worker 更新 Redis 任务状态；
- Vue 3 前端聊天页；
- 会话列表；
- 当前任务状态面板；
- 后台演示页任务与 MCP 工具日志展示；
- 后台演示页展示 Redis 队列、Redis 缓存、Worker、MCP、SQLite 和前后端轮询的中间件说明；
- 后台演示页通过 `/api/admin/middleware-status` 展示 Redis 与 SQLite 实时状态。

建议补充材料：

- 课堂演示截图；
- 答辩 PPT；
- 实验报告正文排版。

## 4. 环境要求

建议版本：

- Python 3.10 或更高版本；
- Node.js 18 或更高版本；
- Redis；
- npm；
- 可选：Docker Desktop。

当前 Windows 本地开发环境已验证：

- Redis on Windows 3.0.504；
- Redis 服务端口：`6379`；
- 后端端口：`8000`。

## 5. Redis 安装与启动

### 5.1 Windows 使用 winget 安装

如果成员使用 Windows，并且已经安装 `winget`，可以执行：

```powershell
winget install --id Redis.Redis -e --accept-package-agreements --accept-source-agreements
```

安装完成后 Redis 默认位置：

```text
C:\Program Files\Redis
```

Redis 会注册为 Windows 服务：

```powershell
Get-Service Redis
```

如果服务没有运行，可以启动：

```powershell
Start-Service Redis
```

验证 Redis：

```powershell
& "C:\Program Files\Redis\redis-cli.exe" ping
```

预期输出：

```text
PONG
```

重启终端后，如果 Redis 已加入 PATH，也可以直接执行：

```powershell
redis-cli ping
```

### 5.2 使用 Docker Compose 启动 Redis

如果成员已安装 Docker Desktop，也可以在项目根目录执行：

```powershell
docker compose up -d redis
```

验证：

```powershell
docker compose ps
```

或使用本机 Redis CLI：

```powershell
redis-cli ping
```

## 6. 后端运行方式

进入后端目录：

```powershell
cd backend
```

创建虚拟环境：

```powershell
python -m venv .venv
```

激活虚拟环境：

```powershell
.\.venv\Scripts\activate
```

安装依赖：

```powershell
pip install -r requirements.txt
```

启动后端：

```powershell
python main.py
```

后端默认地址：

```text
http://127.0.0.1:8000
```

数据库会在后端启动时自动初始化，默认生成：

```text
backend/app.db
```

该数据库文件是本地运行产物，不需要提交。

## 7. 后端 API 验证

### 7.1 健康检查

```powershell
curl http://127.0.0.1:8000/api/health
```

预期响应：

```json
{
  "status": "ok",
  "service": "middleware-customer-service"
}
```

### 7.2 创建会话

```powershell
curl -X POST http://127.0.0.1:8000/api/sessions `
  -H "Content-Type: application/json" `
  -d "{\"title\":\"测试会话\"}"
```

### 7.3 发送消息并创建任务

假设创建出的会话 ID 是 `1`：

```powershell
curl -X POST http://127.0.0.1:8000/api/sessions/1/messages `
  -H "Content-Type: application/json" `
  -d "{\"content\":\"我想退款，怎么处理？\"}"
```

预期响应中包含：

```json
{
  "task_id": "...",
  "session_id": 1,
  "user_message_id": 1,
  "status": "PENDING"
}
```

### 7.4 查询任务状态

```powershell
curl http://127.0.0.1:8000/api/tasks/{task_id}
```

在 Worker 正常运行时，任务会从 `PENDING` 进入 `PROCESSING`，最终变为：

```text
SUCCESS / FAILED / TRANSFERRED
```

其中 `SUCCESS` 表示智能客服已生成回复，`TRANSFERRED` 表示系统判断需要人工处理并创建工单，`FAILED` 表示 Worker 处理异常。

## 8. Redis 队列验证

发送消息后，可以检查 Redis 队列长度。若 Worker 尚未消费，队列长度会增加；若 Worker 已处理完成，队列长度通常会回到 `0`：

```powershell
& "C:\Program Files\Redis\redis-cli.exe" LLEN customer_service:task_queue
```

未启动 Worker 时的预期结果：

```text
1
```

Worker 正常运行并消费完成后的预期结果：

```text
0
```

查看任务状态 Hash：

```powershell
& "C:\Program Files\Redis\redis-cli.exe" HGETALL customer_service:task:{task_id}
```

其中 `{task_id}` 替换为接口返回的真实任务 ID。

预期可以看到：

```text
task_id
...
session_id
1
user_message_id
1
status
PENDING
```

如需清空当前 Redis 测试数据：

```powershell
& "C:\Program Files\Redis\redis-cli.exe" FLUSHDB
```

## 9. 当前完整启动顺序

完整项目启动顺序：

1. 启动 Redis；
2. 启动后端；
3. 启动 MCP Server；
4. 启动 Worker；
5. 启动前端。

## 10. MCP Server 运行方式

进入 MCP Server 目录：

```powershell
cd mcp_server
```

创建虚拟环境：

```powershell
python -m venv .venv
```

激活虚拟环境：

```powershell
.\.venv\Scripts\activate
```

安装依赖：

```powershell
pip install -r requirements.txt
```

启动 MCP Server：

```powershell
python server.py
```

当前 MCP 工具采用“规则兜底 + 可选大模型增强”模式。未配置大模型时，系统使用本地规则和模板，保证课堂演示稳定可运行；配置 OpenAI 兼容接口后，问题分类、转人工判断和客服回复会优先由大模型辅助完成。

当前 Worker 直接复用 `mcp_server/tools/customer_service_tools.py` 中的本地函数以保证课程演示链路稳定。后续可以替换为标准 MCP Client 调用。

已实现工具：

- `classify_question`
- `search_knowledge_base`
- `generate_reply`
- `create_ticket`
- `transfer_to_human`

## 11. Worker 运行方式

进入 Worker 目录：

```powershell
cd worker
```

创建虚拟环境：

```powershell
python -m venv .venv
```

激活虚拟环境：

```powershell
.\.venv\Scripts\activate
```

安装依赖：

```powershell
pip install -r requirements.txt
```

启动 Worker：

```powershell
python worker.py
```

Worker 会阻塞等待 Redis List 中的任务：

```text
customer_service:task_queue
```

收到任务后，Worker 会执行：

```text
BRPOP 出队 -> PROCESSING -> MCP 工具调用 -> 保存工具日志 -> 保存机器人回复/工单 -> SUCCESS 或 TRANSFERRED
```

## 12. 大模型辅助配置

大模型配置是可选项。复制 `.env.example` 为 `.env`：

```powershell
copy .env.example .env
```

默认大模型提供方为阿里云百炼通义千问，使用 OpenAI 兼容接口。在 `.env` 中填写：

```env
LLM_ENABLE=true
LLM_API_KEY=你的 API Key
LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
LLM_MODEL=qwen-plus
LLM_TIMEOUT_SECONDS=20
```

说明：

- `LLM_ENABLE=false` 时完全使用本地规则和模板；
- `LLM_ENABLE=true` 但 `LLM_API_KEY` 为空时，会自动回退到本地规则；
- `LLM_BASE_URL` 默认使用阿里云百炼北京地域 OpenAI 兼容地址；
- `LLM_MODEL` 默认使用 `qwen-plus`；
- 也支持 DeepSeek、智谱等提供 OpenAI 兼容接口的模型服务；
- 不要把真实 API Key 提交到仓库。

大模型当前参与三个工具：

- `classify_question`：规则先给初步分类，大模型从固定分类枚举中二次判断；
- `transfer_to_human`：规则先判断，大模型辅助确认是否转人工；
- `generate_reply`：结合用户问题、分类和知识库命中生成更自然的客服回复。

`search_knowledge_base` 仍使用本地 JSON 知识库，保证结果可解释、可复现。

## 13. MCP 工具本地测试

在 `mcp_server` 目录且已激活该目录虚拟环境后执行：

```powershell
python -c "from tools.customer_service_tools import classify_question_tool; print(classify_question_tool('我想退款，怎么处理？'))"
```

预期输出包含：

```text
售后退款问题
```

测试转人工判断：

```powershell
python -c "from tools.customer_service_tools import classify_question_tool, transfer_to_human_tool; q='我已经反馈三次了，没人处理，我要人工客服。'; c=classify_question_tool(q)['category']; print(c, transfer_to_human_tool(q, c))"
```

预期输出包含：

```text
投诉或转人工
need_transfer
True
```

## 14. 任务处理联调验证

启动 Redis、后端和 Worker 后，创建会话并发送消息：

```powershell
curl -X POST http://127.0.0.1:8000/api/sessions `
  -H "Content-Type: application/json" `
  -d "{\"title\":\"Worker联调会话\"}"
```

```powershell
curl -X POST http://127.0.0.1:8000/api/sessions/1/messages `
  -H "Content-Type: application/json" `
  -d "{\"content\":\"我想退款，怎么处理？\"}"
```

查询任务状态：

```powershell
curl http://127.0.0.1:8000/api/tasks/{task_id}
```

预期状态为 `SUCCESS`。如果问题需要人工处理，预期状态为 `TRANSFERRED`。

查询工具调用日志：

```powershell
curl http://127.0.0.1:8000/api/admin/tool-logs
```

查询后台中间件状态：

```powershell
curl http://127.0.0.1:8000/api/admin/middleware-status
```

该接口用于后台演示页，返回 Redis 连接状态、队列长度、任务缓存 key、会话缓存 key 和 SQLite 数据统计。

验证 Redis 队列已被消费：

```powershell
& "C:\Program Files\Redis\redis-cli.exe" LLEN customer_service:task_queue
```

预期结果：

```text
0
```

当前已完成的本地联调结果：

| 测试问题 | 预期分类 | 实际状态 | 说明 |
| --- | --- | --- | --- |
| 我买了课程但是一直打不开，应该怎么办？ | 技术问题 | SUCCESS | Worker 生成排查建议 |
| 我想退款，怎么处理？ | 售后退款问题 | SUCCESS | Worker 生成退款流程说明 |
| 我已经反馈三次了，没人处理，我要人工客服。 | 投诉或转人工 | TRANSFERRED | Worker 创建工单 |
| 这个产品多少钱，有哪些功能？ | 售前咨询 | SUCCESS | Worker 生成售前咨询回复 |
| 你好 | 问候闲聊 | SUCCESS | Worker 生成接待问候 |
| 介绍一下课程套餐 | 商品咨询 | SUCCESS | Worker 生成商品咨询回复 |
| 11 | 无效输入 | SUCCESS | Worker 引导用户补充具体问题 |

当前验收结果：Redis 队列最终长度为 `0`，SQLite 能保存任务、聊天消息、工单和 MCP 工具调用日志；前端聊天页能展示智能客服回复，后台页能展示 Redis、Worker、MCP、SQLite 等中间件说明和实时状态。

## 15. 前端运行方式

进入前端目录：

```powershell
cd frontend
```

安装依赖：

```powershell
npm install
```

启动开发服务器：

```powershell
npm run dev
```

前端默认地址：

```text
http://127.0.0.1:5173
```

页面说明：

- `/`：聊天页，左侧会话列表，中间聊天窗口，右侧任务状态面板；
- `/admin`：后台演示页，展示中间件说明、Redis 实时状态、SQLite 统计、课堂演示步骤、任务列表和 MCP 工具调用日志。
- 会话列表支持关闭、恢复和删除会话；
- 删除会话会同步清理消息、任务、工具日志、工单和 Redis 状态。

前端接口配置位置：

```text
frontend/src/api/client.js
```

默认 API 地址：

```text
http://127.0.0.1:8000/api
```

生产构建验证：

```powershell
npm run build
```

## 16. 关键配置

配置示例见：

```text
.env.example
```

主要配置项：

```text
BACKEND_HOST=127.0.0.1
BACKEND_PORT=8000
DATABASE_URL=sqlite:///./app.db
REDIS_HOST=127.0.0.1
REDIS_PORT=6379
REDIS_DB=0
REDIS_TASK_QUEUE=customer_service:task_queue
REDIS_KEY_PREFIX=customer_service
VITE_API_BASE_URL=http://127.0.0.1:8000/api
LLM_ENABLE=false
LLM_API_KEY=
LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
LLM_MODEL=qwen-plus
LLM_TIMEOUT_SECONDS=20
```

## 17. 中间件技术亮点

本项目重点展示：

- Redis List 作为轻量消息队列；
- Redis Hash 保存任务状态；
- Redis Hash 保存会话最近状态；
- 后端请求与后台处理解耦；
- Worker 异步消费任务；
- MCP Server 作为 AI 工具调用中间层；
- SQLite 持久化保存完整业务记录。

完整链路目标：

```text
用户提问 -> 后端创建任务 -> Redis 入队 -> Worker 出队 -> MCP 工具处理 -> 数据库保存 -> Redis 更新状态 -> 前端展示回复
```

## 18. 常见问题

### 18.1 redis-cli 命令找不到

Windows winget 安装 Redis 后，可能需要重启终端才能直接使用 `redis-cli`。也可以使用完整路径：

```powershell
& "C:\Program Files\Redis\redis-cli.exe" ping
```

### 18.2 创建会话时报 Redis 连接失败

确认 Redis 服务是否运行：

```powershell
Get-Service Redis
```

如果未运行：

```powershell
Start-Service Redis
```

### 18.3 任务一直是 PENDING

通常表示 Worker 没有启动，或 Worker 没有连接到同一个 Redis 和 SQLite 数据库。正常情况下任务状态会按以下流程变化：

```text
PENDING -> PROCESSING -> SUCCESS / FAILED / TRANSFERRED
```

### 18.4 是否必须配置真实大模型 API

不是必须。默认 `LLM_ENABLE=false`，系统使用规则和模板实现。如果配置了 OpenAI 兼容接口，MCP 工具会使用大模型辅助问题归因、转人工判断和智能回复；如果调用失败，会自动回退到规则和模板。

### 18.5 前端页面打不开

确认前端开发服务器是否启动：

```powershell
cd frontend
npm run dev
```

然后访问：

```text
http://127.0.0.1:5173
```

## 19. 三人分工建议

- 成员 A：后端、数据库、API、Redis 入队；
- 成员 B：MCP Server、Worker、Redis 出队、工具调用日志；
- 成员 C：Vue 前端、演示页面、README 与实验报告整理。

## 20. 课堂演示建议

推荐演示顺序：

1. 打开聊天页 `http://127.0.0.1:5173`；
2. 新建会话并发送“我想退款，怎么处理？”；
3. 观察右侧任务状态面板中的分类、知识库命中、回复和是否转人工；
4. 打开后台页 `http://127.0.0.1:5173/admin`；
5. 说明 Redis List 队列、Redis Hash 状态缓存、Worker 异步消费、MCP 工具调用和 SQLite 持久化；
6. 展示任务列表和 MCP 工具调用日志；
7. 再发送“我已经反馈三次了，没人处理，我要人工客服。”，展示 `TRANSFERRED` 状态和工单创建逻辑。

建议截图：

- 聊天页完整三栏布局；
- 任务状态面板；
- 后台中间件说明卡片；
- Redis 实时状态面板；
- MCP 工具调用日志详情；
- SQLite 统计结果。

## 21. 答辩问题要点

为什么使用 Redis List 而不是 Kafka：

Redis 安装简单、本地运行成本低，`LPUSH` 和 `BRPOP` 已能满足本课程项目的轻量异步队列需求；Kafka 更适合高吞吐日志流和消费者组场景，本项目不需要引入额外复杂度。

为什么需要 Worker：

智能客服处理包含分类、检索、生成回复和工单判断，可能耗时。后端请求只负责保存消息和创建任务，Worker 后台异步处理，能体现请求处理与任务处理解耦。

MCP Server 的作用是什么：

MCP Server 把 AI 相关能力封装为标准工具，包括问题分类、知识库检索、回复生成、转人工判断和工单创建。当前 Worker 为保证课堂演示稳定，直接复用工具函数；后续可以替换为标准 MCP Client 调用。

Redis 和 SQLite 的边界是什么：

Redis 保存队列和最近状态，适合快速读写和任务流转；SQLite 保存会话、消息、任务、工具调用日志和工单，是最终事实记录。
