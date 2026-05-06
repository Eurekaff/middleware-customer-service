<template>
  <span class="status-badge" :class="`status-${statusText.toLowerCase()}`">
    {{ statusText }}
  </span>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  status: {
    type: String,
    default: 'UNKNOWN',
  },
})

const statusText = computed(() => props.status || 'UNKNOWN')
</script>
