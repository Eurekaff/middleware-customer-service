<template>
  <main class="admin-shell">
    <header class="admin-header">
      <div>
        <p class="eyebrow">课堂演示后台</p>
        <h1>任务与 MCP 工具日志</h1>
      </div>
      <div class="admin-actions">
        <RouterLink class="ghost-button" to="/">返回聊天页</RouterLink>
        <button class="primary-button" type="button" @click="loadData">刷新</button>
      </div>
    </header>

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
import { onMounted, ref } from 'vue'
import StatusBadge from '../components/StatusBadge.vue'
import { listAdminTasks, listToolLogs } from '../api/client'

const tasks = ref([])
const logs = ref([])

onMounted(loadData)

async function loadData() {
  const [taskData, logData] = await Promise.all([listAdminTasks(), listToolLogs()])
  tasks.value = taskData
  logs.value = logData
}

function pretty(value) {
  if (!value) return '-'
  try {
    return JSON.stringify(JSON.parse(value), null, 2)
  } catch {
    return value
  }
}
</script>
