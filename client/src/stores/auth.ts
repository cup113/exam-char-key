import { ref } from 'vue'
import { defineStore } from 'pinia'
import type { UserInfo } from '@/types'
import * as authService from '@/services/authService'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<UserInfo>({ logged_in: false })

  const quota = ref<{ used: number; limit: number; remaining: number } | null>(null)
  const quotaLoading = ref(false)

  async function fetchUser() {
    try {
      user.value = await authService.fetchMe()
    } catch {
      user.value = { logged_in: false }
    }
  }

  async function fetchQuota() {
    quotaLoading.value = true
    try {
      quota.value = await authService.fetchQuota()
    } catch { /* ignore */ }
    quotaLoading.value = false
  }

  async function logout() {
    await authService.logout()
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
