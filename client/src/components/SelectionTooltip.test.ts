import { describe, it, expect, afterEach } from 'vitest'
import { mount } from '@vue/test-utils'
import SelectionTooltip from './SelectionTooltip.vue'

describe('SelectionTooltip', () => {
  let wrapper: ReturnType<typeof mount>

  afterEach(() => {
    wrapper?.unmount()
  })

  function mountTooltip(props: { show: boolean; x: number; y: number }) {
    wrapper = mount(SelectionTooltip, {
      props,
      global: { stubs: { Teleport: true } },
    })
    return wrapper
  }

  it('does not render when show is false', () => {
    mountTooltip({ show: false, x: 0, y: 0 })
    expect(wrapper.text()).not.toContain('快速确认')
  })

  it('renders at given position', () => {
    mountTooltip({ show: true, x: 100, y: 200 })
    const el = wrapper.get('.fixed')
    const style = el.attributes('style')
    expect(style).toContain('top: 200px')
    expect(style).toContain('left: 100px')
  })

  it('emits quick on quick button click', async () => {
    mountTooltip({ show: true, x: 0, y: 0 })
    await wrapper.find('button').trigger('click')
    expect(wrapper.emitted('quick')).toBeTruthy()
  })

  it('emits deep on deep button click', async () => {
    mountTooltip({ show: true, x: 0, y: 0 })
    const buttons = wrapper.findAll('button')
    await buttons[1].trigger('click')
    expect(wrapper.emitted('deep')).toBeTruthy()
  })
})
