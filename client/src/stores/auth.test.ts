import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'

vi.mock('@/services/authService', () => ({
  fetchMe: vi.fn(),
  fetchQuota: vi.fn(),
  logout: vi.fn(),
}))

import { useAuthStore } from './auth'
import * as authService from '@/services/authService'

const originalLocation = window.location

beforeEach(() => {
  setActivePinia(createPinia())
  Object.defineProperty(window, 'location', {
    value: { ...originalLocation, reload: vi.fn() },
    writable: true,
  })
})

afterEach(() => {
  vi.clearAllMocks()
})

describe('useAuthStore', () => {
  it('starts with logged_out state', () => {
    const store = useAuthStore()
    expect(store.user).toEqual({ logged_in: false })
    expect(store.quota).toBeNull()
    expect(store.quotaLoading).toBe(false)
  })

  it('fetchUser sets user on success', async () => {
    vi.mocked(authService.fetchMe).mockResolvedValue({
      logged_in: true,
      user_id: 'github:test',
      provider: 'github',
    })
    const store = useAuthStore()
    await store.fetchUser()
    expect(store.user.logged_in).toBe(true)
    expect(store.user.user_id).toBe('github:test')
  })

  it('fetchUser keeps logged_out on error', async () => {
    vi.mocked(authService.fetchMe).mockRejectedValue(new Error('fail'))
    const store = useAuthStore()
    await store.fetchUser()
    expect(store.user).toEqual({ logged_in: false })
  })

  it('fetchQuota sets quota and manages loading state', async () => {
    vi.mocked(authService.fetchQuota).mockResolvedValue({
      used: 5, limit: 50, remaining: 45,
    })
    const store = useAuthStore()
    const promise = store.fetchQuota()
    expect(store.quotaLoading).toBe(true)
    await promise
    expect(store.quota).toEqual({ used: 5, limit: 50, remaining: 45 })
    expect(store.quotaLoading).toBe(false)
  })

  it('fetchQuota handles error gracefully', async () => {
    vi.mocked(authService.fetchQuota).mockRejectedValue(new Error('fail'))
    const store = useAuthStore()
    await store.fetchQuota()
    expect(store.quota).toBeNull()
    expect(store.quotaLoading).toBe(false)
  })

  it('logout calls service, resets user, and reloads page', async () => {
    const reloadSpy = vi.fn()
    Object.defineProperty(window, 'location', {
      value: { reload: reloadSpy },
      writable: true,
    })
    const store = useAuthStore()
    store.user = { logged_in: true, user_id: 'github:test' }
    await store.logout()
    expect(authService.logout).toHaveBeenCalled()
    expect(store.user).toEqual({ logged_in: false })
    expect(reloadSpy).toHaveBeenCalled()
  })
})
