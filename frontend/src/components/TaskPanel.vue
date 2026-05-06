<template>
  <aside class="task-panel">
    <div class="panel-head">
      <div>
        <p class="eyebrow">当前任务</p>
        <h2>处理状态</h2>
      </div>
      <StatusBadge :status="task?.status || 'IDLE'" />
    </div>

    <div v-if="task" class="task-fields">
      <div class="field">
        <span>task_id</span>
        <strong class="mono">{{ task.task_id }}</strong>
      </div>
      <div class="field">
        <span>分类结果</span>
        <strong>{{ task.category || '等待处理' }}</strong>
      </div>
      <div class="field">
        <span>是否转人工</span>
        <strong>{{ task.transferred ? '是' : '否' }}</strong>
      </div>
      <div class="field">
        <span>工单编号</span>
        <strong>{{ task.ticket_id || '-' }}</strong>
      </div>
      <div class="field large">
        <span>知识库命中</span>
        <ul v-if="knowledgeHits.length">
          <li v-for="hit in knowledgeHits" :key="hit.title">
            <b>{{ hit.title }}</b>
            <p>{{ hit.content }}</p>
          </li>
        </ul>
        <strong v-else>暂无</strong>
      </div>
      <div class="field large">
        <span>处理结果</span>
        <p>{{ task.result || task.error_message || '任务正在等待 Worker 处理' }}</p>
      </div>
    </div>

    <div v-else class="empty-panel">
      发送一条用户消息后，这里会显示 Redis 任务状态、分类、知识库命中和最终回复。
    </div>
  </aside>
</template>

<script setup>
import { computed } from 'vue'
import StatusBadge from './StatusBadge.vue'

const props = defineProps({
  task: {
    type: Object,
    default: null,
  },
})

const knowledgeHits = computed(() => {
  if (!props.task?.knowledge_hit) return []
  return Array.isArray(props.task.knowledge_hit) ? props.task.knowledge_hit : []
})
</script>
