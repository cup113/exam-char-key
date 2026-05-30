<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useWordsStore } from '@/stores/words'
import { useDocumentLoader } from '@/composables/useDocumentLoader'
import { buildTextSegments } from '@/utils/textSegments'
import type { DocumentRecord, TrackedWordSnapshot, TextSegment, TrackedWord } from '@/types'
import * as documentService from '@/services/documentService'
import TextContent from '@/components/TextContent.vue'
import WordAnalysisCard from '@/components/WordAnalysisCard.vue'
import ConfirmDialog from '@/components/ConfirmDialog.vue'

const route = useRoute()
const router = useRouter()
const wordsStore = useWordsStore()
const { loadDocument, confirmState } = useDocumentLoader()

const doc = ref<DocumentRecord | null>(null)
const loading = ref(true)
const error = ref('')
const activeSnapshot = ref<TrackedWordSnapshot | null>(null)

onMounted(async () => {
  try {
    doc.value = await documentService.getPublicDoc(route.params.uuid as string)
  } catch (e) {
    error.value = e instanceof Error ? e.message : '加载失败'
  } finally {
    loading.value = false
  }
})

const textSegments = computed<TextSegment[]>(() => {
  if (!doc.value) return []
  const words: TrackedWord[] = doc.value.tracked_words.map((w, i) => ({
    id: `doc-${i}`,
    word: w.word,
    context: w.context,
    offset: w.offset,
    mode: w.mode,
    quickAnswer: w.quickAnswer,
    dictResult: w.dictResult,
    deepThink: w.deepThink,
    corpusEntries: w.corpusEntries,
    status: 'done',
    quickStatus: 'done',
    corpusStatus: 'done',
    dictStatus: 'done',
    deepStatus: w.deepThink ? 'done' : 'idle',
    startTime: Date.now(),
  }))
  return buildTextSegments(doc.value.source_text, words)
})

function onWordClick(id: string) {
  const snapIdx = parseInt(id.replace('doc-', ''), 10)
  if (isNaN(snapIdx) || !doc.value) return
  const snap = doc.value.tracked_words[snapIdx]
  if (snap) {
    activeSnapshot.value = snap
  }
}

function closePanel() {
  activeSnapshot.value = null
}

async function handleContinueQuery() {
  if (!doc.value) return
  const ok = await loadDocument(doc.value)
  if (ok) {
    router.push('/')
  }
}
</script>

<template>
  <div class="flex" @pointerup.self="closePanel">
    <main class="flex-1 min-w-0 p-6 transition-all duration-300"
      :class="activeSnapshot ? 'lg:mr-108' : ''">
      <div class="max-w-3xl mx-auto">
        <div v-if="loading" class="text-center text-gray-500 py-16">加载中…</div>
        <div v-else-if="error" class="text-center text-red-500 py-16">{{ error }}</div>
        <template v-else-if="doc">
          <header class="flex items-start justify-between gap-4 mb-6">
            <div>
              <h1 class="text-2xl font-bold">{{ doc.title }}</h1>
              <p class="text-sm text-gray-400 dark:text-gray-500 mt-1">
                {{ doc.created_at }} · {{ doc.tracked_words.length }} 个词语
              </p>
            </div>
            <button @click="handleContinueQuery"
              class="shrink-0 px-4 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-500 transition-colors"
              data-umami-event="shared-continue">
              继续查询
            </button>
          </header>

          <TextContent
            :editable-text="doc.source_text"
            :editing="false"
            :edit-text="doc.source_text"
            :text-segments="textSegments"
            readonly
            @word-click="onWordClick" />
        </template>
      </div>
    </main>

    <aside v-if="activeSnapshot"
      class="flex flex-col bg-white dark:bg-[#1a1b23] border-l border-gray-200 dark:border-gray-700 shadow-2xl transition-transform duration-300"
      :class="[
        'lg:fixed lg:right-0 lg:top-12 lg:bottom-0 lg:w-108 lg:z-30 lg:translate-x-0',
        'max-lg:fixed max-lg:inset-x-0 max-lg:bottom-0 max-lg:max-h-[80vh] max-lg:rounded-t-2xl max-lg:shadow-[0_-8px_30px_rgba(0,0,0,0.15)] max-lg:z-30 max-lg:translate-y-0',
      ]">
      <div class="flex items-start justify-between px-5 py-4 border-b border-gray-100 dark:border-gray-800">
        <div>
          <h2 class="text-lg font-bold">「{{ activeSnapshot.word }}」</h2>
          <span class="text-xs text-gray-400 dark:text-gray-500">文档快照</span>
        </div>
        <button @click="closePanel"
          class="text-gray-400 dark:text-gray-500 hover:text-gray-800 dark:hover:text-white text-lg mt-0.5">✕</button>
      </div>
      <div class="flex-1 overflow-y-auto p-5">
        <WordAnalysisCard :word="activeSnapshot" readonly />
      </div>
      <div class="max-lg:flex lg:hidden items-center justify-center py-2 border-t border-gray-100 dark:border-gray-800 cursor-pointer"
        @click="closePanel">
        <div class="w-10 h-1 bg-gray-300 dark:bg-gray-600 rounded-full"></div>
      </div>
    </aside>

    <ConfirmDialog v-if="confirmState" :state="confirmState" />
  </div>
</template>
