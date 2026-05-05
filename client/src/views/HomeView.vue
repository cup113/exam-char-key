<script setup lang="ts">
import { ref, reactive, computed, onMounted, onUnmounted, watch } from 'vue'
import { useWordsStore } from '@/stores/words'
import { useAuthStore } from '@/stores/auth'
import type { TextSegment } from '@/types'

import TextContent from '@/components/TextContent.vue'
import SelectionTooltip from '@/components/SelectionTooltip.vue'
import QueryPanel from '@/components/QueryPanel.vue'
import LoginButtons from '@/components/LoginButtons.vue'

let hideTimer: ReturnType<typeof setTimeout> | null = null

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
  document.addEventListener('selectionchange', onSelectionChange)
})

onUnmounted(() => {
  wordsStore.abortAll()
  document.removeEventListener('selectionchange', onSelectionChange)
  if (hideTimer) clearTimeout(hideTimer)
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

const getTextOffsetFromSelection = (): number => {
  const sel = window.getSelection()
  if (!sel || !sel.rangeCount) return -1
  const range = sel.getRangeAt(0)
  const node = range.startContainer
  const offset = range.startOffset

  const el = node.nodeType === Node.TEXT_NODE
    ? (node.parentNode as Element)?.closest('[data-offset]')
    : (node as Element).closest('[data-offset]')
  if (!el) return -1

  const baseOffset = parseInt(el.getAttribute('data-offset') || '', 10)
  if (isNaN(baseOffset)) return -1

  let localOffset = 0
  const walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT)
  while (walker.nextNode()) {
    const tn = walker.currentNode as Text
    if (tn === node) return baseOffset + localOffset + offset
    localOffset += (tn.textContent || '').length
  }
  return baseOffset + localOffset
}

const handlePointerUp = (e: PointerEvent) => {
  if (wordsStore.editing) return
  const target = e.target as HTMLElement
  if (target.closest('#query-panel') || target.closest('.tracked-word')) return

  const sel = window.getSelection()
  if (!sel || sel.isCollapsed) return

  showTooltipFromSelection(sel)

  if (selection.showTooltip && sel.rangeCount > 0) {
    const range = sel.getRangeAt(0)
    sel.removeAllRanges()
    requestAnimationFrame(() => {
      if (selection.showTooltip) {
        sel.addRange(range)
      }
    })
  }
}

const onSelectionChange = () => {
  if (wordsStore.editing) return
  const sel = window.getSelection()
  if (!sel || sel.isCollapsed) {
    scheduleHide()
    return
  }

  let node = sel.anchorNode
  if (!node) return
  if (node.nodeType === Node.TEXT_NODE) node = node.parentNode as Node
  const el = node instanceof Element ? node : node.parentElement
  if (!el || !el.closest('[data-offset]')) {
    scheduleHide()
    return
  }

  showTooltipFromSelection(sel)
}

function scheduleHide() {
  if (hideTimer) return
  hideTimer = setTimeout(() => {
    selection.showTooltip = false
    hideTimer = null
  }, 300)
}

function showTooltipFromSelection(sel: Selection) {
  const text = sel.toString().trim()
  if (!text || text.length > 20) return

  const offset = getTextOffsetFromSelection()
  if (offset === -1) return

  const pos = getSelectionPosition()
  if (!pos) return

  const gap = 8
  const tooltipWidth = 180
  const clampedX = Math.max(
    tooltipWidth / 2 + gap,
    Math.min(pos.x, window.innerWidth - tooltipWidth / 2 - gap)
  )

  selection.word = text
  selection.offset = offset
  selection.context = getContextAround(offset, text.length)
  selection.x = clampedX
  selection.y = Math.max(10, pos.y - 50)
  selection.showTooltip = true

  if (hideTimer) {
    clearTimeout(hideTimer)
    hideTimer = null
  }
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
          class="mb-3 px-3 py-2 bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-800 rounded-lg text-xs flex items-center justify-between gap-2">
          <span>免费剩余 <strong>{{ auth.quota!.remaining }}</strong> 次 · <LoginButtons size="sm" /></span>
          <button @click="auth.dismissQuotaPrompt"
            class="text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-300 text-lg leading-none">&times;</button>
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
  </div>
</template>
