import { describe, it, expect, vi, beforeEach } from 'vitest'
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
vi.mock('@/composables/useDocumentLoader', () => ({
  useDocumentLoader: vi.fn(() => ({
    loadDocument: vi.fn(),
    confirmState: null,
  })),
}))

import TextContent from './TextContent.vue'

function createWord(overrides = {}) {
  return {
    id: 'word-1',
    word: '之',
    context: '学而时习之',
    offset: 3,
    mode: 'quick',
    status: 'done',
    quickAnswer: '代词',
    dictResult: '',
    deepThink: '',
    corpusEntries: [],
    quickStatus: 'done',
    corpusStatus: 'done',
    dictStatus: 'done',
    deepStatus: 'idle',
    startTime: Date.now(),
    ...overrides,
  }
}

describe('TextContent', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    localStorage.clear()
  })

  it('renders plain text when no segments', () => {
    const wrapper = mount(TextContent, {
      props: {
        editableText: '子曰学而时习之',
        editing: false,
        editText: '',
        textSegments: [],
      },
    })
    expect(wrapper.text()).toContain('子曰学而时习之')
  })

  it('renders text segments with tracked words', () => {
    const word = createWord()
    const wrapper = mount(TextContent, {
      props: {
        editableText: '学而时习之',
        editing: false,
        editText: '',
        textSegments: [
          { type: 'text', content: '学而时习' },
          { type: 'word', word },
        ],
      },
    })
    expect(wrapper.text()).toContain('学而时习')
    expect(wrapper.text()).toContain('之')
    expect(wrapper.text()).toContain('代词')
  })

  it('shows loading spinner for loading words', () => {
    const word = createWord({ status: 'loading', quickAnswer: '', quickStatus: 'loading' })
    const wrapper = mount(TextContent, {
      props: {
        editableText: '学而时习之',
        editing: false,
        editText: '',
        textSegments: [{ type: 'word', word }],
      },
    })
    expect(wrapper.find('.animate-spin').exists()).toBe(true)
  })

  it('shows error class for error words', () => {
    const word = createWord({ status: 'error', quickAnswer: '' })
    const wrapper = mount(TextContent, {
      props: {
        editableText: 'a',
        editing: false,
        editText: '',
        textSegments: [{ type: 'word', word }],
      },
    })
    const span = wrapper.find('.tracked-word')
    expect(span.classes().some(c => c.includes('red'))).toBe(true)
  })

  it('enters editing mode', () => {
    const wrapper = mount(TextContent, {
      props: {
        editableText: '原文',
        editing: true,
        editText: '编辑中',
        textSegments: [],
      },
    })
    expect(wrapper.find('textarea').exists()).toBe(true)
    expect((wrapper.find('textarea').element as HTMLTextAreaElement).value).toBe('编辑中')
  })

  it('emits saveEditing on save button', async () => {
    const wrapper = mount(TextContent, {
      props: {
        editableText: '原文',
        editing: true,
        editText: '新内容',
        textSegments: [],
      },
    })
    const buttons = wrapper.findAll('button')
    const saveBtn = buttons.find(b => b.text().includes('保存'))
    expect(saveBtn).toBeTruthy()
    await saveBtn!.trigger('click')
    expect(wrapper.emitted('saveEditing')).toBeTruthy()
  })

  it('emits cancelEditing on cancel button', async () => {
    const wrapper = mount(TextContent, {
      props: {
        editableText: '原文',
        editing: true,
        editText: '新内容',
        textSegments: [],
      },
    })
    const buttons = wrapper.findAll('button')
    const cancelBtn = buttons.find(b => b.text().includes('取消'))
    expect(cancelBtn).toBeTruthy()
    await cancelBtn!.trigger('click')
    expect(wrapper.emitted('cancelEditing')).toBeTruthy()
  })

  it('emits wordClick on tracked word click', async () => {
    const word = createWord()
    const wrapper = mount(TextContent, {
      props: {
        editableText: '之',
        editing: false,
        editText: '',
        textSegments: [{ type: 'word', word }],
      },
    })
    await wrapper.find('.tracked-word').trigger('click')
    expect(wrapper.emitted('wordClick')).toBeTruthy()
    expect(wrapper.emitted('wordClick')![0]).toEqual(['word-1'])
  })

  it('hides document and editing UI in readonly mode', () => {
    const wrapper = mount(TextContent, {
      props: {
        editableText: 'text',
        editing: false,
        editText: '',
        textSegments: [],
        readonly: true,
      },
    })
    expect(wrapper.text()).not.toContain('文档')
    expect(wrapper.text()).not.toContain('编辑文本')
  })
})
