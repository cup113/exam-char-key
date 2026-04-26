import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { useStorage } from '@vueuse/core'

export interface TrackedWord {
  id: string
  word: string
  context: string
  mode: 'quick' | 'deep'
  status: 'pending' | 'loading' | 'done' | 'error'
  quickAnswer: string
  dictResult: string
  deepThink: string
  statusText: string
  startTime: number
}

export const useWordsStore = defineStore('words', () => {
  const trackedWords = useStorage<TrackedWord[]>('tracked-words', [])

  const activeWordId = ref<string | null>(null)

  const activeWord = computed(() =>
    trackedWords.value.find(w => w.id === activeWordId.value) || null
  )

  function addWord(word: string, context: string, mode: 'quick' | 'deep') {
    const id = `${Date.now()}-${Math.random().toString(36).slice(2)}`
    trackedWords.value.push({
      id,
      word,
      context,
      mode,
      status: 'pending',
      quickAnswer: '',
      dictResult: '',
      deepThink: '',
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
    trackedWords.value = trackedWords.value.filter(w => w.id !== id)
    if (activeWordId.value === id) {
      activeWordId.value = null
    }
  }

  function clearAll() {
    trackedWords.value = []
    activeWordId.value = null
  }

  return {
    trackedWords,
    activeWordId,
    activeWord,
    addWord,
    updateWord,
    removeWord,
    clearAll,
  }
})