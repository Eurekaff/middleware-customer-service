import axios from 'axios'

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api',
  timeout: 10000,
})

export async function createSession(title = '新建会话') {
  const response = await api.post('/sessions', { title })
  return response.data
}

export async function listSessions() {
  const response = await api.get('/sessions')
  return response.data
}

export async function getSession(sessionId) {
  const response = await api.get(`/sessions/${sessionId}`)
  return response.data
}

export async function updateSessionStatus(sessionId, status) {
  const response = await api.patch(`/sessions/${sessionId}/status`, { status })
  return response.data
}

export async function deleteSession(sessionId) {
  const response = await api.delete(`/sessions/${sessionId}`)
  return response.data
}

export async function sendMessage(sessionId, content) {
  const response = await api.post(`/sessions/${sessionId}/messages`, { content })
  return response.data
}

export async function getTask(taskId) {
  const response = await api.get(`/tasks/${taskId}`)
  return response.data
}

export async function listAdminTasks() {
  const response = await api.get('/admin/tasks')
  return response.data
}

export async function listToolLogs() {
  const response = await api.get('/admin/tool-logs')
  return response.data
}

export async function getMiddlewareStatus() {
  const response = await api.get('/admin/middleware-status')
  return response.data
}
