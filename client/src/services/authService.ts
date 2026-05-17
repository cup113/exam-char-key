import { apiClient } from './apiClient'
import type { UserInfo } from '@/types'

export function fetchMe(): Promise<UserInfo> {
  return apiClient.get<UserInfo>('/api/auth/me')
}

export function fetchQuota(): Promise<{ used: number; limit: number; remaining: number }> {
  return apiClient.get<{ used: number; limit: number; remaining: number }>('/api/quota')
}

export async function logout(): Promise<void> {
  await apiClient.post('/api/auth/logout')
}
