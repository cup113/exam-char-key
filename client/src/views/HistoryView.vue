<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useAuthStore } from '@/stores/auth'
import LoginButtons from '@/components/LoginButtons.vue'
import DictDisplay from '@/components/DictDisplay.vue'
import type { ECHistoryEntry } from '@/types'

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
const searchQuery = ref('')
const expandedId = ref<number | null>(null)

// --- Checkbox & range selection ---
const toggledIds = ref<Set<number>>(new Set())
const autoCheckedIds = ref<Set<number>>(new Set())
const checkedIds = ref<Set<number>>(new Set())

const filteredRecords = computed(() => {
  if (!searchQuery.value.trim()) return records.value
  const q = searchQuery.value.trim().toLowerCase()
  return records.value.filter(r => r.word.includes(q))
})

const selectedCount = computed(() => checkedIds.value.size)

function recalculateChecked() {
  const filtered = filteredRecords.value
  const manual = [...toggledIds.value].filter(id => filtered.some(r => r.id === id))

  if (manual.length >= 2) {
    const indices = manual.map(id => filtered.findIndex(r => r.id === id)).sort((a, b) => a - b)
    const minIdx = indices[0]!
    const maxIdx = indices[indices.length - 1]!

    const newChecked = new Set(manual)
    const newAuto = new Set<number>()
    for (let i = minIdx + 1; i < maxIdx; i++) {
      const r = filtered[i]
      if (r && !newChecked.has(r.id)) {
        newChecked.add(r.id)
        newAuto.add(r.id)
      }
    }

    checkedIds.value = newChecked
    autoCheckedIds.value = newAuto
  } else {
    checkedIds.value = new Set(manual)
    autoCheckedIds.value = new Set()
  }
}

function handleCheck(id: number) {
  if (checkedIds.value.has(id)) {
    if (autoCheckedIds.value.has(id)) {
      const newChecked = new Set(toggledIds.value)
      checkedIds.value = newChecked
      autoCheckedIds.value = new Set()
    } else {
      const newToggled = new Set(toggledIds.value)
      newToggled.delete(id)
      toggledIds.value = newToggled
      recalculateChecked()
    }
  } else {
    const newToggled = new Set(toggledIds.value)
    newToggled.add(id)
    toggledIds.value = newToggled
    recalculateChecked()
  }
}

watch(searchQuery, () => {
  toggledIds.value = new Set()
  autoCheckedIds.value = new Set()
  checkedIds.value = new Set()
})

// --- Migration ---
const legacyData = ref<ECHistoryEntry[] | null>(null)
const migrating = ref(false)
const migrateDone = ref(false)
const migrateError = ref('')

function detectLegacyData() {
  try {
    const raw = localStorage.getItem('EC_history')
    if (raw) {
      const parsed = JSON.parse(raw)
      if (Array.isArray(parsed) && parsed.length > 0) {
        legacyData.value = parsed
      }
    }
  } catch { /* ignore */ }
}

async function handleMigrate() {
  if (!legacyData.value) return
  migrating.value = true
  migrateError.value = ''
  try {
    const res = await fetch('/api/migrate', {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ entries: legacyData.value }),
    })
    if (!res.ok) {
      const err = await res.json()
      throw new Error(err.detail || '迁移失败')
    }
    localStorage.removeItem('EC_history')
    legacyData.value = null
    migrateDone.value = true
  } catch (e: any) {
    migrateError.value = e.message
  } finally {
    migrating.value = false
  }
}

// --- Export ---
const exporting = ref(false)
const exportError = ref('')

async function handleExport(format: 'json' | 'word' | 'apkg', scope: 'selected' | 'all') {
  exporting.value = true
  exportError.value = ''
  try {
    const body: Record<string, any> = { format }
    if (scope === 'selected' && selectedCount.value > 0) {
      body.ids = [...checkedIds.value]
    }
    const res = await fetch('/api/export', {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })
    if (!res.ok) {
      const err = await res.json()
      throw new Error(err.detail || '导出失败')
    }
    const blob = await res.blob()
    const disposition = res.headers.get('Content-Disposition') || ''
    const match = disposition.match(/filename="?(.+?)"?$/)
    const filename = match?.[1] ?? `学习记录.${format === 'json' ? 'json' : (format === 'word' ? 'docx' : 'apkg')}`
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    a.click()
    URL.revokeObjectURL(url)
  } catch (e: any) {
    exportError.value = e.message
  } finally {
    exporting.value = false
  }
}

// --- Delete ---
const deleteError = ref('')

async function handleDelete(id: number) {
  if (!confirm('确定删除这条记录？')) return
  try {
    const res = await fetch(`/api/history/${id}`, { method: 'DELETE', credentials: 'include' })
    if (!res.ok) throw new Error('删除失败')
    records.value = records.value.filter(r => r.id !== id)
    toggledIds.value.delete(id)
    autoCheckedIds.value.delete(id)
    checkedIds.value.delete(id)
  } catch {
    deleteError.value = '删除失败'
  }
}

async function handleBatchDelete() {
  if (selectedCount.value === 0) return
  if (!confirm(`确定删除选中的 ${selectedCount.value} 条记录？`)) return
  try {
    const res = await fetch('/api/history/delete', {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ids: [...checkedIds.value] }),
    })
    if (!res.ok) throw new Error('批量删除失败')
    records.value = records.value.filter(r => !checkedIds.value.has(r.id))
    toggledIds.value = new Set()
    autoCheckedIds.value = new Set()
    checkedIds.value = new Set()
  } catch {
    deleteError.value = '批量删除失败'
  }
}

// --- Lifecycle ---
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
  } catch { /* ignore */ }
  loading.value = false
  detectLegacyData()
})

function toggleExpand(id: number) {
  expandedId.value = expandedId.value === id ? null : id
}

function formatTime(iso: string) {
  return iso.replace('T', ' ').slice(0, 16)
}
</script>

<template>
  <div class="max-w-2xl mx-auto p-10 pt-20">
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-bold">历史记录</h1>
      <input v-model="searchQuery" type="text" placeholder="搜索词语…"
        class="w-44 px-3 py-1.5 text-sm border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-900 text-gray-800 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none focus:ring-1 focus:ring-blue-300" />
    </div>

    <div v-if="loading" class="text-gray-400 dark:text-gray-500">加载中...</div>

    <div v-if="!loading && !auth.user.logged_in" class="text-center text-gray-400 dark:text-gray-500 py-20">
      <p class="mb-4">请先登录</p>
      <div class="flex gap-3 justify-center">
        <LoginButtons size="md" />
      </div>
    </div>

    <template v-if="!loading && auth.user.logged_in">
      <!-- Legacy data migration -->
      <div v-if="legacyData && !migrateDone"
        class="mb-4 px-4 py-3 bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-800 rounded-lg text-sm flex items-center justify-between gap-3">
        <span>📦 检测到旧版数据 ({{ legacyData.length }} 条)</span>
        <button @click="handleMigrate" :disabled="migrating"
          class="shrink-0 px-3 py-1 bg-amber-600 text-white rounded text-sm hover:bg-amber-500 disabled:opacity-50 transition-colors">
          {{ migrating ? '迁移中...' : '迁移到服务器' }}
        </button>
      </div>
      <p v-if="migrateDone" class="mb-4 text-sm text-green-600 dark:text-green-400">✅ 迁移完成</p>
      <p v-if="migrateError" class="mb-4 text-sm text-red-500">❌ {{ migrateError }}</p>

      <!-- Stats -->
      <div v-if="records.length > 0" class="mb-3 text-sm text-gray-500 dark:text-gray-400">
        <span>共 {{ records.length }} 条记录</span>
        <span v-if="selectedCount > 0">，已选中 {{ selectedCount }} 条</span>
      </div>
      <div v-if="selectedCount > 0" class="mb-3 text-xs text-gray-400 dark:text-gray-500">
        💡 选中首尾两条可自动选取中间所有记录
      </div>

      <!-- Empty state -->
      <div v-if="records.length === 0" class="text-center text-gray-400 dark:text-gray-500 py-20">
        暂无保存记录。在阅读页面查询词语后，可以保存答案到历史。
      </div>

      <!-- Record list -->
      <div class="space-y-2">
        <div v-for="r in filteredRecords" :key="r.id"
          class="bg-white dark:bg-[#1a1b23] rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden transition-shadow hover:shadow-sm dark:hover:shadow-gray-900/50">
          <div class="flex items-center gap-2 px-4 py-3">
            <input type="checkbox" :checked="checkedIds.has(r.id)" @change="handleCheck(r.id)"
              class="shrink-0 w-4 h-4 rounded border-gray-300 dark:border-gray-600 text-blue-600 focus:ring-blue-500 cursor-pointer" />
            <div class="flex items-center gap-2 min-w-0 flex-1 cursor-pointer" @click="toggleExpand(r.id)">
              <span class="text-lg font-bold text-blue-700 dark:text-blue-400 shrink-0">「{{ r.word }}」</span>
              <span class="text-xs text-gray-400 dark:text-gray-500 bg-gray-100 dark:bg-gray-800 px-1.5 py-0.5 rounded shrink-0">
                {{ r.mode === 'deep' ? '深度' : '快速' }}
              </span>
              <span class="text-xs text-gray-400 dark:text-gray-500 shrink-0">{{ formatTime(r.created_at) }}</span>
            </div>
            <div class="flex items-center gap-1 shrink-0">
              <button @click="toggleExpand(r.id)" class="px-2 py-1 text-xs text-gray-400 dark:text-gray-500 hover:text-gray-700 dark:hover:text-gray-200" data-umami-event="history-item-toggle">
                {{ expandedId === r.id ? '收起' : '展开' }}
              </button>
              <button @click="handleDelete(r.id)" class="px-2 py-1 text-xs text-red-400 dark:text-red-500 hover:text-red-600 dark:hover:text-red-400" title="删除">🗑</button>
            </div>
          </div>
          <div v-if="expandedId === r.id" class="px-4 pb-4 border-t border-gray-100 dark:border-gray-800 pt-3 space-y-2">
            <div v-if="r.quick_answer" class="p-2.5 bg-blue-50 dark:bg-blue-950/30 rounded-lg">
              <h4 class="text-xs font-bold text-blue-700 dark:text-blue-400 mb-0.5">⚡ 快速回答</h4>
              <p class="text-sm whitespace-pre-wrap">{{ r.quick_answer }}</p>
            </div>
            <div v-if="r.dict_result" class="p-2.5 bg-emerald-50 dark:bg-emerald-950/30 rounded-lg">
              <h4 class="text-xs font-bold text-emerald-700 dark:text-emerald-400 mb-0.5">📖 汉典释义</h4>
              <DictDisplay :dict-result="r.dict_result" />
            </div>
            <div v-if="r.deep_think" class="p-2.5 bg-purple-50 dark:bg-purple-950/30 rounded-lg">
              <h4 class="text-xs font-bold text-purple-700 dark:text-purple-400 mb-0.5">🧠 深度分析</h4>
              <p class="text-sm whitespace-pre-wrap">{{ r.deep_think }}</p>
            </div>
            <div v-if="r.context" class="text-xs text-gray-400 dark:text-gray-500 italic">
              语境：{{ r.context.slice(0, 120) }}{{ r.context.length > 120 ? '...' : '' }}
            </div>
          </div>
        </div>
      </div>

      <!-- No results for search -->
      <div v-if="records.length > 0 && filteredRecords.length === 0" class="text-center text-gray-400 dark:text-gray-500 py-10">
        无匹配记录
      </div>

      <!-- Action bar -->
      <div v-if="records.length > 0" class="mt-6 pt-4 border-t border-gray-200 dark:border-gray-700">
        <div class="flex items-center gap-2 flex-wrap">
          <template v-if="selectedCount > 0">
            <span class="text-sm text-gray-500 dark:text-gray-400 mr-1">导出选中:</span>
            <button @click="handleExport('json', 'selected')" :disabled="exporting"
              class="px-3 py-1.5 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-500 disabled:opacity-50 transition-colors">JSON</button>
            <button @click="handleExport('word', 'selected')" :disabled="exporting"
              class="px-3 py-1.5 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-500 disabled:opacity-50 transition-colors">Word</button>
            <button @click="handleExport('apkg', 'selected')" :disabled="exporting"
              class="px-3 py-1.5 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-500 disabled:opacity-50 transition-colors">Anki</button>
            <span class="mx-2 text-gray-300 dark:text-gray-600">|</span>
            <button @click="handleBatchDelete"
              class="px-3 py-1.5 text-sm text-red-600 dark:text-red-400 border border-red-200 dark:border-red-800 rounded-lg hover:bg-red-50 dark:hover:bg-red-950/30 transition-colors">
              批量删除
            </button>
          </template>
          <span class="text-sm text-gray-500 dark:text-gray-400 mr-1">导出全部:</span>
          <button @click="handleExport('json', 'all')" :disabled="exporting"
            class="px-3 py-1.5 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-500 disabled:opacity-50 transition-colors">JSON</button>
          <button @click="handleExport('word', 'all')" :disabled="exporting"
            class="px-3 py-1.5 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-500 disabled:opacity-50 transition-colors">Word</button>
          <button @click="handleExport('apkg', 'all')" :disabled="exporting"
            class="px-3 py-1.5 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-500 disabled:opacity-50 transition-colors">Anki</button>
        </div>
        <p v-if="exporting" class="text-gray-400 dark:text-gray-500 text-xs mt-2">导出中...</p>
        <p v-if="exportError" class="text-red-500 text-sm mt-2">❌ {{ exportError }}</p>
        <p v-if="deleteError" class="text-red-500 text-sm mt-2">❌ {{ deleteError }}</p>
      </div>
    </template>
  </div>
</template>
