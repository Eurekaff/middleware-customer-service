<template>
  <main class="app-shell">
    <section class="sidebar">
      <div class="brand-block">
        <p class="eyebrow">Middleware Lab</p>
        <h1>智能客服工作流</h1>
      </div>
      <button class="primary-button" type="button" @click="handleCreateSession">新建会话</button>

      <div class="session-list">
        <article
          v-for="item in sessions"
          :key="item.id"
          class="session-item"
          :class="{ active: item.id === currentSession?.id }"
          @click="selectSession(item.id)"
        >
          <div class="session-copy">
            <strong>{{ item.title }}</strong>
            <span>{{ item.last_message || '暂无消息' }}</span>
          </div>
          <div class="session-actions">
            <button class="mini-button" type="button" @click.stop="toggleSessionStatus(item)">
              {{ item.status === 'CLOSED' ? '恢复' : '关闭' }}
            </button>
            <button class="mini-button danger" type="button" @click.stop="handleDeleteSession(item)">
              删除
            </button>
          </div>
        </article>
      </div>

      <RouterLink class="admin-link" to="/admin">后台演示页</RouterLink>
    </section>

    <section class="chat-main">
      <header class="chat-header">
        <div>
          <p class="eyebrow">当前会话</p>
          <h2>{{ currentSession?.title || '未选择会话' }}</h2>
        </div>
        <button class="ghost-button" type="button" @click="refreshAll">刷新</button>
      </header>

      <div class="message-list">
        <div v-if="!messages.length" class="empty-state">
          创建会话后输入问题，系统会展示任务入队、Worker 处理和 MCP 工具调用结果。
        </div>
        <article
          v-for="message in messages"
          :key="message.id"
          class="message"
          :class="message.role === 'USER' ? 'message-user' : 'message-assistant'"
        >
          <span>{{ message.role === 'USER' ? '用户' : '机器人' }}</span>
          <p>{{ message.content }}</p>
          <small v-if="message.task_id" class="mono">task: {{ message.task_id }}</small>
        </article>
      </div>

      <form class="composer" @submit.prevent="handleSend">
        <textarea
          v-model="draft"
          :disabled="!currentSession || currentSession.status === 'CLOSED' || sending"
          rows="3"
          :placeholder="currentSession?.status === 'CLOSED' ? '当前会话已关闭，可恢复后继续发送' : '输入用户问题，例如：我想退款，怎么处理？'"
        />
        <button class="primary-button" type="submit" :disabled="!canSend">
          {{ sending ? '发送中' : '发送' }}
        </button>
      </form>
    </section>

    <TaskPanel :task="currentTask" />
  </main>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import TaskPanel from '../components/TaskPanel.vue'
import {
  createSession,
  deleteSession,
  getSession,
  getTask,
  listSessions,
  sendMessage,
  updateSessionStatus,
} from '../api/client'

const sessions = ref([])
const currentSession = ref(null)
const messages = ref([])
const currentTask = ref(null)
const draft = ref('')
const sending = ref(false)
let pollTimer = null

const canSend = computed(() =>
  Boolean(currentSession.value && currentSession.value.status !== 'CLOSED' && draft.value.trim() && !sending.value),
)

onMounted(async () => {
  await refreshAll()
  if (!sessions.value.length) {
    await handleCreateSession()
  } else {
    await selectSession(sessions.value[0].id)
  }
})

onUnmounted(() => {
  clearPolling()
})

async function refreshAll() {
  sessions.value = await listSessions()
  if (currentSession.value) {
    const exists = sessions.value.some((session) => session.id === currentSession.value.id)
    if (exists) {
      await loadSession(currentSession.value.id)
    } else {
      currentSession.value = null
      messages.value = []
    }
  }
}

async function handleCreateSession() {
  const session = await createSession('新建会话')
  await refreshAll()
  await selectSession(session.id)
}

async function selectSession(sessionId) {
  clearPolling()
  currentTask.value = null
  await loadSession(sessionId)
}

async function toggleSessionStatus(item) {
  const nextStatus = item.status === 'CLOSED' ? 'ACTIVE' : 'CLOSED'
  await updateSessionStatus(item.id, nextStatus)
  await refreshAll()
}

async function handleDeleteSession(item) {
  const confirmed = window.confirm(`确定删除会话“${item.title}”吗？相关消息、任务和工具日志都会删除。`)
  if (!confirmed) return

  const deletingCurrent = currentSession.value?.id === item.id
  await deleteSession(item.id)
  await refreshAll()
  if (deletingCurrent) {
    const next = sessions.value[0]
    if (next) {
      await selectSession(next.id)
    } else {
      await handleCreateSession()
    }
  }
}

async function loadSession(sessionId) {
  currentSession.value = await getSession(sessionId)
  messages.value = currentSession.value.messages || []
}

async function handleSend() {
  if (!canSend.value) return
  sending.value = true
  try {
    const content = draft.value.trim()
    draft.value = ''
    const taskInfo = await sendMessage(currentSession.value.id, content)
    currentTask.value = { ...taskInfo }
    await loadSession(currentSession.value.id)
    startPolling(taskInfo.task_id)
  } finally {
    sending.value = false
  }
}

function startPolling(taskId) {
  clearPolling()
  pollTimer = window.setInterval(async () => {
    const task = await getTask(taskId)
    currentTask.value = task
    if (['SUCCESS', 'FAILED', 'TRANSFERRED'].includes(task.status)) {
      clearPolling()
      await loadSession(task.session_id)
      await refreshAll()
    }
  }, 1000)
}

function clearPolling() {
  if (pollTimer) {
    window.clearInterval(pollTimer)
    pollTimer = null
  }
}
</script>
