import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'

vi.mock('@/services/queryService', () => ({
  queryQuick: vi.fn(),
  queryCorpus: vi.fn(() => []),
  queryDictionary: vi.fn(() => ''),
  queryDeep: vi.fn(),
}))

vi.mock('@/services/documentService', () => ({
  createDoc: vi.fn(),
}))

vi.mock('@/utils/document', () => ({
  toSnapshot: vi.fn((w) => ({
    word: w.word,
    context: w.context,
    offset: w.offset,
    mode: w.mode,
    quickAnswer: w.quickAnswer,
    dictResult: w.dictResult,
    deepThink: w.deepThink,
    corpusEntries: w.corpusEntries,
  })),
  fromSnapshot: vi.fn((s) => ({
    id: `${Date.now()}-test`,
    ...s,
    status: 'done',
    quickStatus: 'done',
    corpusStatus: 'done',
    dictStatus: 'done',
    deepStatus: s.deepThink ? 'done' : 'idle',
    startTime: Date.now(),
  })),
}))

vi.mock('./auth', () => ({
  useAuthStore: vi.fn(() => ({
    fetchQuota: vi.fn(),
  })),
}))

import { useWordsStore } from './words'
import * as queryService from '@/services/queryService'
import * as documentService from '@/services/documentService'

describe('useWordsStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    localStorage.clear()
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  it('starts with empty state', () => {
    const store = useWordsStore()
    expect(store.trackedWords).toEqual([])
    expect(store.activeWordId).toBeNull()
    expect(store.activeWord).toBeNull()
    expect(store.isDirty).toBe(false)
    expect(store.editing).toBe(false)
  })

  it('adds a word', () => {
    const store = useWordsStore()
    const id = store.addWord('之', '学而时习之', 'quick', 3)
    expect(store.trackedWords).toHaveLength(1)
    expect(store.trackedWords[0].word).toBe('之')
    expect(store.trackedWords[0].context).toBe('学而时习之')
    expect(store.trackedWords[0].mode).toBe('quick')
    expect(store.trackedWords[0].offset).toBe(3)
    expect(store.trackedWords[0].status).toBe('pending')
    expect(store.trackedWords[0].quickStatus).toBe('idle')
    expect(store.trackedWords[0].id).toBe(id)
    expect(store.isDirty).toBe(true)
  })

  it('removes a word', () => {
    const store = useWordsStore()
    const id1 = store.addWord('之', '', 'quick', 0)
    store.addWord('乎', '', 'quick', 0)
    store.removeWord(id1)
    expect(store.trackedWords).toHaveLength(1)
    expect(store.trackedWords[0].word).toBe('乎')
  })

  it('removes active word and clears reference', () => {
    const store = useWordsStore()
    const id = store.addWord('之', '', 'quick', 0)
    store.activeWordId = id
    store.removeWord(id)
    expect(store.activeWordId).toBeNull()
    expect(store.activeWord).toBeNull()
  })

  it('clears all words', () => {
    const store = useWordsStore()
    store.addWord('之', '', 'quick', 0)
    store.addWord('乎', '', 'quick', 0)
    store.clearAll()
    expect(store.trackedWords).toEqual([])
    expect(store.activeWordId).toBeNull()
    expect(store.isDirty).toBe(true)
  })

  it('sets active word correctly', () => {
    const store = useWordsStore()
    const id = store.addWord('之', '', 'quick', 0)
    store.activeWordId = id
    expect(store.activeWord).not.toBeNull()
    expect(store.activeWord!.word).toBe('之')
  })

  it('updates word fields', () => {
    const store = useWordsStore()
    const id = store.addWord('之', '', 'quick', 0)
    store.updateWord(id, { quickAnswer: '代词' })
    expect(store.trackedWords[0].quickAnswer).toBe('代词')
  })

  it('handles editing lifecycle', () => {
    const store = useWordsStore()
    const original = store.editableText
    store.startEditing()
    expect(store.editing).toBe(true)
    expect(store.editText).toBe(original)
    store.cancelEditing()
    expect(store.editing).toBe(false)
    store.startEditing()
    store.editText = '新文本'
    store.saveEditing()
    expect(store.editableText).toBe('新文本')
    expect(store.editing).toBe(false)
    expect(store.isDirty).toBe(true)
  })

  it('queryWord sets loading state and starts query', async () => {
    const store = useWordsStore()
    const id = store.queryWord('之', '学而时习之', 'quick', 0)
    const word = store.trackedWords[0]
    expect(word.status).toBe('loading')
    expect(word.quickStatus).toBe('loading')
    expect(word.corpusStatus).toBe('loading')
    expect(word.dictStatus).toBe('loading')
    expect(store.activeWordId).toBe(id)
  })

  it('saveSnapshot calls createDoc and resets dirty', async () => {
    vi.mocked(documentService.createDoc).mockResolvedValue({ id: 1, title: '测试' } as any)
    const store = useWordsStore()
    store.addWord('之', '', 'quick', 0)
    store.isDirty = true
    const result = await store.saveSnapshot('测试文档', false)
    expect(documentService.createDoc).toHaveBeenCalled()
    expect(result).toEqual({ id: 1, title: '测试' })
    expect(store.isDirty).toBe(false)
  })

  it('importDocument clears current and loads from doc', () => {
    const store = useWordsStore()
    store.addWord('旧词', '', 'quick', 0)
    const doc = {
      id: 1,
      user_id: 'github:test',
      title: '测试',
      source_text: '新文本',
      tracked_words: [{ word: '新词', context: '新文本', offset: 0, mode: 'quick', quickAnswer: '', dictResult: '', deepThink: '', corpusEntries: [] }],
      is_public: false,
      public_uuid: null,
      created_at: '2025-01-01',
      updated_at: '2025-01-01',
    }
    store.importDocument(doc as any)
    expect(store.editableText).toBe('新文本')
    expect(store.trackedWords).toHaveLength(1)
    expect(store.trackedWords[0].word).toBe('新词')
    expect(store.isDirty).toBe(false)
  })

  it('retryWord resets fields and re-runs', () => {
    const store = useWordsStore()
    const id = store.addWord('之', '', 'quick', 0)
    store.updateWord(id, { status: 'done', quickAnswer: '旧结果', dictResult: '旧' })
    store.retryWord(id)
    const w = store.trackedWords[0]
    expect(w.status).toBe('loading')
    expect(w.quickAnswer).toBe('')
    expect(w.dictResult).toBe('')
    expect(w.corpusEntries).toEqual([])
    expect(w.quickStatus).toBe('loading')
    expect(w.corpusStatus).toBe('loading')
    expect(w.dictStatus).toBe('loading')
    expect(w.deepStatus).toBe('idle')
  })

  it('abortAll does not throw on empty controllers', () => {
    const store = useWordsStore()
    expect(() => store.abortAll()).not.toThrow()
  })

  it('retryDictionary resets dict fields', () => {
    const store = useWordsStore()
    const id = store.addWord('之', '', 'quick', 0)
    store.updateWord(id, { dictResult: '旧字典', dictStatus: 'done' })
    store.retryDictionary(id)
    expect(store.trackedWords[0].dictResult).toBe('')
    expect(store.trackedWords[0].dictStatus).toBe('loading')
  })

  it('upgradeToDeep sets deep mode', () => {
    const store = useWordsStore()
    const id = store.addWord('之', '', 'quick', 0)
    store.upgradeToDeep(id)
    expect(store.trackedWords[0].mode).toBe('deep')
    expect(store.trackedWords[0].status).toBe('loading')
    expect(store.trackedWords[0].deepStatus).toBe('loading')
  })
})
