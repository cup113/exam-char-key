import { describe, it, expect, vi, afterEach, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import SaveDocumentDialog from './SaveDocumentDialog.vue'

describe('SaveDocumentDialog', () => {
  let wrapper: ReturnType<typeof mount>

  afterEach(() => {
    wrapper?.unmount()
  })

  beforeEach(() => {
    vi.clearAllMocks()
  })

  function mountDialog(overrides: { defaultTitle?: string; savedResult?: any } = {}) {
    wrapper = mount(SaveDocumentDialog, {
      props: {
        defaultTitle: '默认标题',
        savedResult: null,
        ...overrides,
      },
      global: { stubs: { Teleport: true } },
    })
    return wrapper
  }

  it('renders title input and checkbox', () => {
    mountDialog()
    expect(wrapper.find('input').exists()).toBe(true)
    expect(wrapper.find('input[type="checkbox"]').exists()).toBe(true)
    expect(wrapper.text()).toContain('保存文档')
    expect(wrapper.text()).toContain('保存')
    expect(wrapper.text()).toContain('取消')
  })

  it('default title is pre-filled', () => {
    mountDialog({ defaultTitle: '论语' })
    const input = wrapper.findAll('input')[0]!
    expect((input.element as HTMLInputElement).value).toBe('论语')
  })

  it('emits save with title and isPublic on save button', async () => {
    mountDialog({ defaultTitle: '论语' })
    const input = wrapper.findAll('input')[0]!
    await input.setValue('新标题')
    const checkbox = wrapper.find('input[type="checkbox"]')
    await checkbox.setValue(true)
    const saveBtn = wrapper.findAll('button').find(b => b.text() === '保存')
    await saveBtn!.trigger('click')
    expect(wrapper.emitted('save')).toBeTruthy()
    expect(wrapper.emitted('save')![0]).toEqual([{ title: '新标题', isPublic: true }])
  })

  it('emits save with trimmed title falling back to default', async () => {
    mountDialog({ defaultTitle: '论语' })
    const input = wrapper.findAll('input')[0]!
    await input.setValue('   ')
    const saveBtn = wrapper.findAll('button').find(b => b.text() === '保存')
    await saveBtn!.trigger('click')
    expect(wrapper.emitted('save')![0]).toEqual([{ title: '论语', isPublic: false }])
  })

  it('emits cancel on cancel button', async () => {
    mountDialog()
    const cancelBtn = wrapper.findAll('button').find(b => b.text() === '取消')
    await cancelBtn!.trigger('click')
    expect(wrapper.emitted('cancel')).toBeTruthy()
  })

  it('emits cancel on overlay click', async () => {
    mountDialog()
    await wrapper.get('.fixed.inset-0').trigger('click')
    expect(wrapper.emitted('cancel')).toBeTruthy()
  })

  describe('after save', () => {
    const savedResult = { id: 42, title: '论语', public_uuid: 'abc-123' }

    it('shows success message', () => {
      mountDialog({ savedResult })
      expect(wrapper.text()).toContain('文档已保存')
    })

    it('shows dismiss button instead of cancel/save', () => {
      mountDialog({ savedResult })
      expect(wrapper.text()).toContain('关闭')
      expect(wrapper.text()).not.toContain('取消')
    })

    it('emits dismiss on dismiss button', async () => {
      mountDialog({ savedResult })
      const dismissBtn = wrapper.findAll('button').find(b => b.text() === '关闭')
      await dismissBtn!.trigger('click')
      expect(wrapper.emitted('dismiss')).toBeTruthy()
    })

    it('copies share URL to clipboard', async () => {
      const writeText = vi.fn().mockResolvedValue(undefined)
      vi.stubGlobal('navigator', { clipboard: { writeText } })
      mountDialog({ savedResult })
      const copyBtn = wrapper.findAll('button').find(b => b.text() === '复制')
      await copyBtn!.trigger('click')
      expect(writeText).toHaveBeenCalledWith(expect.stringContaining('/shared/abc-123'))
      vi.unstubAllGlobals()
    })

    it('does not show share URL section when public_uuid is null', () => {
      mountDialog({ savedResult: { id: 42, title: '论语', public_uuid: null } })
      expect(wrapper.text()).not.toContain('复制')
    })
  })
})
