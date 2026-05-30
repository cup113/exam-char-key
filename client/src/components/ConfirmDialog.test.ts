import { describe, it, expect, vi, afterEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { reactive } from 'vue'
import type { ConfirmState } from './ConfirmDialog.vue'
import ConfirmDialog from './ConfirmDialog.vue'

function createState(overrides: Partial<ConfirmState> = {}): ConfirmState {
  return reactive({
    show: true,
    title: '确认',
    message: '确定执行此操作？',
    buttons: [
      { label: '确定', value: 'confirm', variant: 'primary' },
      { label: '取消', value: 'cancel' },
    ],
    resolve: vi.fn(),
    ...overrides,
  }) as unknown as ConfirmState
}

describe('ConfirmDialog', () => {
  let wrapper: ReturnType<typeof mount>

  afterEach(() => {
    wrapper?.unmount()
    vi.clearAllMocks()
  })

  function mountDialog(state: ConfirmState) {
    wrapper = mount(ConfirmDialog, {
      props: { state },
      global: { stubs: { Teleport: true } },
    })
    return wrapper
  }

  it('renders when show is true', () => {
    const state = createState()
    mountDialog(state)
    expect(wrapper.text()).toContain('确认')
    expect(wrapper.text()).toContain('确定执行此操作？')
  })

  it('does not render when show is false', () => {
    const state = createState({ show: false })
    mountDialog(state)
    expect(wrapper.text()).not.toContain('确认')
  })

  it('renders all buttons', () => {
    const state = createState()
    mountDialog(state)
    expect(wrapper.text()).toContain('确定')
    expect(wrapper.text()).toContain('取消')
  })

  it('calls resolve and hides on button click', async () => {
    const state = createState()
    mountDialog(state)
    await wrapper.find('button').trigger('click')
    expect(state.resolve).toHaveBeenCalledWith('confirm')
    expect(state.show).toBe(false)
  })

  it('calls resolve with cancel on overlay click', async () => {
    const state = createState()
    mountDialog(state)
    const overlay = wrapper.get('.fixed.inset-0')
    await overlay.trigger('click')
    expect(state.resolve).toHaveBeenCalledWith('cancel')
    expect(state.show).toBe(false)
  })

  it('applies correct variant classes', () => {
    const state = createState({
      buttons: [
        { label: 'Primary', value: 'p', variant: 'primary' },
        { label: 'Danger', value: 'd', variant: 'danger' },
        { label: 'Default', value: 'def' },
      ],
    })
    mountDialog(state)
    const buttons = wrapper.findAll('button')
    expect(buttons[0].classes()).toContain('bg-blue-600')
    expect(buttons[1].classes()).toContain('bg-red-600')
    expect(buttons[2].classes()).toContain('border-gray-300')
  })
})
