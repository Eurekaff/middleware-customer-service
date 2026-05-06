# 本地演示指南

## 1. 本地环境要求

建议本地环境如下：

- Python 3.10 或更高版本；
- Node.js 18 或更高版本；
- Redis 6 或更高版本；
- npm；
- 可选：Docker Desktop，用于通过 `docker-compose.yml` 启动 Redis。

## 2. Redis 启动方式

### 2.1 使用 Docker Compose

后续项目根目录将提供 `docker-compose.yml`，只包含 Redis 服务。

```bash
docker compose up -d redis
```

默认 Redis 地址：

```text
localhost:6379
```

### 2.2 使用本地 Redis

如果已安装 Redis，可直接启动：

```bash
redis-server
```

Windows 环境也可以使用 Docker 或 WSL 启动 Redis。

## 3. 后端启动方式

进入后端目录：

```bash
cd backend
```

创建虚拟环境并安装依赖：

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

初始化数据库并启动后端：

```bash
python main.py
```

后端默认地址：

```text
http://localhost:8000
```

健康检查：

```bash
curl http://localhost:8000/api/health
```

## 4. MCP Server 启动方式

进入 MCP Server 目录：

```bash
cd mcp_server
```

安装依赖：

```bash
pip install -r requirements.txt
```

启动服务：

```bash
python server.py
```

说明：课程项目优先保证完整链路可运行。如果 Worker 暂时使用本地封装调用 MCP 工具，仍会保留真实 MCP Server 入口，便于后续替换为标准 MCP 调用。

## 5. Worker 启动方式

进入 Worker 目录：

```bash
cd worker
```

安装依赖：

```bash
pip install -r requirements.txt
```

启动 Worker：

```bash
python worker.py
```

Worker 启动后会阻塞等待 Redis 队列中的任务。收到任务后会使用 `BRPOP` 出队，调用 MCP 工具，保存工具调用日志、机器人回复或工单，并更新任务状态。

## 6. 前端启动方式

进入前端目录：

```bash
cd frontend
```

安装依赖：

```bash
npm install
```

启动开发服务器：

```bash
npm run dev
```

前端默认地址：

```text
http://localhost:5173
```

实际 Vite 配置中固定为：

```text
http://127.0.0.1:5173
```

前端页面包含：

- `/`：聊天页，左侧会话列表，中间聊天窗口，右侧任务状态面板；
- `/admin`：后台演示页，展示中间件说明、Redis 实时状态、SQLite 统计、课堂演示步骤、任务列表和 MCP 工具调用日志。

## 7. 推荐启动顺序

1. 启动 Redis；
2. 启动后端 FastAPI；
3. 启动 MCP Server；
4. 启动 Worker；
5. 启动前端 Vue。

Windows 成员也可以直接使用项目根目录的一键脚本：

```powershell
powershell -ExecutionPolicy Bypass -File scripts\dev.ps1
```

该脚本会完成首次依赖安装并启动 Redis、后端、Worker、MCP Server 和前端。首次创建 `.env` 时，脚本会询问是否启用阿里云百炼大模型：

```text
Enable Alibaba DashScope LLM? (y/N)
```

直接按回车表示不启用大模型，系统使用本地规则和模板，仍可完整演示。输入 `y` 后，脚本会提示输入 DashScope API Key，并自动写入 `.env`。

如果使用 Docker 启动 Redis：

```powershell
powershell -ExecutionPolicy Bypass -File scripts\dev.ps1 -UseDockerRedis
```

停止脚本启动的服务：

```powershell
powershell -ExecutionPolicy Bypass -File scripts\stop.ps1
```

## 8. 演示步骤

1. 打开前端页面；
2. 创建新会话；
3. 输入测试问题；
4. 页面显示用户消息，右侧任务状态面板显示任务处理过程；
5. 观察右侧任务状态从 `PENDING` 变为 `PROCESSING`；
6. Worker 处理完成后，任务状态变为 `SUCCESS` 或 `TRANSFERRED`；
7. 页面刷新并显示“智能客服”回复；
8. 进入后台演示页查看 Redis、Worker、MCP、SQLite 等中间件说明；
9. 查看 Redis 实时状态、SQLite 统计、任务列表和 MCP 工具调用日志；
10. 说明 Redis 队列、状态缓存、Worker 异步处理、MCP 工具封装和 SQLite 持久化的作用。

当前后端和 Worker 已可通过 API 联调。未启动前端时，可以使用 curl 创建会话、发送消息，再通过 `/api/tasks/{task_id}` 和 `/api/admin/tool-logs` 验证处理结果。

## 9. 测试样例

### 样例 1

用户问题：

```text
我买了课程但是一直打不开，应该怎么办？
```

预期分类：技术问题。

预期结果：系统给出网络、浏览器缓存、重新登录等排查建议。

### 样例 2

用户问题：

```text
我想退款，怎么处理？
```

预期分类：售后退款问题。

预期结果：系统给出退款流程说明。

### 样例 3

用户问题：

```text
我已经反馈三次了，没人处理，我要人工客服。
```

预期分类：投诉或转人工。

预期结果：系统建议转人工或创建工单。

### 样例 4

用户问题：

```text
这个产品多少钱，有哪些功能？
```

预期分类：售前咨询。

预期结果：系统给出产品功能和购买建议。

## 10. 验收检查点

- 前端可以提交问题；
- 后端可以创建任务；
- Redis 队列存在任务入队和出队；
- Worker 可以消费任务；
- MCP 工具被调用；
- SQLite 保存聊天记录；
- 前端显示最终回复；
- 后台页显示中间件说明、Redis 实时状态、SQLite 统计、任务和工具日志；
- 文档说明与真实代码一致。

## 11. 当前联调结果

已完成本地联调，验证结果如下：

| 测试问题 | 预期分类 | 实际状态 | 说明 |
| --- | --- | --- | --- |
| 我买了课程但是一直打不开，应该怎么办？ | 技术问题 | SUCCESS | Worker 生成排查建议 |
| 我想退款，怎么处理？ | 售后退款问题 | SUCCESS | Worker 生成退款流程说明 |
| 我已经反馈三次了，没人处理，我要人工客服。 | 投诉或转人工 | TRANSFERRED | Worker 创建工单 |
| 这个产品多少钱，有哪些功能？ | 售前咨询 | SUCCESS | Worker 生成售前咨询回复 |
| 你好 | 问候闲聊 | SUCCESS | Worker 生成接待问候 |
| 介绍一下课程套餐 | 商品咨询 | SUCCESS | Worker 生成商品咨询回复 |
| 11 | 无效输入 | SUCCESS | Worker 引导用户补充具体问题 |

本次联调中，Redis 队列最终长度为 `0`，SQLite 能保存会话、消息、任务、工单和 MCP 工具调用日志；后台演示页可以展示 Redis 与 SQLite 的实时统计。

说明：当前 Worker 为保证课程演示稳定，直接复用 MCP 工具函数；`mcp_server/server.py` 保留真实 MCP Server 入口，后续可替换为标准 MCP Client 调用。MCP Server 使用 stdio 协议，后台无客户端连接时可能直接退出，交互式运行或由 MCP Client 拉起时可正常作为工具服务入口。

## 12. 截图建议

实验报告建议保留以下截图：

- 聊天页三栏布局；
- 技术问题处理成功结果；
- 退款问题处理成功结果；
- 投诉或转人工问题的 `TRANSFERRED` 状态；
- 后台中间件说明卡片；
- Redis 实时状态面板；
- SQLite 统计面板；
- MCP 工具调用日志详情。

## 13. 答辩说明重点

答辩时建议重点说明：

- Redis List 如何实现轻量任务队列；
- Redis Hash 如何缓存任务状态和会话状态；
- Worker 为什么可以避免后端请求阻塞；
- MCP Server 为什么适合作为 AI 工具调用中间层；
- SQLite 为什么保存完整业务数据；
- 大模型只是增强能力，规则和模板兜底保证本地可运行；
- 当前简化点包括无复杂权限、无死信队列、无 WebSocket 推送和无向量数据库。
