<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  deepThink: string
}>()

const contextText = computed(() => {
  for (const line of props.deepThink.split('\n')) {
    const trimmed = line.trim()
    const match = trimmed.match(/^\[解释\]\s*(.*)$/)
    if (match) return match[1]
  }
  return ''
})

const hasMarkers = computed(() =>
  /^\[(解释|词义)\]/.test(props.deepThink.trim())
)

const fallbackText = computed(() => {
  if (hasMarkers.value) return ''
  return props.deepThink
})
</script>

<template>
  <div v-if="contextText" class="rounded-xl border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900 px-4 py-3">
    <p class="text-xs text-gray-500 dark:text-gray-400 mb-1">📝 语境分析</p>
    <p class="text-sm leading-relaxed text-gray-700 dark:text-gray-200 whitespace-pre-wrap">{{ contextText }}</p>
  </div>
  <div v-else-if="fallbackText" class="rounded-xl border border-purple-100 dark:border-purple-900 bg-purple-50 dark:bg-purple-950/30 px-4 py-3">
    <p class="text-sm leading-relaxed whitespace-pre-wrap">{{ fallbackText }}</p>
  </div>
</template>
