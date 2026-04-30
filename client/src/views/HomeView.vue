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

const editableText = ref(`子曰："为政以德，譬如北辰，居其所而众星共之。"
子曰："诗三百，一言以蔽之，曰：'思无邪'。"
孟懿子问孝。子曰："无违。"樊迟御，子告之曰："孟孙问孝于我，我对曰'无违'。"樊迟曰："何谓也？"子曰："生，事之以礼；死，葬之以礼，祭之以礼。"`)

const selection = reactive({
  word: '',
  offset: 0,
  context: '',
  showTooltip: false,
  x: 0,
  y: 0,
})

const showPanel = ref(false)
const editing = ref(false)
const editText = ref('')
const savedAnswer = ref('')
const saveSuccess = ref(false)

const textSegments = computed<TextSegment[]>(() => {
  if (editing.value) return []
  const text = editableText.value
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

const getContextAround = (offset: number, wordLen: number, windowSize = 80): string => {
  const start = Math.max(0, offset - windowSize)
  const end = Math.min(editableText.value.length, offset + wordLen + windowSize)
  let result = editableText.value.slice(start, end)
  if (start > 0) result = '...' + result
  if (end < editableText.value.length) result = result + '...'
  return result
}

onMounted(() => {
  auth.fetchUser()
})

onUnmounted(() => {
  wordsStore.cleanupSSE()
})

watch(() => wordsStore.activeWordId, (id) => {
  showPanel.value = id !== null
  if (id) {
    const w = wordsStore.trackedWords.find(x => x.id === id)
    savedAnswer.value = w?.quickAnswer || ''
    saveSuccess.value = false
  }
})

const handleMouseUp = (e: MouseEvent) => {
  if (editing.value) return
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

  const offset = editableText.value.indexOf(text)
  if (offset === -1) {
    selection.showTooltip = false
    return
  }

  selection.word = text
  selection.offset = offset
  selection.context = getContextAround(offset, text.length)
  selection.x = e.clientX
  selection.y = e.clientY - 50
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

const startEditing = () => {
  editText.value = editableText.value
  editing.value = true
}

const saveEditing = () => {
  editableText.value = editText.value
  editing.value = false
  wordsStore.clearAll()
}

const cancelEditing = () => {
  editing.value = false
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
  <div class="flex" @mouseup="handleMouseUp">
    <main class="flex-1 min-w-0 p-10 transition-all duration-300"
      :class="showPanel ? 'lg:mr-108' : ''">
      <div class="max-w-3xl mx-auto">
        <TextContent
          :editableText="editableText"
          :editing="editing"
          :editText="editText"
          :textSegments="textSegments"
          @startEditing="startEditing"
          @saveEditing="saveEditing"
          @cancelEditing="cancelEditing"
          @update:editText="editText = $event"
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
