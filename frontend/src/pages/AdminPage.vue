<template>
  <main class="admin-shell">
    <header class="admin-header">
      <div>
        <p class="eyebrow">课堂演示后台</p>
        <h1>中间件工作流演示控制台</h1>
      </div>
      <div class="admin-actions">
        <RouterLink class="ghost-button" to="/">返回聊天页</RouterLink>
        <button class="primary-button" type="button" @click="loadData">刷新</button>
      </div>
    </header>

    <section class="middleware-grid">
      <article v-for="item in middlewareCards" :key="item.name" class="middleware-card">
        <div class="middleware-card-head">
          <span>{{ item.badge }}</span>
          <strong>{{ item.name }}</strong>
        </div>
        <p>{{ item.role }}</p>
        <dl>
          <div>
            <dt>演示点</dt>
            <dd>{{ item.demo }}</dd>
          </div>
          <div>
            <dt>当前状态</dt>
            <dd>{{ item.status }}</dd>
          </div>
        </dl>
      </article>
    </section>

    <section class="admin-demo-grid">
      <article class="admin-card">
        <div class="panel-head">
          <h2>Redis 实时状态</h2>
          <StatusBadge :status="middlewareStatus?.redis?.connected ? 'SUCCESS' : 'FAILED'" />
        </div>
        <div v-if="middlewareStatus" class="middleware-state">
          <div class="state-row">
            <span>任务队列 Key</span>
            <strong class="mono">{{ middlewareStatus.redis.queue_name }}</strong>
          </div>
          <div class="state-row">
            <span>队列长度</span>
            <strong>{{ middlewareStatus.redis.queue_length }}</strong>
          </div>
          <div class="state-row">
            <span>任务状态缓存</span>
            <strong>{{ middlewareStatus.redis.task_cache_keys.length }} 个 key</strong>
          </div>
          <div class="state-row">
            <span>会话状态缓存</span>
            <strong>{{ middlewareStatus.redis.session_cache_keys.length }} 个 key</strong>
          </div>
          <details>
            <summary>查看 Redis Key 示例</summary>
            <pre>{{ pretty(middlewareStatus.redis) }}</pre>
          </details>
        </div>
        <p v-else class="empty-panel">点击刷新后查看 Redis 队列和缓存状态。</p>
      </article>

      <article class="admin-card">
        <div class="panel-head">
          <h2>SQLite 持久化统计</h2>
          <span>数据库落库结果</span>
        </div>
        <div v-if="middlewareStatus" class="stat-grid">
          <div>
            <strong>{{ middlewareStatus.sqlite.sessions }}</strong>
            <span>会话</span>
          </div>
          <div>
            <strong>{{ middlewareStatus.sqlite.messages }}</strong>
            <span>消息</span>
          </div>
          <div>
            <strong>{{ middlewareStatus.sqlite.tasks }}</strong>
            <span>任务</span>
          </div>
          <div>
            <strong>{{ middlewareStatus.sqlite.tool_logs }}</strong>
            <span>工具日志</span>
          </div>
          <div>
            <strong>{{ middlewareStatus.sqlite.tickets }}</strong>
            <span>工单</span>
          </div>
        </div>
      </article>

      <article class="admin-card demo-steps">
        <div class="panel-head">
          <h2>课堂演示步骤</h2>
          <span>从聊天页触发</span>
        </div>
        <ol>
          <li>聊天页输入问题，后端创建 PENDING 任务。</li>
          <li>观察 Redis List 队列长度变化。</li>
          <li>Worker 使用 BRPOP 取出任务并改为 PROCESSING。</li>
          <li>MCP 工具依次完成分类、知识库检索、回复生成和转人工判断。</li>
          <li>刷新后台，查看任务状态、SQLite 统计和工具调用日志。</li>
        </ol>
      </article>
    </section>

    <section class="admin-grid">
      <div class="admin-card">
        <div class="panel-head">
          <h2>任务列表</h2>
          <span>{{ tasks.length }} 条</span>
        </div>
        <div class="table-wrap">
          <table>
            <thead>
              <tr>
                <th>task_id</th>
                <th>状态</th>
                <th>分类</th>
                <th>结果摘要</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="task in tasks" :key="task.task_id">
                <td class="mono">{{ task.task_id }}</td>
                <td><StatusBadge :status="task.status" /></td>
                <td>{{ task.category || '-' }}</td>
                <td>{{ task.result || '-' }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <div class="admin-card">
        <div class="panel-head">
          <h2>MCP 工具调用日志</h2>
          <span>{{ logs.length }} 条</span>
        </div>
        <div class="log-list">
          <article v-for="log in logs" :key="log.id" class="log-item">
            <div>
              <strong>{{ log.tool_name }}</strong>
              <StatusBadge :status="log.success ? 'SUCCESS' : 'FAILED'" />
            </div>
            <p class="mono">task: {{ log.task_id }}</p>
            <details>
              <summary>查看输入输出</summary>
              <pre>{{ pretty(log.input_json) }}</pre>
              <pre>{{ pretty(log.output_json) }}</pre>
              <pre v-if="log.error_message">{{ log.error_message }}</pre>
            </details>
          </article>
        </div>
      </div>
    </section>
  </main>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import StatusBadge from '../components/StatusBadge.vue'
import { getMiddlewareStatus, listAdminTasks, listToolLogs } from '../api/client'

const tasks = ref([])
const logs = ref([])
const middlewareStatus = ref(null)

const middlewareCards = computed(() => [
  {
    badge: 'Redis List',
    name: '轻量消息队列',
    role: '作为 FastAPI 与 Worker 之间的任务缓冲层。',
    demo: '用户发送消息后写入 customer_service:task_queue，Worker 使用 BRPOP 阻塞消费。',
    status: middlewareStatus.value
      ? `${middlewareStatus.value.redis.queue_length} 个待处理任务`
      : '等待刷新',
  },
  {
    badge: 'Redis Hash',
    name: '任务与会话状态缓存',
    role: '缓存任务状态和会话最近状态，支持前端快速轮询。',
    demo: '查看 customer_service:task:{task_id} 和 customer_service:session:{session_id}。',
    status: middlewareStatus.value
      ? `${middlewareStatus.value.redis.task_cache_keys.length} 个任务缓存，${middlewareStatus.value.redis.session_cache_keys.length} 个会话缓存`
      : '等待刷新',
  },
  {
    badge: 'Worker',
    name: '异步任务消费者',
    role: '从 Redis 队列读取任务，避免聊天请求阻塞在 AI 处理阶段。',
    demo: '观察任务状态从 PENDING 到 PROCESSING，再到 SUCCESS / TRANSFERRED。',
    status: tasks.value.length ? `${tasks.value.length} 条任务可查看` : '暂无任务',
  },
  {
    badge: 'MCP',
    name: 'AI 工具调用中间层',
    role: '统一封装问题分类、知识库检索、回复生成和工单创建工具。',
    demo: '后台日志展示每次工具调用的输入、输出和是否成功。',
    status: logs.value.length ? `${logs.value.length} 条工具日志` : '暂无日志',
  },
  {
    badge: 'SQLite',
    name: '业务数据持久化',
    role: '保存会话、消息、任务、工具调用日志和工单。',
    demo: '刷新后查看 SQLite 统计数量随聊天处理增加。',
    status: middlewareStatus.value
      ? `${middlewareStatus.value.sqlite.messages} 条消息，${middlewareStatus.value.sqlite.tool_logs} 条日志`
      : '等待刷新',
  },
  {
    badge: 'Axios Polling',
    name: '前后端分离轮询',
    role: '前端发送消息后立即拿到 task_id，再轮询任务状态。',
    demo: '聊天页右侧任务面板展示分类、知识库命中、回复和转人工结果。',
    status: 'GET /api/tasks/{task_id}',
  },
])

onMounted(loadData)

async function loadData() {
  const [taskData, logData, statusData] = await Promise.all([
    listAdminTasks(),
    listToolLogs(),
    getMiddlewareStatus(),
  ])
  tasks.value = taskData
  logs.value = logData
  middlewareStatus.value = statusData
}

function pretty(value) {
  if (!value) return '-'
  try {
    return JSON.stringify(typeof value === 'string' ? JSON.parse(value) : value, null, 2)
  } catch {
    return value
  }
}
</script>
