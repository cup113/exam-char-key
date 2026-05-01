import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { useLocalStorage } from '@vueuse/core'
import type { CorpusEntry } from '@/types'

export interface TrackedWord {
  id: string
  word: string
  context: string
  offset: number
  mode: 'quick' | 'deep'
  status: 'pending' | 'loading' | 'done' | 'error'
  quickAnswer: string
  dictResult: string
  deepThink: string
  corpusEntries: CorpusEntry[]
  statusText: string
  startTime: number
}

async function readSSEStream(
  response: Response,
  onChunk: (chunk: string) => void,
): Promise<void> {
  const reader = response.body!.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  try {
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })

      const lines = buffer.split('\n')
      buffer = lines.pop() || ''

      for (const line of lines) {
        const trimmed = line.trim()
        if (!trimmed.startsWith('data: ')) continue
        const payload = trimmed.slice(6)
        if (payload === '[DONE]') return
        try {
          const data = JSON.parse(payload)
          if (data.chunk) onChunk(data.chunk)
        } catch {
          // skip malformed JSON
        }
      }
    }
  } catch (err) {
    if (err instanceof DOMException && err.name === 'AbortError') throw err
    console.error('SSE read error:', err)
    throw err
  }
}

export const useWordsStore = defineStore('words', () => {
  const trackedWords = useLocalStorage<TrackedWord[]>('ECK_tracked-words', [])

  const activeWordId = ref<string | null>(null)

  const activeWord = computed(() =>
    trackedWords.value.find(w => w.id === activeWordId.value) || null
  )

  const activeControllers = new Map<string, AbortController>()

  const editableText = useLocalStorage('ECK_editable-text', `子曰："为政以德，譬如北辰，居其所而众星共之。"
子曰："诗三百，一言以蔽之，曰：'思无邪'。"
孟懿子问孝。子曰："无违。"樊迟御，子告之曰："孟孙问孝于我，我对曰'无违'。"樊迟曰："何谓也？"子曰："生，事之以礼；死，葬之以礼，祭之以礼。"`)

  const editing = ref(false)
  const editText = ref('')

  function startEditing() {
    editText.value = editableText.value
    editing.value = true
  }

  function saveEditing() {
    editableText.value = editText.value
    editing.value = false
    clearAll()
  }

  function cancelEditing() {
    editing.value = false
  }

  function addWord(word: string, context: string, mode: 'quick' | 'deep', offset: number) {
    const id = `${Date.now()}-${Math.random().toString(36).slice(2)}`
    trackedWords.value.push({
      id,
      word,
      context,
      offset,
      mode,
      status: 'pending',
      quickAnswer: '',
      dictResult: '',
      deepThink: '',
      corpusEntries: [],
      statusText: '等待中...',
      startTime: Date.now(),
    })
    return id
  }

  function updateWord(id: string, updates: Partial<TrackedWord>) {
    const word = trackedWords.value.find(w => w.id === id)
    if (word) {
      Object.assign(word, updates)
    }
  }

  function abortWord(id: string) {
    const ctrl = activeControllers.get(id)
    if (ctrl) {
      ctrl.abort()
      activeControllers.delete(id)
    }
  }

  function abortAll() {
    for (const ctrl of activeControllers.values()) {
      ctrl.abort()
    }
    activeControllers.clear()
  }

  // --- 各端点请求 ---

  async function fetchQuick(wordId: string, word: string, context: string, signal: AbortSignal) {
    updateWord(wordId, { statusText: '正在快速解答...' })
    const url = new URL('/api/query/quick', location.origin)
    url.searchParams.set('word', word)
    url.searchParams.set('context', context)

    const resp = await fetch(url.toString(), { signal })
    if (!resp.ok) {
      const err = await resp.json().catch(() => ({ detail: '快速查询失败' }))
      throw new Error(err.detail || `HTTP ${resp.status}`)
    }

    await readSSEStream(resp, (chunk) => {
      const current = trackedWords.value.find(w => w.id === wordId)
      updateWord(wordId, { quickAnswer: (current?.quickAnswer || '') + chunk })
    })
    updateWord(wordId, { statusText: '快速查询完成' })
  }

  async function fetchCorpus(wordId: string, word: string, signal: AbortSignal) {
    updateWord(wordId, { statusText: '正在查询语料库...' })
    const url = new URL('/api/query/corpus', location.origin)
    url.searchParams.set('word', word)

    const resp = await fetch(url.toString(), { signal })
    if (!resp.ok) {
      const err = await resp.json().catch(() => ({ detail: '语料库查询失败' }))
      throw new Error(err.detail || `HTTP ${resp.status}`)
    }

    const data = await resp.json()
    updateWord(wordId, { corpusEntries: data.entries })
  }

  async function fetchDictionary(wordId: string, word: string, signal: AbortSignal) {
    updateWord(wordId, { statusText: '正在查阅汉典...' })
    const url = new URL('/api/query/dictionary', location.origin)
    url.searchParams.set('word', word)

    const resp = await fetch(url.toString(), { signal })
    if (!resp.ok) {
      const err = await resp.json().catch(() => ({ detail: '汉典查询失败' }))
      throw new Error(err.detail || `HTTP ${resp.status}`)
    }

    const data = await resp.json()
    updateWord(wordId, { dictResult: data.result })
  }

  async function fetchDeep(wordId: string, word: string, context: string, signal: AbortSignal) {
    updateWord(wordId, { statusText: '正在深度思考...' })
    const url = new URL('/api/query/deep', location.origin)
    url.searchParams.set('word', word)
    url.searchParams.set('context', context)

    const resp = await fetch(url.toString(), { signal })
    if (!resp.ok) {
      const err = await resp.json().catch(() => ({ detail: '深度分析失败' }))
      throw new Error(err.detail || `HTTP ${resp.status}`)
    }

    await readSSEStream(resp, (chunk) => {
      const current = trackedWords.value.find(w => w.id === wordId)
      updateWord(wordId, { deepThink: (current?.deepThink || '') + chunk })
    })
  }

  // --- 核心编排 ---

  async function runQuery(wordId: string, word: string, context: string, mode: 'quick' | 'deep') {
    const controller = new AbortController()
    activeControllers.set(wordId, controller)
    const signal = controller.signal

    try {
      const quickP = fetchQuick(wordId, word, context, signal).catch(err => {
        if (err instanceof DOMException && err.name === 'AbortError') throw err
        console.error('quick failed', err)
        updateWord(wordId, { statusText: `快速查询失败` })
      })
      const corpusP = fetchCorpus(wordId, word, signal).catch(err => {
        if (err instanceof DOMException && err.name === 'AbortError') throw err
        console.error('corpus failed', err)
      })
      const dictP = fetchDictionary(wordId, word, signal).catch(err => {
        if (err instanceof DOMException && err.name === 'AbortError') throw err
        console.error('dictionary failed', err)
      })

      await Promise.all([quickP, corpusP, dictP])

      if (signal.aborted) return

      if (mode === 'deep') {
        updateWord(wordId, { statusText: '正在准备深度分析...' })
        await fetchDeep(wordId, word, context, signal)
      }

      if (!signal.aborted) {
        updateWord(wordId, { status: 'done', statusText: '查询完成' })
      }
    } catch (err) {
      if (err instanceof DOMException && err.name === 'AbortError') return
      const message = err instanceof Error ? err.message : '未知错误'
      updateWord(wordId, { status: 'error', statusText: `错误: ${message}` })
    } finally {
      activeControllers.delete(wordId)
    }
  }

  function queryWord(word: string, context: string, mode: 'quick' | 'deep', offset: number): string {
    const wordId = addWord(word, context, mode, offset)
    activeWordId.value = wordId
    updateWord(wordId, { status: 'loading', statusText: '正在连接...' })
    runQuery(wordId, word, context, mode)
    return wordId
  }

  function removeWord(id: string) {
    abortWord(id)
    trackedWords.value = trackedWords.value.filter(w => w.id !== id)
    if (activeWordId.value === id) {
      activeWordId.value = null
    }
  }

  function clearAll() {
    abortAll()
    trackedWords.value = []
    activeWordId.value = null
  }

  function retryWord(id: string) {
    const word = trackedWords.value.find(w => w.id === id)
    if (!word) return

    abortWord(id)

    word.status = 'loading'
    word.statusText = '正在连接...'
    word.quickAnswer = ''
    word.dictResult = ''
    word.deepThink = ''
    word.corpusEntries = []
    word.startTime = Date.now()

    runQuery(id, word.word, word.context, word.mode)
  }

  return {
    trackedWords,
    activeWordId,
    activeWord,
    editableText,
    editing,
    editText,
    addWord,
    updateWord,
    removeWord,
    clearAll,
    abortAll,
    queryWord,
    retryWord,
    startEditing,
    saveEditing,
    cancelEditing,
  }
})