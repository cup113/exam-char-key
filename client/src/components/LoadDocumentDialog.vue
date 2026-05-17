<script setup lang="ts">
import { ref, onMounted } from 'vue'
import type { DocumentRecord } from '@/types'
import * as documentService from '@/services/documentService'
import type { DocListItem } from '@/services/documentService'

const emit = defineEmits<{
  load: [doc: DocumentRecord]
  cancel: []
}>()

const documents = ref<DocListItem[]>([])
const loading = ref(true)
const error = ref('')
const actionError = ref('')
const copiedId = ref<number | null>(null)

async function fetchDocs() {
  loading.value = true
  error.value = ''
  try {
    const data = await documentService.listDocs()
    documents.value = data.documents || []
  } catch (e) {
    error.value = e instanceof Error ? e.message : '未知错误'
  } finally {
    loading.value = false
  }
}

onMounted(fetchDocs)

function wordCount(doc: DocListItem): number {
  return doc.tracked_words?.length || 0
}

function preview(text: string, len = 40): string {
  return text.length > len ? text.slice(0, len) + '…' : text
}

async function deleteDoc(doc: DocListItem) {
  if (!window.confirm(`确认删除「${doc.title}」？`)) return
  actionError.value = ''
  try {
    await documentService.deleteDoc(doc.id)
    await fetchDocs()
  } catch (e) {
    actionError.value = e instanceof Error ? e.message : '删除失败'
  }
}

async function togglePublic(doc: DocListItem) {
  actionError.value = ''
  const nextPublic = !doc.is_public
  try {
    await documentService.updateDoc(doc.id, { is_public: nextPublic })
    await fetchDocs()
  } catch (e) {
    actionError.value = e instanceof Error ? e.message : '操作失败'
  }
}

async function copyPublicLink(doc: DocListItem) {
  if (!doc.public_uuid) return
  const url = `${window.location.origin}/shared/${doc.public_uuid}`
  try {
    await navigator.clipboard.writeText(url)
    copiedId.value = doc.id
    setTimeout(() => { copiedId.value = null }, 2000)
  } catch {
    actionError.value = '复制失败'
  }
}
</script>

<template>
  <Teleport to="body">
    <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/30" @click.self="emit('cancel')">
      <div class="bg-white dark:bg-gray-900 rounded-xl p-6 w-[90vw] max-w-[520px] max-h-[75vh] flex flex-col shadow-2xl">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-lg font-bold">文档管理</h3>
          <button @click="emit('cancel')"
            class="text-gray-400 dark:text-gray-500 hover:text-gray-800 dark:hover:text-white text-lg">✕</button>
        </div>

        <p v-if="actionError" class="text-xs text-red-500 mb-2">{{ actionError }}</p>

        <div v-if="loading" class="text-center text-gray-500 py-8">加载中…</div>
        <div v-else-if="error" class="text-center text-red-500 py-4">{{ error }}</div>
        <div v-else-if="documents.length === 0" class="text-center text-gray-500 py-8">暂无文档</div>
        <div v-else class="overflow-y-auto flex-1 space-y-2">
          <div v-for="doc in documents" :key="doc.id"
            class="p-3 rounded-lg border border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors cursor-pointer"
            @click="emit('load', doc as unknown as DocumentRecord)">
            <div class="flex items-start justify-between gap-2">
              <div class="font-medium text-sm truncate min-w-0">{{ doc.title }}</div>
              <span class="shrink-0 text-xs text-gray-400 dark:text-gray-500 whitespace-nowrap">{{ doc.created_at }}</span>
            </div>
            <div class="text-xs text-gray-500 dark:text-gray-400 mt-0.5 truncate">
              原文: {{ preview(doc.source_text) }}
            </div>
            <div class="flex items-center gap-2 mt-1.5">
              <span class="text-xs text-gray-400 dark:text-gray-500">{{ wordCount(doc) }} 词</span>
              <button v-if="doc.is_public"
                @click.stop="togglePublic(doc)"
                class="text-xs text-green-600 dark:text-green-400 hover:text-green-700 dark:hover:text-green-300 transition-colors">公开</button>
              <button v-else
                @click.stop="togglePublic(doc)"
                class="text-xs text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-300 transition-colors">私有</button>
              <button v-if="doc.public_uuid"
                @click.stop="copyPublicLink(doc)"
                class="text-xs text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 transition-colors">
                {{ copiedId === doc.id ? '已复制' : '复制链接' }}
              </button>
              <button @click.stop="deleteDoc(doc)"
                class="text-xs text-red-500 hover:text-red-700 dark:hover:text-red-400 transition-colors ml-auto">删除</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>
