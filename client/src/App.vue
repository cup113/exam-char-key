<script setup lang="ts">
import { ref, reactive, onMounted, watch, nextTick } from 'vue'
import { useWordsStore, type TrackedWord } from './stores/words'
import type { UserInfo } from './types'

const wordsStore = useWordsStore()

const user = ref<UserInfo>({ logged_in: false })
const editableText = ref(`子曰："为政以德，譬如北辰，居其所而众星共之。"
子曰："诗三百，一言以蔽之，曰：'思无邪'。"
孟懿子问孝。子曰："无违。"樊迟御，子告之曰："孟孙问孝于我，我对曰'无违'。"樊迟曰："何谓也？"子曰："生，事之以礼；死，葬之以礼，祭之以礼。"`)

const selection = reactive({
  word: '',
  context: '',
  showTooltip: false,
  x: 0,
  y: 0,
})

const showPanel = ref(false)
const textEl = ref<HTMLDivElement | null>(null)
const activeEventSources = new Map<string, EventSource>()

onMounted(async () => {
  try {
    const resp = await fetch('http://localhost:8000/auth/me', { credentials: 'include' })
    user.value = await resp.json()
  } catch {
    user.value = { logged_in: false }
  }
  initTextContent()
})

watch(() => wordsStore.activeWordId, (id) => {
  showPanel.value = id !== null
})

const initTextContent = () => {
  if (textEl.value) {
    textEl.value.innerText = editableText.value
  }
}

const handleMouseUp = (e: MouseEvent) => {
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

  const parentNode = sel.anchorNode?.parentElement
  const context = parentNode?.innerText || text

  selection.word = text
  selection.context = context
  selection.x = e.pageX
  selection.y = e.pageY - 50
  selection.showTooltip = true
}

const wrapWordInDOM = (word: string, wordId: string) => {
  const sel = window.getSelection()
  if (!sel || !sel.rangeCount) return

  const range = sel.getRangeAt(0)
  if (range.toString() !== word) return

  const span = document.createElement('span')
  span.className = 'tracked-word'
  span.dataset.wordId = wordId
  span.textContent = word
  span.addEventListener('click', (e) => {
    e.stopPropagation()
    wordClick(wordId)
  })

  range.deleteContents()
  range.insertNode(span)

  sel.removeAllRanges()
}

const startQuery = (mode: 'quick' | 'deep') => {
  const wordId = wordsStore.addWord(selection.word, selection.context, mode)
  selection.showTooltip = false
  wordsStore.activeWordId = wordId

  nextTick(() => wrapWordInDOM(selection.word, wordId))

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
      updateDOMWordStyle(wordId, 'error')
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
        updateDOMWordStyle(wordId, 'done')
        es.close()
        activeEventSources.delete(wordId)
        break
    }
  }

  es.onerror = () => {
    wordsStore.updateWord(wordId, { status: 'error', statusText: '连接中断或额度耗尽' })
    updateDOMWordStyle(wordId, 'error')
    es.close()
    activeEventSources.delete(wordId)
  }
}

const updateDOMWordStyle = (wordId: string, status: 'loading' | 'done' | 'error') => {
  const el = document.querySelector(`[data-word-id="${wordId}"]`) as HTMLElement
  if (!el) return

  el.classList.remove('loading', 'done', 'error')
  el.classList.add(status)
}

const wordClick = (id: string) => {
  wordsStore.activeWordId = id
}

const getWordClass = (word: TrackedWord) => {
  const base = 'inline cursor-pointer transition-all duration-200'
  const hasAnswer = word.quickAnswer || word.dictResult || word.deepThink
  if (!hasAnswer) {
    return `${base} border-b border-dashed border-blue-400 hover:bg-blue-100`
  }
  if (word.status === 'done') {
    return `${base} border-b-2 border-blue-500 bg-blue-50 hover:bg-blue-100`
  }
  if (word.status === 'error') {
    return `${base} border-b border-dashed border-red-400 hover:bg-red-50`
  }
  return `${base} border-b border-dashed border-yellow-400 hover:bg-yellow-50`
}

const closePanel = () => {
  showPanel.value = false
  wordsStore.activeWordId = null
}

const logout = () => fetch('http://localhost:8000/auth/logout', { method: 'POST', credentials: 'include' }).then(() => location.reload())
</script>

<template>
  <div class="min-h-screen bg-gray-50 text-gray-800 font-sans flex" @mouseup="handleMouseUp">
    <header
      class="fixed top-0 left-0 right-0 h-12 bg-white border-b border-gray-200 flex items-center justify-between px-6 z-40">
      <span class="font-bold text-lg">📖 划词查询</span>
      <div class="flex items-center gap-4 text-sm">
        <span v-if="user.logged_in" class="text-gray-500">{{ user.user_id }}</span>
        <a v-if="!user.logged_in" href="http://localhost:8000/auth/github/login"
          class="px-3 py-1 bg-gray-900 text-white rounded hover:bg-gray-700">GitHub 登录</a>
        <a v-if="!user.logged_in" href="http://localhost:8000/auth/gitee/login"
          class="px-3 py-1 bg-green-600 text-white rounded hover:bg-green-500">Gitee 登录</a>
        <button v-if="user.logged_in" @click="logout" class="text-gray-400 hover:text-red-500">退出</button>
      </div>
    </header>

    <main class="flex-1 max-w-3xl mx-auto p-10 pt-20">
      <h1 class="text-3xl font-bold mb-4">论语·为政</h1>
      <div contenteditable="true" ref="textEl"
        class="min-h-48 p-4 border border-gray-200 rounded-lg text-lg leading-loose focus:outline-none focus:ring-2 focus:ring-blue-300"
        @input="(e) => editableText = (e.target as HTMLElement).innerText"></div>
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
    </aside>

    <div v-if="wordsStore.trackedWords.length > 0"
      class="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 z-40">
      <div class="px-6 py-2 border-b border-gray-100 flex items-center justify-between text-xs">
        <span class="text-gray-400">正在追踪的词 ({{ wordsStore.trackedWords.length }})</span>
        <button @click="wordsStore.clearAll" class="text-gray-400 hover:text-red-500">清空全部</button>
      </div>
      <div class="max-h-20 overflow-y-auto px-6 py-2">
        <div class="flex flex-wrap gap-2">
          <span v-for="word in wordsStore.trackedWords" :key="word.id" @click="wordClick(word.id)"
            :class="getWordClass(word)">
            {{ word.word }}
            <span v-if="word.status === 'done' && word.quickAnswer" class="text-gray-400 text-xs ml-0.5">
              ({{ word.quickAnswer.slice(0, 10) }}{{ word.quickAnswer.length > 10 ? '...' : '' }})
            </span>
            <span v-if="word.status === 'loading'" class="ml-1">
              <span class="animate-spin inline-block w-3 h-3 border border-blue-400 border-t-transparent rounded-full"></span>
            </span>
          </span>
        </div>
      </div>
    </div>
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