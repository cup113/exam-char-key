<script setup lang="ts">
import { ref, reactive, computed, onMounted, onUnmounted, watch } from 'vue'
import { useWordsStore, type TrackedWord } from '@/stores/words'
import { useAuthStore } from '@/stores/auth'

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
const activeEventSources = new Map<string, EventSource>()

type TextSegment =
  | { type: 'text'; content: string }
  | { type: 'word'; word: TrackedWord }

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
  for (const es of activeEventSources.values()) {
    es.close()
  }
  activeEventSources.clear()
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
  selection.x = e.pageX
  selection.y = e.pageY - 50
  selection.showTooltip = true
}

const startQuery = (mode: 'quick' | 'deep') => {
  const wordId = wordsStore.addWord(selection.word, selection.context, mode, selection.offset)
  selection.showTooltip = false
  wordsStore.activeWordId = wordId

  wordsStore.updateWord(wordId, { status: 'loading', statusText: '正在连接...' })

  const url = new URL('http://localhost:8000/api/query')
  url.searchParams.set('word', selection.word)
  url.searchParams.set('context', selection.context)
  url.searchParams.set('mode', mode)

  const es = new EventSource(url.toString())
  activeEventSources.set(wordId, es)

  es.onmessage = (event) => {
    const data = JSON.parse(event.data)

    if (data.error) {
      wordsStore.updateWord(wordId, { status: 'error', statusText: `错误: ${data.error}` })
      es.close()
      activeEventSources.delete(wordId)
      return
    }

    switch (data.step) {
      case 'quick_answer':
        if (data.status === 'start') wordsStore.updateWord(wordId, { statusText: '正在快速解答...' })
        if (data.chunk) {
          const current = wordsStore.trackedWords.find(w => w.id === wordId)
          wordsStore.updateWord(wordId, { quickAnswer: (current?.quickAnswer || '') + data.chunk })
        }
        break
      case 'dictionary':
        if (data.status === 'fetching') wordsStore.updateWord(wordId, { statusText: '正在查阅汉典...' })
        if (data.result) {
          wordsStore.updateWord(wordId, {
            dictResult: data.result,
            statusText: mode === 'quick' ? '查询完成' : '字典查询完成'
          })
        }
        break
      case 'deep_think':
        if (data.status === 'start') wordsStore.updateWord(wordId, { statusText: '正在深度思考...' })
        if (data.chunk) {
          const current = wordsStore.trackedWords.find(w => w.id === wordId)
          wordsStore.updateWord(wordId, { deepThink: (current?.deepThink || '') + data.chunk })
        }
        break
      case 'done':
        wordsStore.updateWord(wordId, { status: 'done', statusText: '查询完成' })
        savedAnswer.value = wordsStore.trackedWords.find(w => w.id === wordId)?.quickAnswer || ''
        es.close()
        activeEventSources.delete(wordId)
        break
    }
  }

  es.onerror = () => {
    wordsStore.updateWord(wordId, { status: 'error', statusText: '连接中断或额度耗尽' })
    es.close()
    activeEventSources.delete(wordId)
  }
}

const wordClick = (id: string) => {
  wordsStore.activeWordId = id
}

const getTrackedWordClass = (w: TrackedWord) => {
  const isActive = w.id === wordsStore.activeWordId
  const base = 'tracked-word inline cursor-pointer transition-all duration-200 rounded'
  if (isActive) {
    return `${base} border-b-2 border-blue-600 bg-blue-200 ring-2 ring-blue-300`
  }
  if (w.status === 'loading') {
    return `${base} border-b-2 border-dashed border-yellow-400 bg-yellow-50 hover:bg-yellow-100`
  }
  if (w.status === 'done' && (w.quickAnswer || w.dictResult || w.deepThink)) {
    return `${base} border-b-2 border-blue-500 bg-blue-50 hover:bg-blue-100`
  }
  if (w.status === 'error') {
    return `${base} border-b-2 border-dashed border-red-400 bg-red-50 hover:bg-red-50`
  }
  return `${base} border-b-2 border-dashed border-blue-300 hover:bg-blue-50`
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
    const resp = await fetch('http://localhost:8000/api/history', {
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
    <main class="flex-1 max-w-3xl mx-auto p-10">
      <div class="flex items-center justify-between mb-4">
        <h1 class="text-3xl font-bold">论语·为政</h1>
        <div class="flex gap-2 text-sm">
          <button v-if="!editing && wordsStore.trackedWords.length > 0" @click="wordsStore.clearAll"
            class="text-gray-400 hover:text-red-500">清空追踪</button>
          <button v-if="!editing" @click="startEditing"
            class="px-3 py-1 border border-gray-300 rounded hover:bg-gray-100">编辑文本</button>
        </div>
      </div>

      <div v-if="editing" class="space-y-3">
        <textarea v-model="editText"
          class="w-full min-h-48 p-4 border border-gray-200 rounded-lg text-lg leading-loose resize-y focus:outline-none focus:ring-2 focus:ring-blue-300 font-sans"></textarea>
        <div class="flex gap-2 justify-end">
          <button @click="cancelEditing"
            class="px-4 py-1.5 border border-gray-300 rounded text-sm hover:bg-gray-100">取消</button>
          <button @click="saveEditing"
            class="px-4 py-1.5 bg-blue-600 text-white rounded text-sm hover:bg-blue-500">保存</button>
        </div>
      </div>

      <div v-else
        class="min-h-48 p-4 border border-gray-200 rounded-lg text-lg leading-loose whitespace-pre-wrap select-text">
        <template v-if="textSegments.length === 0">
          {{ editableText }}
        </template>
        <template v-else>
          <span v-for="(seg, i) in textSegments" :key="i">
            <span v-if="seg.type === 'text'">{{ seg.content }}</span>
            <span v-else :class="getTrackedWordClass(seg.word)" @click.stop="wordClick(seg.word.id)">
              {{ seg.word.word }}
              <span v-if="seg.word.quickAnswer.length > 0" class="text-sm text-yellow-800">({{ seg.word.quickAnswer }})</span>
              <span v-if="seg.word.status === 'loading'" class="ml-0.5">
                <span class="animate-spin inline-block w-3 h-3 border border-yellow-400 border-t-transparent rounded-full align-middle"></span>
              </span>
            </span>
          </span>
        </template>
      </div>

      <p class="text-sm text-gray-400 mt-4">💡 提示：用鼠标选中任意词语，即可触发查询。</p>
    </main>

    <Teleport to="body">
      <div v-if="selection.showTooltip"
        class="fixed bg-gray-900 text-white px-3 py-2 rounded-lg shadow-2xl flex gap-2 text-sm z-50 animate-in fade-in"
        :style="{ top: selection.y + 'px', left: selection.x + 'px', transform: 'translateX(-50%)' }">
        <button @click.stop="startQuery('quick')" class="hover:text-blue-300 transition-colors">⚡ 快速确认</button>
        <div class="w-px bg-gray-600"></div>
        <button @click.stop="startQuery('deep')" class="hover:text-purple-300 transition-colors">🧠 深度查询</button>
      </div>
    </Teleport>

    <aside id="query-panel"
      class="fixed right-0 top-12 bottom-0 w-105 bg-white shadow-2xl border-l border-gray-200 flex flex-col transition-transform duration-300 z-30"
      :class="showPanel ? 'translate-x-0' : 'translate-x-full'">
      <div class="flex items-center justify-between px-5 py-4 border-b border-gray-100">
        <div>
          <h2 class="text-lg font-bold">「{{ wordsStore.activeWord?.word }}」</h2>
          <span class="text-xs text-gray-400">{{ wordsStore.activeWord?.mode === 'deep' ? '深度查询' : '快速确认' }}</span>
        </div>
        <button @click="closePanel" class="text-gray-400 hover:text-gray-800 text-lg">✕</button>
      </div>

      <div v-if="wordsStore.activeWord" class="px-5 py-3 text-sm flex items-center gap-2 border-b border-gray-50">
        <span v-if="wordsStore.activeWord.status === 'loading'" class="relative flex h-2.5 w-2.5">
          <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75"></span>
          <span class="relative inline-flex rounded-full h-2.5 w-2.5 bg-blue-500"></span>
        </span>
        <span v-else-if="wordsStore.activeWord.status === 'done'" class="h-2.5 w-2.5 rounded-full bg-green-400"></span>
        <span v-else-if="wordsStore.activeWord.status === 'error'" class="h-2.5 w-2.5 rounded-full bg-red-400"></span>
        <span v-else class="h-2.5 w-2.5 rounded-full bg-gray-400"></span>
        <span :class="{
          'text-blue-600': wordsStore.activeWord.status === 'loading',
          'text-green-600': wordsStore.activeWord.status === 'done',
          'text-red-600': wordsStore.activeWord.status === 'error',
          'text-gray-600': wordsStore.activeWord.status === 'pending'
        }">{{ wordsStore.activeWord.statusText }}</span>
      </div>

      <div class="flex-1 overflow-y-auto p-5 space-y-4">
        <div v-if="wordsStore.activeWord?.quickAnswer" class="p-4 bg-blue-50 rounded-xl border border-blue-100">
          <h3 class="text-xs font-bold text-blue-700 mb-2 uppercase tracking-wide">⚡ 快速回答</h3>
          <p class="text-sm leading-relaxed whitespace-pre-wrap">{{ wordsStore.activeWord.quickAnswer }}</p>
        </div>

        <div v-if="wordsStore.activeWord?.dictResult" class="p-4 bg-emerald-50 rounded-xl border border-emerald-100">
          <h3 class="text-xs font-bold text-emerald-700 mb-2 uppercase tracking-wide">📖 汉典释义</h3>
          <p class="text-sm leading-relaxed whitespace-pre-wrap">{{ wordsStore.activeWord.dictResult }}</p>
        </div>

        <div v-if="wordsStore.activeWord?.deepThink" class="p-4 bg-purple-50 rounded-xl border border-purple-100">
          <h3 class="text-xs font-bold text-purple-700 mb-2 uppercase tracking-wide">🧠 深度分析</h3>
          <p class="text-sm leading-relaxed whitespace-pre-wrap">{{ wordsStore.activeWord.deepThink }}</p>
        </div>

        <div v-if="!wordsStore.activeWord?.quickAnswer && !wordsStore.activeWord?.dictResult && !wordsStore.activeWord?.deepThink && wordsStore.activeWord?.status !== 'loading'"
          class="text-center text-gray-400 text-sm mt-20">
          选中词语后点击查询
        </div>
      </div>

      <div v-if="wordsStore.activeWord && wordsStore.activeWord.status === 'done' && auth.user.logged_in"
        class="border-t border-gray-100 p-4 space-y-2">
        <textarea v-model="savedAnswer"
          class="w-full p-2 border border-gray-200 rounded-lg text-sm resize-none focus:outline-none focus:ring-1 focus:ring-blue-300"
          rows="2" placeholder="可修改 AI 回答后保存，或输入你自己的答案..."></textarea>
        <div class="flex items-center gap-2">
          <button @click="saveToHistory"
            class="flex-1 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-500 transition-colors">
            保存到历史
          </button>
          <span v-if="saveSuccess" class="text-green-600 text-sm">已保存</span>
        </div>
      </div>
    </aside>
  </div>
</template>

<style scoped>
.tracked-word.loading {
  border-bottom: 2px dashed #f59e0b;
  background-color: #fef3c7;
}
.tracked-word.done {
  border-bottom: 2px solid #3b82f6;
  background-color: #dbeafe;
}
.tracked-word.error {
  border-bottom: 2px dashed #ef4444;
  background-color: #fee2e2;
}
</style>
