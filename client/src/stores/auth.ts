import { ref } from 'vue'
import { defineStore } from 'pinia'
import type { UserInfo } from '@/types'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<UserInfo>({ logged_in: false })

  const quota = ref<{ used: number; limit: number; remaining: number } | null>(null)
  const quotaLoading = ref(false)

  async function fetchUser() {
    try {
      const resp = await fetch('/api/auth/me')
      user.value = await resp.json()
    } catch {
      user.value = { logged_in: false }
    }
  }

  async function fetchQuota() {
    quotaLoading.value = true
    try {
      const resp = await fetch('/api/quota', { credentials: 'include' })
      if (resp.ok) {
        quota.value = await resp.json()
      }
    } catch { /* ignore */ }
    quotaLoading.value = false
  }

  async function logout() {
    await fetch('/api/auth/logout', { method: 'POST' })
    user.value = { logged_in: false }
    location.reload()
  }

  return {
    user,
    quota,
    quotaLoading,
    fetchUser,
    fetchQuota,
    logout,
  }
})
