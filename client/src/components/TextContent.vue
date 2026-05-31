<script setup lang="ts">
import { computed, ref } from 'vue'
import { useWordsStore } from '@/stores/words'
import type { TrackedWord, DocumentRecord } from '@/types'
import { useAuthStore } from '@/stores/auth'
import type { TextSegment } from '@/types'
import { useDocumentLoader } from '@/composables/useDocumentLoader'
import ConfirmDialog from '@/components/ConfirmDialog.vue'
import SaveDocumentDialog from '@/components/SaveDocumentDialog.vue'
import LoadDocumentDialog from '@/components/LoadDocumentDialog.vue'
import UsageGuide from '@/components/UsageGuide.vue'

const props = withDefaults(defineProps<{
  editableText: string
  editing: boolean
  editText: string
  textSegments: TextSegment[]
  readonly?: boolean
}>(), {
  readonly: false,
})

const emit = defineEmits<{
  startEditing: []
  saveEditing: []
  cancelEditing: []
  'update:editText': [value: string]
  wordClick: [id: string]
}>()

const wordsStore = useWordsStore()
const auth = useAuthStore()
const { loadDocument, confirmState } = useDocumentLoader()

const showDocMenu = ref(false)
const showSaveDialog = ref(false)
const showLoadDialog = ref(false)
const docMenuError = ref('')
const saveResult = ref<{ id: number; title: string; public_uuid?: string | null } | null>(null)
const showUsageGuide = ref(false)

function toggleDocMenu() {
  showDocMenu.value = !showDocMenu.value
}

async function handleSave(payload: { title: string; isPublic: boolean }) {
  try {
    const result = await wordsStore.saveSnapshot(payload.title, payload.isPublic)
    saveResult.value = result
  } catch (e) {
    docMenuError.value = e instanceof Error ? e.message : '保存失败'
    setTimeout(() => { docMenuError.value = '' }, 3000)
    showDocMenu.value = false
  }
}

async function handleUpdate(payload: { title: string; isPublic: boolean }) {
  try {
    await wordsStore.updateCurrentDoc(payload.title, payload.isPublic)
    showSaveDialog.value = false
    saveResult.value = null
  } catch (e) {
    docMenuError.value = e instanceof Error ? e.message : '更新失败'
    setTimeout(() => { docMenuError.value = '' }, 3000)
  }
}

function handleDismiss() {
  showSaveDialog.value = false
  saveResult.value = null
}

function handleLoad(doc: DocumentRecord) {
  showLoadDialog.value = false
  showDocMenu.value = false
  loadDocument(doc)
}

const searchQuery = ref('')

const searchSites = [
  { key: 'shidianguji', label: '识典古籍',
    url: (q: string) => `https://www.shidianguji.com/search/${encodeURIComponent(q)}` },
  { key: 'ctext-pre-qin', label: 'ctext 秦汉',
    url: (q: string) => `https://ctext.org/pre-qin-and-han?searchu=${encodeURIComponent(q)}` },
  { key: 'ctext-post-han', label: 'ctext 汉后',
    url: (q: string) => `https://ctext.org/post-han?searchu=${encodeURIComponent(q)}` },
  { key: 'guwendao', label: '古文岛',
    url: (q: string) => `https://www.guwendao.net/search.aspx?value=${encodeURIComponent(q)}` },
]

function searchOn(key: string) {
  const q = searchQuery.value.trim()
  if (!q) return
  const site = searchSites.find(s => s.key === key)
  if (site) window.open(site.url(q), '_blank', 'noopener')
}

const segmentOffsets = computed(() => {
  const offsets: number[] = []
  let cursor = 0
  for (const seg of props.textSegments) {
    if (seg.type === 'text') {
      offsets.push(cursor)
      cursor += seg.content.length
    } else {
      offsets.push(seg.word.offset)
      cursor = seg.word.offset + seg.word.word.length
    }
  }
  return offsets
})

const getTrackedWordClass = (w: TrackedWord) => {
  const isActive = w.id === wordsStore.activeWordId
  const base = 'tracked-word inline cursor-pointer transition-all duration-200 rounded'
  if (isActive) {
    return `${base} border-b-2 border-blue-600 dark:border-blue-400 bg-blue-200 dark:bg-blue-800/50 ring-2 ring-blue-300 dark:ring-blue-600`
  }
  if (w.status === 'loading') {
    return `${base} border-b-2 border-dashed border-yellow-400 bg-yellow-50 dark:bg-yellow-950/30 hover:bg-yellow-100 dark:hover:bg-yellow-900/30`
  }
  if (w.status === 'done' && (w.quickAnswer || w.dictResult || w.deepThink)) {
    return `${base} border-b-2 border-blue-500 bg-blue-50 dark:bg-blue-950/30 hover:bg-blue-100 dark:hover:bg-blue-900/30`
  }
  if (w.status === 'error') {
    return `${base} border-b-2 border-dashed border-red-400 bg-red-50 dark:bg-red-950/30 hover:bg-red-50 dark:hover:bg-red-900/30`
  }
  return `${base} border-b-2 border-dashed border-blue-300 hover:bg-blue-50 dark:hover:bg-blue-950/20`
}
</script>

<template>
  <div class="flex flex-col sm:flex-row sm:items-center justify-between mb-4 gap-1">
    <div class="flex items-center gap-2 min-w-0">
      <h1 class="text-xl sm:text-2xl font-bold shrink-0">划词阅读</h1>
      <span v-if="wordsStore.currentDocId"
        class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs bg-blue-50 dark:bg-blue-950/30 text-blue-600 dark:text-blue-400 whitespace-nowrap">
        📄 {{ wordsStore.currentDocTitle }}</span>
      <span v-if="auth.quota" title="已用查询次数/每日总配额 · 剩余免费次数"
        class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs
               bg-gray-100 dark:bg-gray-800 text-gray-500 dark:text-gray-400 whitespace-nowrap">
        <template v-if="auth.user.logged_in">
          <span>{{ auth.quota.used }}/{{ auth.quota.limit }}</span>
          <span>·</span>
          <span :class="auth.quota.remaining < 5 ? 'text-red-500' : ''">剩{{ auth.quota.remaining }}</span>
        </template>
        <template v-else>
          <span :class="auth.quota.remaining < 5 ? 'text-red-500' : ''">游客共享免费额度 · 剩{{ auth.quota.remaining }} 次</span>
        </template>
      </span>
    </div>
    <div v-if="!readonly" class="flex gap-2 text-sm shrink-0">
      <div class="relative">
        <button v-if="!editing && auth.user.logged_in"
          @click="toggleDocMenu"
          class="px-3 py-1 border border-gray-300 dark:border-gray-600 rounded hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
          data-umami-event="home-doc-menu">📄 文档</button>
        <div v-if="showDocMenu"
          class="absolute right-0 top-full mt-1 w-48 bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 z-40 py-1">
          <button @click="showSaveDialog = true; showDocMenu = false"
            class="w-full text-left px-4 py-2 text-sm hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors">💾 保存文档...</button>
          <button @click="showLoadDialog = true; showDocMenu = false"
            class="w-full text-left px-4 py-2 text-sm hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors">📂 打开文档</button>

        </div>
      </div>
      <button v-if="!editing" @click="emit('startEditing')"
        class="px-3 py-1 border border-gray-300 dark:border-gray-600 rounded hover:bg-gray-100 dark:hover:bg-gray-800" data-umami-event="home-text-edit">编辑文本</button>
      <button @click="showUsageGuide = true"
        class="w-7 h-7 flex items-center justify-center rounded-full border border-gray-300 dark:border-gray-600 text-sm text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
        title="使用指南">?</button>
    </div>
    <p v-if="docMenuError" class="text-red-500 text-xs">{{ docMenuError }}</p>
  </div>

  <div v-if="editing" class="space-y-3">
    <textarea :value="editText"
      @input="emit('update:editText', ($event.target as HTMLTextAreaElement).value)"
      class="w-full min-h-48 p-4 border border-gray-200 dark:border-gray-700 rounded-lg text-lg leading-loose resize-y focus:outline-none focus:ring-2 focus:ring-blue-300 dark:bg-gray-900 dark:text-gray-100 font-sans"></textarea>
    <div class="flex gap-2 justify-end">
      <button @click="emit('cancelEditing')"
        class="px-4 py-1.5 border border-gray-300 dark:border-gray-600 rounded text-sm hover:bg-gray-100 dark:hover:bg-gray-800" data-umami-event="home-text-cancel">取消</button>
      <button @click="emit('saveEditing')"
        class="px-4 py-1.5 bg-blue-600 text-white rounded text-sm hover:bg-blue-500" data-umami-event="home-text-save">保存</button>
    </div>
  </div>

  <div v-else
    class="min-h-48 p-4 border border-gray-200 dark:border-gray-700 dark:bg-gray-900 dark:text-gray-100 rounded-lg text-lg leading-loose whitespace-pre-wrap select-text"
    style="-webkit-touch-callout:none; touch-action: manipulation" @contextmenu.prevent>
    <template v-if="textSegments.length === 0">
      <span data-offset="0">{{ editableText }}</span>
    </template>
    <template v-else>
      <span v-for="(seg, i) in textSegments" :key="i">
        <span v-if="seg.type === 'text'" :data-offset="segmentOffsets[i]">{{ seg.content }}</span>
        <span v-else :data-offset="segmentOffsets[i]" :class="getTrackedWordClass(seg.word)" @click.stop="emit('wordClick', seg.word.id)">
          {{ seg.word.word }}
           <span v-if="seg.word.quickAnswer.length > 0" class="text-sm text-yellow-800 dark:text-yellow-300">({{ seg.word.quickAnswer }})</span>
          <span v-if="seg.word.status === 'loading'" class="ml-0.5">
            <span class="animate-spin inline-block w-3 h-3 border border-yellow-400 border-t-transparent rounded-full align-middle"></span>
          </span>
        </span>
      </span>
    </template>
  </div>

  <p v-if="!readonly" class="text-sm text-gray-400 dark:text-gray-500 mt-4">💡 提示：选中任意词语，即可触发查询。</p>

  <p v-if="!readonly" class="text-xs text-gray-400 dark:text-gray-500 mt-4">需要查找其他文章？输入篇名、作者或文章开头几个字搜索全文，复制后粘贴到上方阅读区即可。</p>

  <div v-if="!readonly" class="mt-2 flex flex-wrap items-start gap-2 p-3 border border-gray-200 dark:border-gray-700 rounded-lg bg-gray-50 dark:bg-gray-900/50">
    <div class="flex items-center gap-1.5 w-full sm:w-auto">
      <span class="text-sm text-gray-500 dark:text-gray-400 whitespace-nowrap">📖 搜索</span>
      <input v-model="searchQuery" placeholder="篇名、作者或文章开头…"
        class="flex-1 min-w-0 px-2.5 py-1 border border-gray-300 dark:border-gray-600 rounded text-sm
               focus:outline-none focus:ring-2 focus:ring-blue-300 dark:bg-gray-800 dark:text-gray-100
               placeholder-gray-400 dark:placeholder-gray-500"
        @keyup.enter="searchOn('shidianguji')">
    </div>
    <div class="flex flex-wrap gap-1.5">
      <button v-for="site in searchSites" :key="site.key" @click="searchOn(site.key)"
        class="px-2.5 py-1 rounded text-xs font-medium border transition-colors whitespace-nowrap
               border-gray-300 dark:border-gray-600
               text-gray-600 dark:text-gray-400
               hover:bg-gray-200 dark:hover:bg-gray-700
               active:bg-gray-300 dark:active:bg-gray-600">
        {{ site.label }}
      </button>
    </div>
  </div>

  <SaveDocumentDialog v-if="showSaveDialog"
    :default-title="wordsStore.editableText.slice(0, 20)"
    :saved-result="saveResult"
    :current-doc="wordsStore.currentDocId ? { id: wordsStore.currentDocId, title: wordsStore.currentDocTitle, is_public: wordsStore.currentDocIsPublic } : null"
    @save="handleSave"
    @update="handleUpdate"
    @cancel="handleDismiss"
    @dismiss="handleDismiss" />

  <LoadDocumentDialog v-if="showLoadDialog"
    @load="handleLoad"
    @cancel="showLoadDialog = false" />

  <ConfirmDialog v-if="confirmState" :state="confirmState" />

  <UsageGuide :show="showUsageGuide" @dismiss="showUsageGuide = false" />
</template>

<style scoped>
.dark .tracked-word.loading {
  border-bottom-color: #f59e0b;
  background-color: #451a03;
}
.dark .tracked-word.done {
  border-bottom-color: #3b82f6;
  background-color: #172554;
}
.dark .tracked-word.error {
  border-bottom-color: #ef4444;
  background-color: #450a0a;
}
</style>
