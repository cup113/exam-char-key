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

export const useWordsStore = defineStore('words', () => {
  const trackedWords = useLocalStorage<TrackedWord[]>('ECK_tracked-words', [])

  const activeWordId = ref<string | null>(null)

  const activeWord = computed(() =>
    trackedWords.value.find(w => w.id === activeWordId.value) || null
  )

  const activeEventSources = new Map<string, EventSource>()

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

  function removeWord(id: string) {
    const es = activeEventSources.get(id)
    if (es) {
      es.close()
      activeEventSources.delete(id)
    }
    trackedWords.value = trackedWords.value.filter(w => w.id !== id)
    if (activeWordId.value === id) {
      activeWordId.value = null
    }
  }

  function clearAll() {
    for (const es of activeEventSources.values()) {
      es.close()
    }
    activeEventSources.clear()
    trackedWords.value = []
    activeWordId.value = null
  }

  function cleanupSSE() {
    for (const es of activeEventSources.values()) {
      es.close()
    }
    activeEventSources.clear()
  }

  function connectSSE(wordId: string, word: string, context: string, mode: 'quick' | 'deep') {
    const url = new URL(location.origin + '/api/query')
    url.searchParams.set('word', word)
    url.searchParams.set('context', context)
    url.searchParams.set('mode', mode)

    const es = new EventSource(url.toString())
    activeEventSources.set(wordId, es)

    es.onmessage = (event) => {
      const data = JSON.parse(event.data)

      if (data.error) {
        updateWord(wordId, { status: 'error', statusText: `错误: ${data.error}` })
        es.close()
        activeEventSources.delete(wordId)
        return
      }

      switch (data.step) {
        case 'quick_answer':
          if (data.status === 'start') updateWord(wordId, { statusText: '正在快速解答...' })
          if (data.chunk) {
            const current = trackedWords.value.find(w => w.id === wordId)
            updateWord(wordId, { quickAnswer: (current?.quickAnswer || '') + data.chunk })
          }
          break
        case 'corpus':
          if (data.status === 'fetching') updateWord(wordId, { statusText: '正在查询语料库...' })
          if (data.entries) {
            updateWord(wordId, { corpusEntries: data.entries })
          }
          break
        case 'dictionary':
          if (data.status === 'fetching') updateWord(wordId, { statusText: '正在查阅汉典...' })
          if (data.result) {
            updateWord(wordId, {
              dictResult: data.result,
              statusText: mode === 'quick' ? '查询完成' : '字典查询完成'
            })
          }
          break
        case 'deep_think':
          if (data.status === 'start') updateWord(wordId, { statusText: '正在深度思考...' })
          if (data.chunk) {
            const current = trackedWords.value.find(w => w.id === wordId)
            updateWord(wordId, { deepThink: (current?.deepThink || '') + data.chunk })
          }
          break
        case 'done':
          updateWord(wordId, { status: 'done', statusText: '查询完成' })
          es.close()
          activeEventSources.delete(wordId)
          break
      }
    }

    es.onerror = (e) => {
      updateWord(wordId, {
        status: 'error',
        statusText: `连接中断。请检查网络后重试。如问题持续，可能是 API 额度已耗尽。\n${e}`
      })
      es.close()
      activeEventSources.delete(wordId)
    }
  }

  function queryWord(word: string, context: string, mode: 'quick' | 'deep', offset: number): string {
    const wordId = addWord(word, context, mode, offset)
    activeWordId.value = wordId
    updateWord(wordId, { status: 'loading', statusText: '正在连接...' })
    connectSSE(wordId, word, context, mode)
    return wordId
  }

  function retryWord(id: string) {
    const word = trackedWords.value.find(w => w.id === id)
    if (!word) return

    const es = activeEventSources.get(id)
    if (es) {
      es.close()
      activeEventSources.delete(id)
    }

    word.status = 'loading'
    word.statusText = '正在连接...'
    word.quickAnswer = ''
    word.dictResult = ''
    word.deepThink = ''
    word.corpusEntries = []
    word.startTime = Date.now()

    connectSSE(id, word.word, word.context, word.mode)
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
    cleanupSSE,
    queryWord,
    retryWord,
    startEditing,
    saveEditing,
    cancelEditing,
  }
})
