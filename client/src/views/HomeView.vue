<script setup lang="ts">
import { ref, reactive, computed, onMounted, onUnmounted, watch } from 'vue'
import { useWordsStore } from '@/stores/words'
import { useAuthStore } from '@/stores/auth'
import type { TextSegment } from '@/types'

import TextContent from '@/components/TextContent.vue'
import SelectionTooltip from '@/components/SelectionTooltip.vue'
import QueryPanel from '@/components/QueryPanel.vue'

const wordsStore = useWordsStore()
const auth = useAuthStore()

const selection = reactive({
  word: '',
  offset: 0,
  context: '',
  showTooltip: false,
  x: 0,
  y: 0,
})

const showPanel = ref(false)
const savedAnswer = ref('')
const saveSuccess = ref(false)

const textSegments = computed<TextSegment[]>(() => {
  if (wordsStore.editing) return []
  const text = wordsStore.editableText
  const words = [...wordsStore.trackedWords]
    .filter(w => text.indexOf(w.word, w.offset) === w.offset)
    .sort((a, b) => a.offset - b.offset)

  const segments: TextSegment[] = []
  let cursor = 0
  for (const w of words) {
    if (w.offset < cursor) continue
    if (w.offset > cursor) {
      segments.push({ type: 'text', content: text.slice(cursor, w.offset) })
    }
    segments.push({ type: 'word', word: w })
    cursor = w.offset + w.word.length
  }
  if (cursor < text.length) {
    segments.push({ type: 'text', content: text.slice(cursor) })
  }
  return segments
})

const getContextAround = (offset: number, wordLen: number, windowSize = 30): string => {
  const start = Math.max(0, offset - windowSize)
  const end = Math.min(wordsStore.editableText.length, offset + wordLen + windowSize)
  let result = wordsStore.editableText.slice(start, end)
  if (start > 0) result = '...' + result
  if (end < wordsStore.editableText.length) result = result + '...'
  return result
}

onMounted(async () => {
  await auth.fetchUser()
  auth.fetchQuota()
})

onUnmounted(() => {
  wordsStore.abortAll()
})

watch(() => wordsStore.activeWordId, (id) => {
  showPanel.value = id !== null
  if (id) {
    const w = wordsStore.trackedWords.find(x => x.id === id)
    savedAnswer.value = w?.quickAnswer || ''
    saveSuccess.value = false
  }
})

const getSelectionPosition = () => {
  const sel = window.getSelection()
  if (sel && sel.rangeCount > 0) {
    const rect = sel.getRangeAt(0).getBoundingClientRect()
    if (rect.width > 0 || rect.height > 0) {
      return { x: rect.left + rect.width / 2, y: rect.top - 10 }
    }
  }
  return null
}

const handlePointerUp = (e: PointerEvent) => {
  if (wordsStore.editing) return
  const target = e.target as HTMLElement
  if (target.closest('#query-panel') || target.closest('.tracked-word')) return

  const sel = window.getSelection()
  if (!sel || sel.isCollapsed) {
    setTimeout(() => { selection.showTooltip = false }, 200)
    return
  }

  const text = sel.toString().trim()
  if (!text || text.length > 20) {
    selection.showTooltip = false
    return
  }

  const offset = wordsStore.editableText.indexOf(text)
  if (offset === -1) {
    selection.showTooltip = false
    return
  }

  const pos = getSelectionPosition() ?? { x: e.clientX, y: e.clientY }

  selection.word = text
  selection.offset = offset
  selection.context = getContextAround(offset, text.length)
  selection.x = pos.x
  selection.y = pos.y - 50
  selection.showTooltip = true
}

const startQuery = (mode: 'quick' | 'deep') => {
  wordsStore.queryWord(selection.word, selection.context, mode, selection.offset)
  selection.showTooltip = false
}

const wordClick = (id: string) => {
  wordsStore.activeWordId = id
}

const closePanel = () => {
  showPanel.value = false
  wordsStore.activeWordId = null
}

const saveToHistory = async () => {
  const w = wordsStore.activeWord
  if (!w) return

  const answer = savedAnswer.value.trim() || w.quickAnswer

  try {
    const resp = await fetch('/api/history', {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        word: w.word,
        context: w.context,
        mode: w.mode,
        quick_answer: answer,
        dict_result: w.dictResult,
        deep_think: w.deepThink,
      }),
    })
    if (resp.ok) {
      saveSuccess.value = true
      setTimeout(() => { saveSuccess.value = false }, 2000)
    }
  } catch {
    // ignore
  }
}
</script>

<template>
  <div class="flex" @pointerup="handlePointerUp">
    <main class="flex-1 min-w-0 p-10 transition-all duration-300"
      :class="showPanel ? 'lg:mr-108' : ''">
      <div class="max-w-3xl mx-auto">
        <div v-if="auth.showQuotaPrompt"
          class="mb-4 px-4 py-3 bg-amber-50 border border-amber-200 rounded-lg text-sm flex items-center justify-between gap-4">
          <span>
            今日免费查询剩余 <strong>{{ auth.quota!.remaining }}</strong> 次，
            注册获取更多免费次数。
          </span>
          <span class="flex items-center gap-2 shrink-0">
            <a href="/api/auth/github/login"
              class="px-3 py-1.5 bg-gray-900 text-white rounded hover:bg-gray-700 text-xs whitespace-nowrap">GitHub 登录</a>
            <a href="/api/auth/gitee/login"
              class="px-3 py-1.5 bg-green-600 text-white rounded hover:bg-green-500 text-xs whitespace-nowrap">Gitee 登录</a>
            <button @click="auth.dismissQuotaPrompt"
              class="text-gray-400 hover:text-gray-600 text-lg leading-none ml-1">&times;</button>
          </span>
        </div>
        <TextContent
          :editableText="wordsStore.editableText"
          :editing="wordsStore.editing"
          :editText="wordsStore.editText"
          :textSegments="textSegments"
          @startEditing="wordsStore.startEditing"
          @saveEditing="wordsStore.saveEditing"
          @cancelEditing="wordsStore.cancelEditing"
          @update:editText="wordsStore.editText = $event"
          @wordClick="wordClick" />
      </div>
    </main>

    <SelectionTooltip
      :show="selection.showTooltip"
      :x="selection.x"
      :y="selection.y"
      @quick="startQuery('quick')"
      @deep="startQuery('deep')" />

    <QueryPanel
      :show="showPanel"
      :activeWord="wordsStore.activeWord"
      :savedAnswer="savedAnswer"
      :saveSuccess="saveSuccess"
      :loggedIn="auth.user.logged_in"
      @close="closePanel"
      @update:savedAnswer="savedAnswer = $event"
      @save="saveToHistory" />

    <div v-if="showPanel"
      class="max-lg:fixed max-lg:inset-0 max-lg:bg-black/30 max-lg:z-20 transition-opacity duration-300"
      @click="closePanel">
    </div>
  </div>
</template>
