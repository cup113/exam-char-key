import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { setActivePinia, createPinia } from 'pinia'
import { ref } from 'vue'

vi.mock('vue-router', () => ({
  useRoute: vi.fn(() => ({ params: { uuid: 'test-uuid' } })),
  useRouter: vi.fn(() => ({ push: vi.fn() })),
}))

vi.mock('@/stores/words', () => ({
  useWordsStore: vi.fn(),
}))

vi.mock('@/composables/useDocumentLoader', () => ({
  useDocumentLoader: vi.fn(),
}))

vi.mock('@/services/documentService', () => ({
  getPublicDoc: vi.fn(),
}))

import { useRoute, useRouter } from 'vue-router'
import { useWordsStore } from '@/stores/words'
import { useDocumentLoader } from '@/composables/useDocumentLoader'
import * as documentService from '@/services/documentService'
import SharedDocumentView from './SharedDocumentView.vue'
import TextContent from '@/components/TextContent.vue'

function flushMicrotasks() {
  return new Promise(resolve => setTimeout(resolve, 0))
}

function makeDoc(overrides = {}) {
  return {
    id: 1,
    user_id: 'github:test',
    title: '论语选段',
    source_text: '学而时习之',
    tracked_words: [
      { word: '学而', offset: 0, context: '学而时习之', mode: 'quick' as const, quickAnswer: '学习', dictResult: '', deepThink: '', corpusEntries: [] },
    ],
    is_public: true,
    public_uuid: 'test-uuid',
    created_at: '2025-06-01T10:00:00',
    updated_at: '2025-06-01T10:00:00',
    ...overrides,
  }
}

describe('SharedDocumentView', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.mocked(useRoute).mockReturnValue({ params: { uuid: 'test-uuid' } } as any)
  })

  it('shows loading state initially', () => {
    vi.mocked(documentService.getPublicDoc).mockReturnValue(new Promise(() => {}))
    vi.mocked(useWordsStore).mockReturnValue({} as any)
    vi.mocked(useDocumentLoader).mockReturnValue({ loadDocument: vi.fn(), confirmState: ref(null) })

    const wrapper = mount(SharedDocumentView)
    expect(wrapper.text()).toContain('加载中')
  })

  it('shows error when document loading fails', async () => {
    vi.mocked(useWordsStore).mockReturnValue({} as any)
    vi.mocked(useDocumentLoader).mockReturnValue({ loadDocument: vi.fn(), confirmState: ref(null) })
    vi.mocked(documentService.getPublicDoc).mockRejectedValue(new Error('文档不存在'))

    const wrapper = mount(SharedDocumentView)
    await flushMicrotasks()
    expect(wrapper.text()).toContain('文档不存在')
  })

  it('renders document when loaded successfully', async () => {
    vi.mocked(useWordsStore).mockReturnValue({} as any)
    vi.mocked(useDocumentLoader).mockReturnValue({ loadDocument: vi.fn(), confirmState: ref(null) })
    vi.mocked(documentService.getPublicDoc).mockResolvedValue(makeDoc())

    const wrapper = mount(SharedDocumentView)
    await flushMicrotasks()
    expect(wrapper.text()).toContain('论语选段')
    expect(wrapper.text()).toContain('1 个词语')
    expect(wrapper.text()).toContain('继续查询')
  })

  it('opens word details on word click', async () => {
    vi.mocked(useWordsStore).mockReturnValue({} as any)
    vi.mocked(useDocumentLoader).mockReturnValue({ loadDocument: vi.fn(), confirmState: ref(null) })
    vi.mocked(documentService.getPublicDoc).mockResolvedValue(makeDoc())

    const wrapper = mount(SharedDocumentView)
    await flushMicrotasks()

    const tc = wrapper.findComponent(TextContent)
    tc.vm.$emit('word-click', 'doc-0')
    await flushMicrotasks()

    expect(wrapper.text()).toContain('学而')
    expect(wrapper.text()).toContain('文档快照')
  })

  it('calls loadDocument on continue query', async () => {
    const loadDocument = vi.fn().mockResolvedValue(true)
    const push = vi.fn()
    vi.mocked(useRouter).mockReturnValue({ push } as any)
    vi.mocked(useWordsStore).mockReturnValue({ closeDocument: vi.fn() } as any)
    vi.mocked(useDocumentLoader).mockReturnValue({ loadDocument, confirmState: ref(null) })
    vi.mocked(documentService.getPublicDoc).mockResolvedValue(makeDoc())

    const wrapper = mount(SharedDocumentView)
    await flushMicrotasks()

    await wrapper.find('[data-umami-event="shared-continue"]').trigger('click')
    expect(loadDocument).toHaveBeenCalled()
    expect(vi.mocked(useWordsStore)().closeDocument).toHaveBeenCalled()
  })
})
