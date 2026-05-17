<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import * as adminService from '@/services/adminService'

const router = useRouter()
const auth = useAuthStore()

const importing = ref(false)
const importResult = ref<{ success: boolean; count?: number; filename?: string; error?: string } | null>(null)
const fileInput = ref<HTMLInputElement | null>(null)

onMounted(async () => {
  await auth.fetchUser()
  if (!auth.user.is_admin) {
    router.replace('/')
  }
})

async function handleImport() {
  const file = fileInput.value?.files?.[0]
  if (!file) return

  importing.value = true
  importResult.value = null

  try {
    importResult.value = await adminService.importCorpus(file)
  } catch (e) {
    importResult.value = { success: false, error: String(e) }
  } finally {
    importing.value = false
    if (fileInput.value) fileInput.value.value = ''
  }
}
</script>

<template>
  <div class="max-w-xl mx-auto p-10 pt-20">
    <h1 class="text-2xl font-bold mb-6">管理面板</h1>

    <div v-if="!auth.user.is_admin" class="text-center text-gray-400 py-20">
      无管理员权限
    </div>

    <template v-else>
      <section class="bg-white dark:bg-[#1a1b23] rounded-xl border border-gray-200 dark:border-gray-700 p-6 mb-6">
        <h2 class="text-sm font-bold text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-4">数据管理</h2>
        <p class="text-sm text-gray-600 dark:text-gray-300 mb-3">
          浏览和编辑数据库中的表数据。
        </p>
        <a href="/admin/"
          class="inline-block px-4 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-500 transition-colors"
          data-umami-event="admin-goto-sqladmin">
          打开 SQLAdmin →
        </a>
      </section>

      <section class="bg-white dark:bg-[#1a1b23] rounded-xl border border-gray-200 dark:border-gray-700 p-6">
        <h2 class="text-sm font-bold text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-4">导入语料库</h2>
        <p class="text-sm text-gray-600 dark:text-gray-300 mb-4">
          上传 JSONL 格式的语料文件，格式与 <code class="text-xs bg-gray-100 dark:bg-gray-800 px-1 rounded">server/import_corpus.py</code> 兼容。
        </p>

        <form @submit.prevent="handleImport" class="flex items-center gap-3">
          <input
            ref="fileInput"
            type="file"
            accept=".jsonl,.json"
            class="block text-sm text-gray-600 dark:text-gray-300 file:mr-3 file:py-1.5 file:px-3 file:rounded file:border file:border-gray-300 dark:file:border-gray-600 file:text-sm file:bg-gray-50 dark:file:bg-gray-800 file:text-gray-700 dark:file:text-gray-200 hover:file:bg-gray-100 dark:hover:file:bg-gray-700"
            required
          >
          <button
            type="submit"
            :disabled="importing"
            class="px-4 py-1.5 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-500 transition-colors disabled:opacity-50"
            data-umami-event="admin-import-submit">
            {{ importing ? '导入中...' : '导入' }}
          </button>
        </form>

        <div v-if="importResult" class="mt-4">
          <div v-if="importResult.success"
            class="text-sm text-green-700 dark:text-green-400 bg-green-50 dark:bg-green-950/30 border border-green-200 dark:border-green-800 rounded-lg px-4 py-3">
            成功从 <strong>{{ importResult.filename }}</strong> 导入 <strong>{{ importResult.count }}</strong> 条语料记录。
          </div>
          <div v-else
            class="text-sm text-red-700 dark:text-red-400 bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-800 rounded-lg px-4 py-3">
            导入失败: {{ importResult.error }}
          </div>
        </div>
      </section>
    </template>
  </div>
</template>
