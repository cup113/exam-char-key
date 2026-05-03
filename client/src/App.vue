<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { RouterView, RouterLink } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useThemeStore } from '@/stores/theme'
import LoginButtons from '@/components/LoginButtons.vue'

const auth = useAuthStore()
const theme = useThemeStore()
const mobileMenuOpen = ref(false)

onMounted(() => auth.fetchUser())
</script>

<template>
  <div class="min-h-screen bg-gray-50 dark:bg-gray-950 text-gray-800 dark:text-gray-100 font-sans flex flex-col">
    <header
      class="fixed top-0 left-0 right-0 h-12 bg-white dark:bg-[#1a1b23] border-b border-gray-200 dark:border-gray-700 flex items-center justify-between px-6 z-40">
      <RouterLink to="/" class="font-bold text-lg">Exam Char Key - 文言释义</RouterLink>
      <div class="hidden lg:flex items-center gap-3 text-sm">
        <nav class="flex gap-4 mr-1">
          <RouterLink to="/" class="text-gray-500 dark:text-gray-400 hover:text-gray-800 dark:hover:text-white">阅读</RouterLink>
          <RouterLink to="/history" class="text-gray-500 dark:text-gray-400 hover:text-gray-800 dark:hover:text-white" data-umami-event="header-page-switch-history">历史记录</RouterLink>
          <RouterLink to="/profile" class="text-gray-500 dark:text-gray-400 hover:text-gray-800 dark:hover:text-white" data-umami-event="header-page-switch-account">个人</RouterLink>
          <RouterLink v-if="auth.user.is_admin" to="/admin" class="text-orange-500 hover:text-orange-400 font-medium" data-umami-event="header-page-switch-admin">管理</RouterLink>
        </nav>
        <button @click="theme.toggle" class="text-gray-500 dark:text-gray-400 hover:text-gray-800 dark:hover:text-white text-base p-0.5" title="切换暗黑模式">
          {{ theme.isDark ? '☀️' : '🌙' }}
        </button>
        <span v-if="auth.user.logged_in" class="text-gray-500 dark:text-gray-400">{{ auth.user.user_id }}</span>
        <LoginButtons v-if="!auth.user.logged_in" size="sm" />
        <button v-if="auth.user.logged_in" @click="auth.logout" class="text-gray-400 dark:text-gray-500 hover:text-red-500" data-umami-event="header-logout">退出</button>
      </div>
      <button @click="mobileMenuOpen = !mobileMenuOpen"
        class="lg:hidden p-2 text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-white -mr-2"  data-umami-event="header-mobile-menu-open">
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path v-if="!mobileMenuOpen" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
          <path v-else stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>
    </header>

    <div v-if="mobileMenuOpen"
      class="fixed inset-0 z-30 bg-black/20 dark:bg-black/40 lg:hidden"
      @click="mobileMenuOpen = false">
    </div>
    <div v-if="mobileMenuOpen"
      class="fixed top-12 left-0 right-0 z-40 bg-white dark:bg-[#1a1b23] border-b border-gray-200 dark:border-gray-700 shadow-lg lg:hidden">
      <div class="px-6 py-4">
        <nav class="flex flex-col gap-1 text-sm">
          <RouterLink to="/" class="text-gray-600 dark:text-gray-300 hover:text-gray-800 dark:hover:text-white py-1.5" @click="mobileMenuOpen = false">阅读</RouterLink>
          <RouterLink to="/history" class="text-gray-600 dark:text-gray-300 hover:text-gray-800 dark:hover:text-white py-1.5" @click="mobileMenuOpen = false" data-umami-event="header-page-switch-history">历史记录</RouterLink>
          <RouterLink to="/profile" class="text-gray-600 dark:text-gray-300 hover:text-gray-800 dark:hover:text-white py-1.5" @click="mobileMenuOpen = false" data-umami-event="header-page-switch-account">个人</RouterLink>
          <RouterLink v-if="auth.user.is_admin" to="/admin" class="text-orange-500 hover:text-orange-400 font-medium py-1.5" @click="mobileMenuOpen = false" data-umami-event="header-page-switch-admin">管理</RouterLink>
        </nav>
        <div class="pt-3 border-t border-gray-100 dark:border-gray-800 mt-2">
          <button @click="theme.toggle" class="flex items-center gap-2 text-gray-500 dark:text-gray-400 hover:text-gray-800 dark:hover:text-white text-sm py-1" title="切换暗黑模式">
            <span class="text-base">{{ theme.isDark ? '☀️' : '🌙' }}</span>
            <span>{{ theme.isDark ? '浅色模式' : '深色模式' }}</span>
          </button>
        </div>
        <div v-if="!auth.user.logged_in" class="flex gap-2 pt-3 border-t border-gray-100 dark:border-gray-800 mt-2">
          <LoginButtons size="sm" />
        </div>
        <div v-else class="flex items-center gap-3 text-sm pt-3 border-t border-gray-100 dark:border-gray-800 mt-2">
          <span class="text-gray-500 dark:text-gray-400">{{ auth.user.user_id }}</span>
          <button @click="auth.logout" class="text-gray-400 dark:text-gray-500 hover:text-red-500" data-umami-event="header-logout">退出</button>
        </div>
      </div>
    </div>

    <main class="flex-1 pt-12">
      <RouterView />
    </main>
  </div>
</template>
