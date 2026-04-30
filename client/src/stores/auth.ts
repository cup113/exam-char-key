import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { useLocalStorage } from '@vueuse/core'
import type { UserInfo } from '@/types'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<UserInfo>({ logged_in: false })

  const quota = ref<{ used: number; limit: number; remaining: number } | null>(null)
  const quotaLoading = ref(false)
  const quotaPromptDismissed = useLocalStorage('ECK_quota-prompt-dismissed', false)

  const showQuotaPrompt = computed(() => {
    if (quotaPromptDismissed.value) return false
    if (user.value.logged_in) return false
    if (!quota.value) return false
    return quota.value.remaining <= 15
  })

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

  function dismissQuotaPrompt() {
    quotaPromptDismissed.value = true
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
    quotaPromptDismissed,
    showQuotaPrompt,
    fetchUser,
    fetchQuota,
    dismissQuotaPrompt,
    logout,
  }
})
