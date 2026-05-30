import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { setActivePinia, createPinia } from 'pinia'

vi.mock('@/stores/auth', () => ({
  useAuthStore: vi.fn(),
}))

vi.mock('vue-router', () => ({
  useRouter: vi.fn(() => ({ replace: vi.fn() })),
}))

vi.mock('@/services/adminService', () => ({
  importCorpus: vi.fn(),
}))

import { useAuthStore } from '@/stores/auth'
import { useRouter } from 'vue-router'
import * as adminService from '@/services/adminService'
import AdminView from './AdminView.vue'

function flushMicrotasks() {
  return new Promise(resolve => setTimeout(resolve, 0))
}

describe('AdminView', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('redirects non-admin to home', async () => {
    const replace = vi.fn()
    vi.mocked(useRouter).mockReturnValue({ replace } as any)
    vi.mocked(useAuthStore).mockReturnValue({
      user: { logged_in: true, user_id: 'github:test', is_admin: false },
      fetchUser: vi.fn().mockResolvedValue(undefined),
    } as any)

    mount(AdminView)
    await flushMicrotasks()
    expect(replace).toHaveBeenCalledWith('/')
  })

  it('renders admin panel for admin user', async () => {
    vi.mocked(useRouter).mockReturnValue({ replace: vi.fn() } as any)
    vi.mocked(useAuthStore).mockReturnValue({
      user: { logged_in: true, user_id: 'github:admin', is_admin: true },
      fetchUser: vi.fn().mockResolvedValue(undefined),
    } as any)

    const wrapper = mount(AdminView)
    await flushMicrotasks()
    expect(wrapper.text()).toContain('管理面板')
    expect(wrapper.text()).toContain('导入语料库')
  })

  it('shows import success result', async () => {
    vi.mocked(useRouter).mockReturnValue({ replace: vi.fn() } as any)
    vi.mocked(useAuthStore).mockReturnValue({
      user: { logged_in: true, user_id: 'github:admin', is_admin: true },
      fetchUser: vi.fn().mockResolvedValue(undefined),
    } as any)
    vi.mocked(adminService.importCorpus).mockResolvedValue({
      success: true, count: 42, filename: 'test.jsonl',
    } as any)

    const wrapper = mount(AdminView)
    await flushMicrotasks()

    const input = wrapper.find('input[type="file"]')
    const file = new File(['data'], 'test.jsonl', { type: 'application/json' })
    Object.defineProperty(input.element, 'files', { value: [file] })
    await input.trigger('change')

    await wrapper.find('form').trigger('submit.prevent')
    await flushMicrotasks()

    expect(wrapper.text()).toContain('成功')
    expect(wrapper.text()).toContain('42')
    expect(wrapper.text()).toContain('test.jsonl')
  })

  it('shows import error result', async () => {
    vi.mocked(useRouter).mockReturnValue({ replace: vi.fn() } as any)
    vi.mocked(useAuthStore).mockReturnValue({
      user: { logged_in: true, user_id: 'github:admin', is_admin: true },
      fetchUser: vi.fn().mockResolvedValue(undefined),
    } as any)
    vi.mocked(adminService.importCorpus).mockRejectedValue(new Error('格式错误'))

    const wrapper = mount(AdminView)
    await flushMicrotasks()

    const input = wrapper.find('input[type="file"]')
    const file = new File(['bad'], 'bad.json', { type: 'application/json' })
    Object.defineProperty(input.element, 'files', { value: [file] })
    await input.trigger('change')

    await wrapper.find('form').trigger('submit.prevent')
    await flushMicrotasks()

    expect(wrapper.text()).toContain('导入失败')
    expect(wrapper.text()).toContain('格式错误')
  })
})
