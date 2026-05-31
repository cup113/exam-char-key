import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'

vi.mock('@/services/documentService', () => ({
  createDoc: vi.fn(() => Promise.resolve({ id: 1, title: 'auto-save' })),
}))

vi.mock('@/stores/auth', () => ({
  useAuthStore: vi.fn(() => ({ fetchQuota: vi.fn() })),
}))

import { useDocumentLoader } from './useDocumentLoader'
import { useWordsStore } from '@/stores/words'

function makeDoc(overrides = {}) {
  return {
    id: 1,
    user_id: 'github:test',
    title: '文档',
    source_text: '内容',
    tracked_words: [],
    is_public: false,
    public_uuid: null,
    created_at: '2025-01-01',
    updated_at: '2025-01-01',
    ...overrides,
  }
}

describe('useDocumentLoader', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    localStorage.clear()
  })

  it('loads document directly when no conflict', async () => {
    const { loadDocument, confirmState } = useDocumentLoader()
    const store = useWordsStore()

    const result = await loadDocument(makeDoc())
    expect(result).toBe(true)
    expect(store.editableText).toBe('内容')
    expect(confirmState.value).toBeNull()
  })

  it('loads document after dirty conflict resolved as discard', async () => {
    const { loadDocument, confirmState } = useDocumentLoader()
    const store = useWordsStore()
    store.addWord('之', '', 'quick', 0)
    store.isDirty = true

    const promise = loadDocument(makeDoc({ source_text: '新内容' }))
    expect(confirmState.value).not.toBeNull()
    expect(confirmState.value!.show).toBe(true)

    confirmState.value!.resolve('discard')
    const result = await promise
    expect(result).toBe(true)
    expect(store.editableText).toBe('新内容')
  })

  it('cancels loading with dirty conflict', async () => {
    const { loadDocument, confirmState } = useDocumentLoader()
    const store = useWordsStore()
    store.addWord('之', '', 'quick', 0)
    store.isDirty = true

    const promise = loadDocument(makeDoc())
    confirmState.value!.resolve('cancel')
    const result = await promise
    expect(result).toBe(false)
  })

  it('saves then loads on dirty conflict', async () => {
    const { loadDocument, confirmState } = useDocumentLoader()
    const store = useWordsStore()
    store.addWord('之', '', 'quick', 0)
    store.isDirty = true

    const promise = loadDocument(makeDoc({ source_text: '保存后加载' }))
    confirmState.value!.resolve('save')
    const result = await promise
    expect(result).toBe(true)
    expect(store.editableText).toBe('保存后加载')
  })
})
