<script setup lang="ts">
import DictDisplay from '@/components/DictDisplay.vue'
import { ref, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import LoginButtons from '@/components/LoginButtons.vue'

const auth = useAuthStore()

interface HistoryRecord {
  id: number
  word: string
  context: string
  mode: string
  quick_answer: string
  dict_result: string
  deep_think: string
  created_at: string
}

const records = ref<HistoryRecord[]>([])
const loading = ref(true)
const selectedId = ref<number | null>(null)

onMounted(async () => {
  await auth.fetchUser()
  if (!auth.user.logged_in) {
    loading.value = false
    return
  }
  try {
    const resp = await fetch('/api/history', { credentials: 'include' })
    if (resp.ok) {
      const data = await resp.json()
      records.value = (data.records || []) as HistoryRecord[]
    }
  } catch {
    // ignore
  }
  loading.value = false
})

function toggleExpand(id: number) {
  selectedId.value = selectedId.value === id ? null : id
}

function formatTime(iso: string) {
  return iso.replace('T', ' ').slice(0, 16)
}
</script>

<template>
  <div class="max-w-2xl mx-auto p-10 pt-20">
    <h1 class="text-2xl font-bold mb-6">历史记录</h1>

    <div v-if="loading" class="text-gray-400">加载中...</div>

    <div v-if="!loading && !auth.user.logged_in" class="text-center text-gray-400 py-20">
      <p class="mb-4">请先登录</p>
      <div class="flex gap-3 justify-center">
        <LoginButtons size="md" />
      </div>
    </div>

    <div v-if="!loading && auth.user.logged_in && records.length === 0" class="text-center text-gray-400 py-20">
      暂无保存记录。在阅读页面查询词语后，可以保存答案到历史。
    </div>

    <div v-if="!loading && auth.user.logged_in" class="space-y-3">
      <div v-for="r in records" :key="r.id"
        class="bg-white rounded-xl border border-gray-200 overflow-hidden transition-shadow hover:shadow-sm">
        <div class="flex items-center justify-between px-5 py-3 cursor-pointer" @click="toggleExpand(r.id)" data-umami-event="history-item-toggle">
          <div class="flex items-center gap-3">
            <span class="text-lg font-bold text-blue-700">「{{ r.word }}」</span>
            <span class="text-xs text-gray-400 bg-gray-100 px-2 py-0.5 rounded">
              {{ r.mode === 'deep' ? '深度' : '快速' }}
            </span>
          </div>
          <div class="flex items-center gap-3">
            <span class="text-xs text-gray-400">{{ formatTime(r.created_at) }}</span>
            <span class="text-gray-300 text-sm">{{ selectedId === r.id ? '收起' : '展开' }}</span>
          </div>
        </div>
        <div v-if="selectedId === r.id" class="px-5 pb-4 border-t border-gray-100 pt-3 space-y-3">
          <div v-if="r.quick_answer" class="p-3 bg-blue-50 rounded-lg">
            <h4 class="text-xs font-bold text-blue-700 mb-1">⚡ 快速回答</h4>
            <p class="text-sm whitespace-pre-wrap">{{ r.quick_answer }}</p>
          </div>
          <div v-if="r.dict_result" class="p-3 bg-emerald-50 rounded-lg">
            <h4 class="text-xs font-bold text-emerald-700 mb-1">📖 汉典释义</h4>
            <DictDisplay :dict-result="r.dict_result" />
          </div>
          <div v-if="r.deep_think" class="p-3 bg-purple-50 rounded-lg">
            <h4 class="text-xs font-bold text-purple-700 mb-1">🧠 深度分析</h4>
            <p class="text-sm whitespace-pre-wrap">{{ r.deep_think }}</p>
          </div>
          <div v-if="r.context" class="text-xs text-gray-400 italic">
            语境：{{ r.context.slice(0, 120) }}{{ r.context.length > 120 ? '...' : '' }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
