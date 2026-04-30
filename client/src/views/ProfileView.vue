<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import type { ECHistoryEntry } from '@/types'

const auth = useAuthStore()

const legacyData = ref<ECHistoryEntry[] | null>(null)
const migrating = ref(false)
const migrateDone = ref(false)
const migrateError = ref('')

const exporting = ref(false)
const exportError = ref('')

onMounted(async () => {
  await auth.fetchUser()
  auth.fetchQuota()
  detectLegacyData()
})

function detectLegacyData() {
  try {
    const raw = localStorage.getItem('EC_history')
    if (raw) {
      const parsed = JSON.parse(raw)
      if (Array.isArray(parsed) && parsed.length > 0) {
        legacyData.value = parsed
      }
    }
  } catch {
    // ignore malformed data
  }
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

async function handleExport(format: 'json' | 'word' | 'apkg') {
  exporting.value = true
  exportError.value = ''
  try {
    const res = await fetch('/api/export', {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ format }),
    })
    if (!res.ok) {
      const err = await res.json()
      throw new Error(err.detail || '导出失败')
    }
    const blob = await res.blob()
    const disposition = res.headers.get('Content-Disposition') || ''
    const match = disposition.match(/filename="?(.+?)"?$/)
    const filename = match ? match[1] : `学习记录.${format === 'json' ? 'json' : (format === 'word' ? 'docx' : 'apkg')}`
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
</script>

<template>
  <div class="max-w-xl mx-auto p-10 pt-20">
    <h1 class="text-2xl font-bold mb-6">个人管理</h1>

    <div v-if="auth.quotaLoading" class="text-gray-400">加载中...</div>

    <template v-if="!auth.quotaLoading && auth.user.logged_in">
      <section class="bg-white rounded-xl border border-gray-200 p-6 mb-6">
        <h2 class="text-sm font-bold text-gray-500 uppercase tracking-wide mb-4">账号信息</h2>
        <div class="space-y-3">
          <div class="flex justify-between">
            <span class="text-gray-500">用户 ID</span>
            <span class="font-mono text-sm">{{ auth.user.user_id }}</span>
          </div>
          <div class="flex justify-between">
            <span class="text-gray-500">登录方式</span>
            <span class="capitalize">{{ auth.user.provider }}</span>
          </div>
        </div>
      </section>

      <section v-if="legacyData" class="bg-white rounded-xl border border-amber-200 p-6 mb-6">
        <h2 class="text-sm font-bold text-amber-700 uppercase tracking-wide mb-4">📦 旧版数据迁移</h2>
        <p class="text-sm text-gray-600 mb-4">
          检测到 {{ legacyData.length }} 条旧版数据（EC_history），迁移到服务器后可进行导出等操作。
        </p>
        <button v-if="!migrateDone" @click="handleMigrate" :disabled="migrating"
          class="px-4 py-2 bg-amber-600 text-white rounded-lg text-sm hover:bg-amber-500 disabled:opacity-50 transition-colors">
          {{ migrating ? '迁移中...' : '迁移到服务器' }}
        </button>
        <p v-if="migrateDone" class="text-green-600 text-sm">✅ 迁移完成</p>
        <p v-if="migrateError" class="text-red-500 text-sm mt-2">❌ {{ migrateError }}</p>
      </section>

      <section class="bg-white rounded-xl border border-gray-200 p-6 mb-6">
        <h2 class="text-sm font-bold text-gray-500 uppercase tracking-wide mb-4">📤 数据导出</h2>
        <p class="text-sm text-gray-600 mb-4">
          将历史记录导出为指定格式。
        </p>
        <div class="flex gap-3">
          <button @click="handleExport('json')" :disabled="exporting"
            class="flex-1 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-500 disabled:opacity-50 transition-colors">
            JSON
          </button>
          <button @click="handleExport('word')" :disabled="exporting"
            class="flex-1 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-500 disabled:opacity-50 transition-colors">
            Word
          </button>
          <button @click="handleExport('apkg')" :disabled="exporting"
            class="flex-1 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-500 disabled:opacity-50 transition-colors">
            Anki
          </button>
        </div>
        <p v-if="exporting" class="text-gray-400 text-xs mt-2">导出中...</p>
        <p v-if="exportError" class="text-red-500 text-sm mt-2">❌ {{ exportError }}</p>
      </section>

      <section class="bg-white rounded-xl border border-gray-200 p-6">
        <h2 class="text-sm font-bold text-gray-500 uppercase tracking-wide mb-4">今日额度</h2>
        <div v-if="auth.quota" class="space-y-3">
          <div class="flex justify-between">
            <span class="text-gray-500">已用</span>
            <span>{{ auth.quota.used }} 次</span>
          </div>
          <div class="flex justify-between">
            <span class="text-gray-500">每日上限</span>
            <span>{{ auth.quota.limit }} 次</span>
          </div>
          <div class="flex justify-between font-medium">
            <span class="text-gray-500">剩余</span>
            <span :class="auth.quota.remaining < 5 ? 'text-red-500' : 'text-green-600'">
              {{ auth.quota.remaining }} 次
            </span>
          </div>
          <div class="w-full bg-gray-100 rounded-full h-2 mt-2">
            <div class="h-2 rounded-full transition-all duration-300"
              :class="auth.quota.remaining < 5 ? 'bg-red-400' : 'bg-blue-400'"
              :style="{ width: (auth.quota.used / auth.quota.limit * 100) + '%' }">
            </div>
          </div>
        </div>
        <p v-else class="text-gray-400 text-sm">获取额度信息失败</p>
      </section>
    </template>

    <div v-if="!auth.quotaLoading && !auth.user.logged_in" class="text-center text-gray-400 py-20">
      <p class="mb-4">请先登录</p>
      <div class="flex gap-3 justify-center">
        <a href="/api/auth/github/login"
          class="px-4 py-2 bg-gray-900 text-white rounded hover:bg-gray-700 text-sm">GitHub 登录</a>
        <a href="/api/auth/gitee/login"
          class="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-500 text-sm">Gitee 登录</a>
      </div>
    </div>
  </div>
</template>
