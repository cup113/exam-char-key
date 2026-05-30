import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount } from '@vue/test-utils'
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

vi.mock('@/services/historyService', () => ({
  createHistory: vi.fn(),
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

vi.mock('@/stores/auth', () => ({
  useAuthStore: vi.fn(() => ({ fetchUser: vi.fn(), fetchQuota: vi.fn(), user: { logged_in: false } })),
}))

import { useWordsStore } from '@/stores/words'
import * as historyService from '@/services/historyService'
import HomeView from './HomeView.vue'

function flushMicrotasks() {
  return new Promise(resolve => setTimeout(resolve, 0))
}

describe('HomeView', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    localStorage.clear()
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  it('renders TextContent, SelectionTooltip, QueryPanel', () => {
    const wrapper = mount(HomeView, {
      global: { stubs: { Teleport: true } },
    })
    expect(wrapper.findComponent({ name: 'TextContent' }).exists()).toBe(true)
    expect(wrapper.findComponent({ name: 'SelectionTooltip' }).exists()).toBe(true)
    expect(wrapper.findComponent({ name: 'QueryPanel' }).exists()).toBe(true)
  })

  it('opens query panel when activeWordId is set', async () => {
    const wrapper = mount(HomeView, {
      global: { stubs: { Teleport: true } },
    })
    await flushMicrotasks()

    const store = useWordsStore()
    store.queryWord('习', '学而时习之', 'quick', 3)
    await flushMicrotasks()

    const panel = wrapper.findComponent({ name: 'QueryPanel' })
    expect(panel.props('show')).toBe(true)
  })

  it('closes panel and clears activeWordId on closePanel', async () => {
    const wrapper = mount(HomeView, {
      global: { stubs: { Teleport: true } },
    })
    await flushMicrotasks()

    const store = useWordsStore()
    const id = store.queryWord('习', '学而时习之', 'quick', 3)
    await flushMicrotasks()

    const panel = wrapper.findComponent({ name: 'QueryPanel' })
    panel.vm.$emit('close')
    await flushMicrotasks()

    expect(store.activeWordId).toBeNull()
  })

  it('saves to history successfully', async () => {
    vi.mocked(historyService.createHistory).mockResolvedValue({ id: 1 } as any)

    const wrapper = mount(HomeView, {
      global: { stubs: { Teleport: true } },
    })
    await flushMicrotasks()

    const store = useWordsStore()
    store.queryWord('习', '学而时习之', 'quick', 3)
    await flushMicrotasks()

    const panel = wrapper.findComponent({ name: 'QueryPanel' })
    panel.vm.$emit('save')
    await flushMicrotasks()

    expect(historyService.createHistory).toHaveBeenCalled()
  })

  it('handles save failure gracefully', async () => {
    vi.mocked(historyService.createHistory).mockRejectedValue(new Error('fail'))

    const wrapper = mount(HomeView, {
      global: { stubs: { Teleport: true } },
    })
    await flushMicrotasks()

    const store = useWordsStore()
    store.queryWord('习', '学而时习之', 'quick', 3)
    await flushMicrotasks()

    const panel = wrapper.findComponent({ name: 'QueryPanel' })
    panel.vm.$emit('save')
    await flushMicrotasks()

    expect(historyService.createHistory).toHaveBeenCalled()
  })
})
