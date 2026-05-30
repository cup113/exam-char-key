import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { setActivePinia, createPinia } from 'pinia'
import type { TrackedWord } from '@/types'

vi.mock('@/services/queryService', () => ({
  queryQuick: vi.fn(),
  queryCorpus: vi.fn(() => []),
  queryDictionary: vi.fn(() => ''),
  queryDeep: vi.fn(),
}))

vi.mock('@/services/documentService', () => ({
  createDoc: vi.fn(),
}))

import { useWordsStore } from '@/stores/words'
import QueryPanel from './QueryPanel.vue'

function createWord(id: string, overrides: Partial<TrackedWord> = {}): TrackedWord {
  return {
    id,
    word: '之',
    context: '学而时习之',
    offset: 3,
    mode: 'quick',
    status: 'pending',
    quickAnswer: '',
    dictResult: '',
    deepThink: '',
    corpusEntries: [],
    quickStatus: 'idle',
    corpusStatus: 'idle',
    dictStatus: 'idle',
    deepStatus: 'idle',
    startTime: Date.now(),
    ...overrides,
  }
}

describe('QueryPanel', () => {
  let wrapper: ReturnType<typeof mount>

  beforeEach(() => {
    setActivePinia(createPinia())
    localStorage.clear()
  })

  afterEach(() => {
    wrapper?.unmount()
    vi.clearAllMocks()
  })

  function mountPanel(props: {
    show?: boolean
    activeWord?: TrackedWord | null
    savedAnswer?: string
    saveSuccess?: boolean
    loggedIn?: boolean
  } = {}) {
    wrapper = mount(QueryPanel, {
      props: {
        show: true,
        activeWord: null,
        savedAnswer: '',
        saveSuccess: false,
        loggedIn: false,
        ...props,
      },
      global: { stubs: { Teleport: true } },
    })
    return wrapper
  }

  it('shows placeholder when no active word', () => {
    mountPanel()
    expect(wrapper.text()).toContain('选中词语后点击查询')
  })

  it('shows word header when active word exists', () => {
    mountPanel({ activeWord: createWord('w1') })
    expect(wrapper.text()).toContain('「之」')
  })

  it('shows mode label', () => {
    mountPanel({ activeWord: createWord('w1', { mode: 'deep' }) })
    expect(wrapper.text()).toContain('深度查询')
    mountPanel({ activeWord: createWord('w2', { mode: 'quick' }) })
    expect(wrapper.text()).toContain('快速确认')
  })

  it('shows cancel button when pending', () => {
    mountPanel({ activeWord: createWord('w1') })
    expect(wrapper.text()).toContain('取消')
  })

  it('shows AI answer when quickAnswer is present', () => {
    mountPanel({ activeWord: createWord('w1', { status: 'done', quickAnswer: '代词', quickStatus: 'done' }) })
    expect(wrapper.text()).toContain('代词')
  })

  it('shows deep meaning when deepThink has [词义]', () => {
    mountPanel({
      activeWord: createWord('w1', {
        status: 'done',
        quickAnswer: '',
        quickStatus: 'idle',
        deepThink: '[词义] 代词，表示"的"\n[解释] 详细分析',
        deepStatus: 'done',
      }),
    })
    expect(wrapper.text()).toContain('代词，表示"的"')
  })

  it('shows DeepAnalysisSplit for deep think', () => {
    mountPanel({
      activeWord: createWord('w1', {
        deepThink: '[词义] 代词\n[解释] 用法分析',
        deepStatus: 'done',
      }),
    })
    expect(wrapper.text()).toContain('用法分析')
  })

  it('shows loading for deep analysis', () => {
    mountPanel({
      activeWord: createWord('w1', {
        deepThink: '',
        deepStatus: 'loading',
        quickAnswer: '',
        quickStatus: 'idle',
      }),
    })
    expect(wrapper.find('.animate-pulse').exists()).toBe(true)
  })

  it('shows error for deep analysis', () => {
    mountPanel({
      activeWord: createWord('w1', {
        deepThink: '',
        deepStatus: 'error',
        quickAnswer: '',
        quickStatus: 'idle',
      }),
    })
    expect(wrapper.text()).toContain('深度分析失败')
  })

  it('shows dict section', () => {
    mountPanel({
      activeWord: createWord('w1', {
        status: 'done',
        dictResult: '{"basic":[{"explanation":"助词"}]}',
        dictStatus: 'done',
      }),
    })
    expect(wrapper.text()).toContain('汉典释义')
  })

  it('shows corpus entries with type labels', () => {
    mountPanel({
      activeWord: createWord('w1', {
        status: 'done',
        corpusEntries: [
          { id: 1, type: 'textbook', context: '学而时习之', word: '之', answer: '代词' },
        ],
        corpusStatus: 'done',
      }),
    })
    expect(wrapper.text()).toContain('教材')
    expect(wrapper.text()).toContain('学而时习之')
  })

  describe('buttons', () => {
    it('cancel button calls store.removeWord', async () => {
      const store = useWordsStore()
      const id = store.addWord('之', '', 'quick', 0)
      mountPanel({ activeWord: createWord(id, { status: 'pending' }) })
      const cancelBtn = wrapper.findAll('button').find(b => b.text() === '取消')
      await cancelBtn!.trigger('click')
      expect(store.trackedWords).toHaveLength(0)
    })

    it('retry button calls store.retryWord', async () => {
      const store = useWordsStore()
      const id = store.addWord('之', '', 'quick', 0)
      store.updateWord(id, { status: 'error', quickStatus: 'error', dictStatus: 'error', corpusStatus: 'error', deepStatus: 'error' })
      mountPanel({
        activeWord: createWord(id, {
          status: 'error',
          quickStatus: 'error',
          dictStatus: 'error',
          corpusStatus: 'error',
          deepStatus: 'error',
        }),
      })
      const retryBtn = wrapper.findAll('button').find(b => b.text() === '重试')
      await retryBtn!.trigger('click')
      expect(store.trackedWords.find(w => w.id === id)?.status).toBe('loading')
    })

    it('upgrade button calls store.upgradeToDeep', async () => {
      const store = useWordsStore()
      const id = store.addWord('之', '', 'quick', 0)
      store.updateWord(id, { status: 'done', quickAnswer: '代词', quickStatus: 'done', corpusStatus: 'done', dictStatus: 'done' })
      mountPanel({
        activeWord: createWord(id, {
          status: 'done',
          quickAnswer: '代词',
          quickStatus: 'done',
          corpusStatus: 'done',
          dictStatus: 'done',
        }),
      })
      const upgradeBtn = wrapper.findAll('button').find(b => b.text() === '升级深度思考')
      await upgradeBtn!.trigger('click')
      expect(store.trackedWords.find(w => w.id === id)?.mode).toBe('deep')
    })
  })

  describe('save section', () => {
    it('shows save area when logged in and done', () => {
      mountPanel({
        activeWord: createWord('w1', {
          status: 'done',
          quickAnswer: '代词',
          quickStatus: 'done',
          corpusStatus: 'done',
          dictStatus: 'done',
        }),
        loggedIn: true,
      })
      expect(wrapper.text()).toContain('保存到历史')
    })

    it('does not show save area when not logged in', () => {
      mountPanel({
        activeWord: createWord('w1', {
          status: 'done',
          quickAnswer: '代词',
          quickStatus: 'done',
          corpusStatus: 'done',
          dictStatus: 'done',
        }),
        loggedIn: false,
      })
      expect(wrapper.text()).not.toContain('保存到历史')
    })

    it('emits update:savedAnswer on textarea input', async () => {
      mountPanel({
        activeWord: createWord('w1', {
          status: 'done',
          quickAnswer: '代词',
          quickStatus: 'done',
          corpusStatus: 'done',
          dictStatus: 'done',
        }),
        loggedIn: true,
        savedAnswer: '代词',
      })
      const textarea = wrapper.find('textarea')
      await textarea.setValue('新答案')
      expect(wrapper.emitted('update:savedAnswer')).toBeTruthy()
      expect(wrapper.emitted('update:savedAnswer')![0]).toEqual(['新答案'])
    })

    it('emits save on save button', async () => {
      mountPanel({
        activeWord: createWord('w1', {
          status: 'done',
          quickAnswer: '代词',
          quickStatus: 'done',
          corpusStatus: 'done',
          dictStatus: 'done',
        }),
        loggedIn: true,
      })
      const saveBtn = wrapper.findAll('button').find(b => b.text() === '保存到历史')
      await saveBtn!.trigger('click')
      expect(wrapper.emitted('save')).toBeTruthy()
    })

    it('shows saveSuccess message', () => {
      mountPanel({
        activeWord: createWord('w1', {
          status: 'done',
          quickAnswer: '代词',
          quickStatus: 'done',
          corpusStatus: 'done',
          dictStatus: 'done',
        }),
        loggedIn: true,
        saveSuccess: true,
      })
      expect(wrapper.text()).toContain('已保存')
    })
  })

  it('emits close on close button', async () => {
    mountPanel({ activeWord: createWord('w1', { status: 'done', quickAnswer: 'a', quickStatus: 'done', corpusStatus: 'done', dictStatus: 'done' }) })
    const closeBtn = wrapper.findAll('button').find(b => b.text() === '✕')
    await closeBtn!.trigger('click')
    expect(wrapper.emitted('close')).toBeTruthy()
  })

  it('shows allFailed placeholder', () => {
    mountPanel({
      activeWord: createWord('w1', {
        status: 'error',
        quickStatus: 'error',
        corpusStatus: 'error',
        dictStatus: 'error',
        deepStatus: 'error',
        quickAnswer: '',
        dictResult: '',
      }),
    })
    expect(wrapper.text()).toContain('全部查询失败')
  })

  it('shows idle placeholder when activeWord is all idle', () => {
    mountPanel({
      activeWord: createWord('w1', { status: 'pending' }),
    })
    expect(wrapper.text()).toContain('选中词语后点击查询')
  })
})
