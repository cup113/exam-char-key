import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { setActivePinia, createPinia } from 'pinia'

vi.mock('@/stores/auth', () => ({
  useAuthStore: vi.fn(),
}))

vi.mock('@/stores/theme', () => ({
  useThemeStore: vi.fn(),
}))

import { useAuthStore } from '@/stores/auth'
import { useThemeStore } from '@/stores/theme'
import App from './App.vue'

function flushMicrotasks() {
  return new Promise(resolve => setTimeout(resolve, 0))
}

function stubRouterLink() {
  return { template: '<a><slot/></a>' }
}

describe('App', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('renders header with navigation', () => {
    vi.mocked(useAuthStore).mockReturnValue({
      user: { logged_in: false },
      fetchUser: vi.fn().mockResolvedValue(undefined),
    } as any)
    vi.mocked(useThemeStore).mockReturnValue({
      isDark: false,
      toggle: vi.fn(),
    } as any)

    const wrapper = mount(App, {
      global: {
        stubs: {
          RouterView: true,
          RouterLink: stubRouterLink(),
          LoginButtons: true,
        },
      },
    })
    expect(wrapper.text()).toContain('Exam Char Key')
  })

  it('shows login buttons when not logged in', () => {
    vi.mocked(useAuthStore).mockReturnValue({
      user: { logged_in: false },
      fetchUser: vi.fn().mockResolvedValue(undefined),
    } as any)
    vi.mocked(useThemeStore).mockReturnValue({
      isDark: false,
      toggle: vi.fn(),
    } as any)

    const wrapper = mount(App, {
      global: {
        stubs: {
          RouterView: true,
          RouterLink: stubRouterLink(),
          LoginButtons: { render: () => 'GitHub 登录' },
        },
      },
    })
    expect(wrapper.text()).toContain('GitHub 登录')
  })

  it('shows user info and logout when logged in', () => {
    vi.mocked(useAuthStore).mockReturnValue({
      user: { logged_in: true, user_id: 'github:test', is_admin: false },
      logout: vi.fn(),
      fetchUser: vi.fn().mockResolvedValue(undefined),
    } as any)
    vi.mocked(useThemeStore).mockReturnValue({
      isDark: false,
      toggle: vi.fn(),
    } as any)

    const wrapper = mount(App, {
      global: {
        stubs: {
          RouterView: true,
          RouterLink: stubRouterLink(),
          LoginButtons: true,
        },
      },
    })
    expect(wrapper.text()).toContain('github:test')
    expect(wrapper.text()).toContain('退出')
  })

  it('shows admin link for admin users', () => {
    vi.mocked(useAuthStore).mockReturnValue({
      user: { logged_in: true, user_id: 'github:admin', is_admin: true },
      logout: vi.fn(),
      fetchUser: vi.fn().mockResolvedValue(undefined),
    } as any)
    vi.mocked(useThemeStore).mockReturnValue({
      isDark: false,
      toggle: vi.fn(),
    } as any)

    const wrapper = mount(App, {
      global: {
        stubs: {
          RouterView: true,
          RouterLink: stubRouterLink(),
          LoginButtons: true,
        },
      },
    })
    expect(wrapper.text()).toContain('管理')
  })

  it('calls fetchUser on mount', async () => {
    const fetchUser = vi.fn().mockResolvedValue(undefined)
    vi.mocked(useAuthStore).mockReturnValue({
      user: { logged_in: false },
      fetchUser,
    } as any)
    vi.mocked(useThemeStore).mockReturnValue({
      isDark: false,
      toggle: vi.fn(),
    } as any)

    mount(App, {
      global: {
        stubs: {
          RouterView: true,
          RouterLink: stubRouterLink(),
          LoginButtons: true,
        },
      },
    })
    await flushMicrotasks()
    expect(fetchUser).toHaveBeenCalled()
  })

  it('toggles mobile menu', async () => {
    vi.mocked(useAuthStore).mockReturnValue({
      user: { logged_in: false },
      fetchUser: vi.fn().mockResolvedValue(undefined),
    } as any)
    vi.mocked(useThemeStore).mockReturnValue({
      isDark: false,
      toggle: vi.fn(),
    } as any)

    const wrapper = mount(App, {
      global: {
        stubs: {
          RouterView: true,
          RouterLink: stubRouterLink(),
          LoginButtons: { render: () => 'GitHub 登录' },
        },
      },
    })
    await flushMicrotasks()

    const menuBtn = wrapper.find('button.lg\\:hidden')
    expect(menuBtn.exists()).toBe(true)
    await menuBtn.trigger('click')
    await flushMicrotasks()

    expect(wrapper.text()).toContain('深色模式')
  })
})
