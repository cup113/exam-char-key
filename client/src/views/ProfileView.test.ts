import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { setActivePinia, createPinia } from 'pinia'

vi.mock('@/stores/auth', () => ({
  useAuthStore: vi.fn(),
}))

import { useAuthStore } from '@/stores/auth'
import ProfileView from './ProfileView.vue'

function flushMicrotasks() {
  return new Promise(resolve => setTimeout(resolve, 0))
}

describe('ProfileView', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('renders user info when logged in', async () => {
    vi.mocked(useAuthStore).mockReturnValue({
      user: { logged_in: true, user_id: 'github:test', provider: 'github' },
      fetchUser: vi.fn().mockResolvedValue(undefined),
    } as any)

    const wrapper = mount(ProfileView)
    await flushMicrotasks()
    expect(wrapper.text()).toContain('github:test')
    expect(wrapper.text()).toContain('github')
  })

  it('shows login prompt when not logged in', async () => {
    vi.mocked(useAuthStore).mockReturnValue({
      user: { logged_in: false },
      fetchUser: vi.fn().mockResolvedValue(undefined),
    } as any)

    const wrapper = mount(ProfileView)
    await flushMicrotasks()
    expect(wrapper.text()).toContain('请先登录')
  })

  it('calls fetchUser on mount', async () => {
    const fetchUser = vi.fn().mockResolvedValue(undefined)
    vi.mocked(useAuthStore).mockReturnValue({
      user: { logged_in: false },
      fetchUser,
    } as any)

    mount(ProfileView)
    await flushMicrotasks()
    expect(fetchUser).toHaveBeenCalled()
  })
})
