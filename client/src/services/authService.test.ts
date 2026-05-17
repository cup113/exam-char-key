import { describe, it, expect, vi } from 'vitest'

vi.mock('./apiClient')

import { apiClient } from './apiClient'
import { fetchMe, fetchQuota, logout } from './authService'

const mockApi = vi.mocked(apiClient)

describe('authService', () => {
  it('fetchMe calls apiClient.get with /api/auth/me', async () => {
    mockApi.get.mockResolvedValue({ logged_in: true })
    const result = await fetchMe()
    expect(mockApi.get).toHaveBeenCalledWith('/api/auth/me')
    expect(result.logged_in).toBe(true)
  })

  it('fetchQuota calls apiClient.get with /api/quota', async () => {
    mockApi.get.mockResolvedValue({ used: 1, limit: 10, remaining: 9 })
    const result = await fetchQuota()
    expect(mockApi.get).toHaveBeenCalledWith('/api/quota')
    expect(result.remaining).toBe(9)
  })

  it('logout calls apiClient.post with /api/auth/logout', async () => {
    mockApi.post.mockResolvedValue(undefined)
    await logout()
    expect(mockApi.post).toHaveBeenCalledWith('/api/auth/logout')
  })
})
