import { ref } from 'vue'
import { defineStore } from 'pinia'
import type { UserInfo } from '@/types'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<UserInfo>({ logged_in: false })

  async function fetchUser() {
    try {
      const resp = await fetch('/api/auth/me')
      user.value = await resp.json()
    } catch {
      user.value = { logged_in: false }
    }
  }

  async function logout() {
    await fetch('/api/auth/logout', { method: 'POST' })
    user.value = { logged_in: false }
    location.reload()
  }

  return { user, fetchUser, logout }
})
