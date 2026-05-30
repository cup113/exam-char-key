import { describe, it, expect, afterEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { type CorpusEntry } from '@/types'
import WordAnalysisCard from './WordAnalysisCard.vue'

interface WordLike {
  word: string
  quickAnswer: string
  dictResult: string
  deepThink: string
  corpusEntries: CorpusEntry[]
  mode: string
  quickStatus?: string
  dictStatus?: string
  deepStatus?: string
  corpusStatus?: string
}

function createWord(overrides: Partial<WordLike> = {}): WordLike {
  return {
    word: '之',
    quickAnswer: '代词',
    dictResult: JSON.stringify({ basic: [{ explanation: '助词' }] }),
    deepThink: '',
    corpusEntries: [],
    mode: 'quick',
    quickStatus: 'done',
    dictStatus: 'done',
    deepStatus: 'idle',
    corpusStatus: 'idle',
    ...overrides,
  }
}

describe('WordAnalysisCard', () => {
  let wrapper: ReturnType<typeof mount>

  afterEach(() => {
    wrapper?.unmount()
  })

  function mountCard(word: WordLike | null, readonly = false) {
    wrapper = mount(WordAnalysisCard, {
      props: { word, readonly },
      global: { stubs: { Teleport: true } },
    })
    return wrapper
  }

  it('shows placeholder when word is null and idle', () => {
    mountCard(null)
    expect(wrapper.text()).toContain('选中词语后点击查询')
  })

  it('shows allFailed message when all statuses are error', () => {
    mountCard(createWord({
      quickAnswer: '',
      dictResult: '',
      quickStatus: 'error',
      dictStatus: 'error',
      deepStatus: 'error',
      corpusStatus: 'error',
    }))
    expect(wrapper.text()).toContain('全部查询失败')
  })

  it('renders AI answer section with quick answer', () => {
    mountCard(createWord())
    expect(wrapper.text()).toContain('AI 解答')
    expect(wrapper.text()).toContain('代词')
  })

  it('renders deep meaning when deepThink has [词义]', () => {
    const word = createWord({
      deepThink: '[词义] 代词，表示"的"\n[解释] 详细分析',
      deepStatus: 'done',
      quickAnswer: '',
      quickStatus: 'idle',
    })
    mountCard(word)
    expect(wrapper.text()).toContain('代词，表示"的"')
    expect(wrapper.text()).toContain('详细分析')
  })

  it('renders loading state for quick answer', () => {
    mountCard(createWord({
      quickAnswer: '',
      quickStatus: 'loading',
      dictResult: '',
      dictStatus: 'idle',
      deepThink: 'placeholder',
    }))
    expect(wrapper.find('.animate-pulse').exists()).toBe(true)
  })

  it('renders error state for quick answer', () => {
    mountCard(createWord({
      quickAnswer: '',
      quickStatus: 'error',
      dictResult: '',
      dictStatus: 'idle',
      deepThink: 'placeholder',
    }))
    expect(wrapper.text()).toContain('快速查询失败')
  })

  it('renders dict section with DictDisplay', () => {
    mountCard(createWord())
    expect(wrapper.text()).toContain('汉典释义')
  })

  it('renders loading for dict', () => {
    mountCard(createWord({
      dictResult: '',
      dictStatus: 'loading',
      quickAnswer: '',
      quickStatus: 'idle',
    }))
    expect(wrapper.find('.animate-pulse').exists()).toBe(true)
  })

  it('renders error for dict', () => {
    mountCard(createWord({
      dictResult: '',
      dictStatus: 'error',
      quickAnswer: '',
      quickStatus: 'idle',
    }))
    expect(wrapper.text()).toContain('汉典查询失败')
  })

  it('renders corpus entries with type labels', () => {
    const word = createWord({
      corpusEntries: [
        { id: 1, type: 'textbook', context: '学而时习之', word: '之', answer: '代词' },
      ],
      corpusStatus: 'done',
    })
    mountCard(word)
    expect(wrapper.text()).toContain('教材')
    expect(wrapper.text()).toContain('学而时习之')
    expect(wrapper.text()).toContain('代词')
  })

  it('renders loading for corpus', () => {
    mountCard(createWord({
      corpusStatus: 'loading',
      quickAnswer: '',
      quickStatus: 'idle',
      dictResult: '',
      dictStatus: 'idle',
    }))
    expect(wrapper.find('.animate-pulse').exists()).toBe(true)
  })

  it('renders error for corpus', () => {
    mountCard(createWord({
      corpusStatus: 'error',
      quickAnswer: '',
      quickStatus: 'idle',
      dictResult: '',
      dictStatus: 'idle',
      corpusEntries: [],
    }))
    expect(wrapper.text()).toContain('语料库查询失败')
  })

  it('supports readonly mode (no loading/error states)', () => {
    const word = createWord({
      quickAnswer: '',
      quickStatus: 'loading',
      dictResult: '',
      dictStatus: 'idle',
    })
    mountCard(word, true)
    expect(wrapper.find('.animate-pulse').exists()).toBe(false)
    expect(wrapper.text()).not.toContain('快速查询失败')
  })

  it('hides sections when status is idle', () => {
    const word = createWord({
      quickAnswer: '',
      quickStatus: 'idle',
      dictResult: '',
      dictStatus: 'idle',
      deepStatus: 'idle',
      corpusStatus: 'idle',
    })
    mountCard(word)
    expect(wrapper.text()).not.toContain('AI 解答')
    expect(wrapper.text()).not.toContain('汉典释义')
    expect(wrapper.text()).not.toContain('语料库参考')
  })
})
