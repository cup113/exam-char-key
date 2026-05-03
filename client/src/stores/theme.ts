import { ref, watch } from 'vue'
import { defineStore } from 'pinia'
import { useLocalStorage } from '@vueuse/core'

export const useThemeStore = defineStore('theme', () => {
  const systemDark = window.matchMedia('(prefers-color-scheme: dark)').matches
  const userPreference = useLocalStorage<boolean | null>('ECK_dark', null)

  const isDark = ref(userPreference.value ?? systemDark)

  watch(isDark, apply, { immediate: true })

  window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
    if (userPreference.value === null) {
      isDark.value = e.matches
    }
  })

  function apply() {
    document.documentElement.classList.toggle('dark', isDark.value)
  }

  function toggle() {
    userPreference.value = !isDark.value
    isDark.value = userPreference.value
  }

  return { isDark, toggle }
})
