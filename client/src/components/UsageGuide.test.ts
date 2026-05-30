import { describe, it, expect, vi, afterEach } from 'vitest'
import { mount } from '@vue/test-utils'
import UsageGuide from './UsageGuide.vue'

vi.mock('../../package.json', () => ({ version: '1.0.0' }))

describe('UsageGuide', () => {
  let wrapper: ReturnType<typeof mount>

  afterEach(() => {
    wrapper?.unmount()
  })

  function mountGuide(show: boolean) {
    wrapper = mount(UsageGuide, {
      props: { show },
      global: { stubs: { Teleport: true } },
    })
    return wrapper
  }

  it('does not render when show is false', () => {
    mountGuide(false)
    expect(wrapper.text()).not.toContain('使用指南')
  })

  it('renders guide tab by default', () => {
    mountGuide(true)
    expect(wrapper.text()).toContain('使用指南')
    expect(wrapper.text()).toContain('划词查询')
  })

  it('switches to about tab', async () => {
    mountGuide(true)
    const buttons = wrapper.findAll('button')
    await buttons[2].trigger('click')
    expect(wrapper.text()).toContain('关于本应用')
  })

  it('emits dismiss on close button', async () => {
    mountGuide(true)
    const buttons = wrapper.findAll('button')
    await buttons[0].trigger('click')
    expect(wrapper.emitted('dismiss')).toBeTruthy()
  })

  it('emits dismiss on overlay click', async () => {
    mountGuide(true)
    await wrapper.get('.fixed.inset-0').trigger('click')
    expect(wrapper.emitted('dismiss')).toBeTruthy()
  })

  it('displays version in about tab', async () => {
    mountGuide(true)
    const buttons = wrapper.findAll('button')
    await buttons[2].trigger('click')
    expect(wrapper.text()).toContain('1.0.0')
  })
})
