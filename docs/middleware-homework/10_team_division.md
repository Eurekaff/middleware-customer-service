# 三人分工与联调计划

## 1. 分工原则

本项目按“后端与数据库”“中间件与 Worker/MCP”“前端与文档演示”三个方向分工。每位成员负责一个主要模块，同时参与最终联调和答辩准备。

## 2. 成员 A：后端与数据库

### 2.1 负责模块

- FastAPI 后端；
- SQLAlchemy 模型；
- SQLite 数据库初始化；
- 会话、消息、任务、工具日志 API；
- Redis 入队和任务状态写入。

### 2.2 交付物

- `backend/main.py`；
- `backend/app/` 后端代码；
- `backend/requirements.txt`；
- 数据库表结构；
- 后端 API 测试命令。

### 2.3 验收标准

- 后端可以启动；
- `/api/health` 返回正常；
- 可以创建会话；
- 可以发送消息并返回 `task_id`；
- Redis 中可以看到任务状态和队列数据；
- SQLite 中可以看到会话、消息、任务、工单和工具调用日志记录；
- `/api/admin/middleware-status` 可以返回 Redis 与 SQLite 演示状态。

## 3. 成员 B：中间件、Worker 与 MCP

### 3.1 负责模块

- Redis 队列消费；
- Worker 异步任务处理；
- MCP Server 工具；
- MCP 工具调用封装；
- 工具调用日志保存；
- 工单创建逻辑。

### 3.2 交付物

- `worker/worker.py`；
- `worker/services/`；
- `mcp_server/server.py`；
- `mcp_server/tools/`；
- `mcp_server/requirements.txt`；
- Worker 和 MCP 工具测试说明。

### 3.3 验收标准

- Worker 可以连接 Redis；
- Worker 可以使用 `BRPOP` 消费任务；
- Worker 可以调用分类、检索、回复、工单和转人工工具；
- 工具调用日志可以写入数据库；
- 任务最终状态可以更新为 `SUCCESS`、`FAILED` 或 `TRANSFERRED`。

## 4. 成员 C：前端与文档演示

### 4.1 负责模块

- Vue 3 前端；
- 会话列表页面；
- 聊天页面；
- 任务状态面板；
- 后台中间件演示页；
- README 和实验报告材料整理。

### 4.2 交付物

- `frontend/package.json`；
- `frontend/src/` 前端代码；
- 根目录 `README.md`；
- `docs/middleware-homework/` 文档更新；
- 演示截图和答辩材料。

### 4.3 验收标准

- 前端可以启动；
- 可以创建会话并发送消息；
- 右侧任务面板可以显示任务状态、分类、知识库命中和处理结果；
- 任务完成后显示“智能客服”回复；
- 后台页可以查看中间件说明、Redis 实时状态、SQLite 统计、任务列表和 MCP 工具调用日志；
- 文档中的运行命令与实际代码一致。

## 5. 联调计划

### 5.1 第一轮联调

目标：验证后端、SQLite 和 Redis 入队。

步骤：

1. 启动 Redis；
2. 启动后端；
3. 调用创建会话 API；
4. 调用发送消息 API；
5. 检查 Redis 队列和 SQLite 任务表。

### 5.2 第二轮联调

目标：验证 Worker 和 MCP 工具。

步骤：

1. 启动 Redis；
2. 启动后端；
3. 启动 MCP Server；
4. 启动 Worker；
5. 发送测试问题；
6. 检查任务状态、机器人回复和工具调用日志。

### 5.3 第三轮联调

目标：验证前端完整演示链路。

步骤：

1. 按顺序启动 Redis、后端、MCP Server、Worker 和前端；
2. 在前端创建会话；
3. 输入四组测试问题；
4. 观察任务状态变化；
5. 查看后台演示页；
6. 整理截图和答辩说明。

## 6. 最终验收标准

最终验收以完整链路是否跑通为核心：

```text
用户提问 -> 后端创建任务 -> Redis 入队 -> Worker 出队 -> MCP 工具处理 -> 数据库保存 -> Redis 更新状态 -> 前端展示回复
```

具体标准如下：

- 所有服务可以本地启动；
- Redis 队列和状态缓存可观察；
- SQLite 保存会话、消息、任务、工具调用日志和工单；
- 前端能展示用户问题、任务状态和最终回复；
- 后台页能展示 Redis、Worker、MCP、SQLite、前后端轮询说明以及实时状态；
- 文档能解释系统架构、中间件设计和 MCP 工具设计；
- 答辩时能说明为什么选择 Redis List、为什么引入 Worker、为什么使用 MCP Server。

## 7. 最终交付材料

最终提交时应包含：

- 完整源码；
- 根目录 `README.md`；
- `docs/middleware-homework/` 下的课程设计文档；
- `.env.example` 配置示例；
- `scripts/` 一键配置、启动和停止脚本；
- `docker-compose.yml` 中的 Redis 服务；
- 前端聊天页和后台演示页截图；
- 实验报告正文或报告初稿；
- 答辩 PPT。
