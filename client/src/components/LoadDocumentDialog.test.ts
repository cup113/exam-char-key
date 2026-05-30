import { describe, it, expect, vi, afterEach, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import LoadDocumentDialog from './LoadDocumentDialog.vue'

const mockDocs = vi.hoisted(() => [
  {
    id: 1,
    title: '论语',
    source_text: '学而时习之',
    tracked_words: [{ word: '之', offset: 3 }],
    created_at: '2025-01-01 10:00',
    is_public: true,
    public_uuid: 'abc-123',
  },
  {
    id: 2,
    title: '大学',
    source_text: '大学之道',
    tracked_words: [],
    created_at: '2025-01-02 12:00',
    is_public: false,
    public_uuid: null,
  },
])

const mockService = vi.hoisted(() => ({
  listDocs: vi.fn().mockResolvedValue({ documents: mockDocs }),
  deleteDoc: vi.fn(),
  updateDoc: vi.fn(),
}))

vi.mock('@/services/documentService', () => mockService)

describe('LoadDocumentDialog', () => {
  let wrapper: ReturnType<typeof mount>

  beforeEach(() => {
    vi.clearAllMocks()
    mockService.listDocs.mockResolvedValue({ documents: mockDocs })
    vi.stubGlobal('confirm', vi.fn(() => true))
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  afterEach(() => {
    wrapper?.unmount()
  })

  function mountDialog() {
    wrapper = mount(LoadDocumentDialog, {
      props: {},
      global: { stubs: { Teleport: true } },
    })
    return wrapper
  }

  it('shows loading state initially', () => {
    mockService.listDocs.mockReturnValue(new Promise(() => {}))
    mountDialog()
    expect(wrapper.text()).toContain('加载中')
  })

  it('renders document list after loading', async () => {
    mountDialog()
    await flushPromises()
    expect(wrapper.text()).toContain('论语')
    expect(wrapper.text()).toContain('大学')
  })

  it('shows empty state', async () => {
    mockService.listDocs.mockResolvedValue({ documents: [] })
    mountDialog()
    await flushPromises()
    expect(wrapper.text()).toContain('暂无文档')
  })

  it('shows error state', async () => {
    mockService.listDocs.mockRejectedValue(new Error('网络错误'))
    mountDialog()
    await flushPromises()
    expect(wrapper.text()).toContain('网络错误')
  })

  it('emits load on document click', async () => {
    mountDialog()
    await flushPromises()
    const docEl = wrapper.findAll('div').filter(d => d.attributes('class')?.includes('cursor-pointer'))
    await docEl[0]!.trigger('click')
    expect(wrapper.emitted('load')).toBeTruthy()
    expect(wrapper.emitted('load')![0]![0]).toMatchObject({ id: 1, title: '论语' })
  })

  it('emits cancel on close button', async () => {
    mountDialog()
    const closeBtn = wrapper.findAll('button').find(b => b.text() === '✕')
    await closeBtn!.trigger('click')
    expect(wrapper.emitted('cancel')).toBeTruthy()
  })

  it('emits cancel on overlay click', async () => {
    mountDialog()
    await wrapper.get('.fixed.inset-0').trigger('click')
    expect(wrapper.emitted('cancel')).toBeTruthy()
  })

  it('shows word count per document', async () => {
    mountDialog()
    await flushPromises()
    expect(wrapper.text()).toContain('1 词')
    expect(wrapper.text()).toContain('0 词')
  })

  it('shows source text preview', async () => {
    mountDialog()
    await flushPromises()
    expect(wrapper.text()).toContain('学而时习之')
    expect(wrapper.text()).toContain('大学之道')
  })

  it('deletes document and refreshes list', async () => {
    const confirmSpy = vi.spyOn(window, 'confirm').mockReturnValue(true)
    mockService.deleteDoc.mockResolvedValue(undefined)
    mountDialog()
    await flushPromises()
    const deleteBtns = wrapper.findAll('button').filter(b => b.text() === '删除')
    await deleteBtns[0]!.trigger('click')
    expect(mockService.deleteDoc).toHaveBeenCalledWith(1)
    expect(mockService.listDocs).toHaveBeenCalledTimes(2)
    confirmSpy.mockRestore()
  })

  it('toggles public status', async () => {
    mountDialog()
    await flushPromises()
    const publicBtn = wrapper.findAll('button').filter(b => b.text() === '私有')
    await publicBtn[0]!.trigger('click')
    expect(mockService.updateDoc).toHaveBeenCalledWith(2, { is_public: true })
    expect(mockService.listDocs).toHaveBeenCalledTimes(2)
  })

  it('copies public link to clipboard', async () => {
    const writeText = vi.fn().mockResolvedValue(undefined)
    vi.stubGlobal('navigator', { clipboard: { writeText } })
    mountDialog()
    await flushPromises()
    const copyBtn = wrapper.findAll('button').filter(b => b.text() === '复制链接')
    await copyBtn[0]!.trigger('click')
    expect(writeText).toHaveBeenCalledWith(expect.stringContaining('/shared/abc-123'))
    vi.unstubAllGlobals()
  })

  it('shows action error on delete failure', async () => {
    const confirmSpy = vi.spyOn(window, 'confirm').mockReturnValue(true)
    mockService.deleteDoc.mockRejectedValue(new Error('删除失败'))
    mountDialog()
    await flushPromises()
    const deleteBtns = wrapper.findAll('button').filter(b => b.text() === '删除')
    await deleteBtns[0]!.trigger('click')
    await flushPromises()
    expect(wrapper.text()).toContain('删除失败')
    confirmSpy.mockRestore()
  })

  it('preview truncates long text', async () => {
    const longText = 'a'.repeat(100)
    mockService.listDocs.mockResolvedValue({
      documents: [{ id: 1, title: '长文', source_text: longText, tracked_words: [], created_at: '', is_public: false, public_uuid: null }],
    })
    mountDialog()
    await flushPromises()
    expect(wrapper.text()).toContain('…')
  })
})
