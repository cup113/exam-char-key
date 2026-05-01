<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { RouterView, RouterLink } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import LoginButtons from '@/components/LoginButtons.vue'

const auth = useAuthStore()
const mobileMenuOpen = ref(false)

onMounted(() => auth.fetchUser())
</script>

<template>
  <div class="min-h-screen bg-gray-50 text-gray-800 font-sans flex flex-col">
    <header
      class="fixed top-0 left-0 right-0 h-12 bg-white border-b border-gray-200 flex items-center justify-between px-6 z-40">
      <RouterLink to="/" class="font-bold text-lg">Exam Char Key - 文言释义</RouterLink>
      <div class="hidden lg:flex items-center gap-4 text-sm">
        <nav class="flex gap-4 mr-2">
          <RouterLink to="/" class="text-gray-500 hover:text-gray-800">阅读</RouterLink>
          <RouterLink to="/history" class="text-gray-500 hover:text-gray-800">历史记录</RouterLink>
          <RouterLink to="/profile" class="text-gray-500 hover:text-gray-800">个人</RouterLink>
        </nav>
        <span v-if="auth.user.logged_in" class="text-gray-500">{{ auth.user.user_id }}</span>
        <LoginButtons v-if="!auth.user.logged_in" size="sm" />
        <button v-if="auth.user.logged_in" @click="auth.logout" class="text-gray-400 hover:text-red-500">退出</button>
      </div>
      <button @click="mobileMenuOpen = !mobileMenuOpen"
        class="lg:hidden p-2 text-gray-600 hover:text-gray-800 -mr-2">
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path v-if="!mobileMenuOpen" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
          <path v-else stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>
    </header>

    <div v-if="mobileMenuOpen"
      class="fixed inset-0 z-30 bg-black/20 lg:hidden"
      @click="mobileMenuOpen = false">
    </div>
    <div v-if="mobileMenuOpen"
      class="fixed top-12 left-0 right-0 z-40 bg-white border-b border-gray-200 shadow-lg lg:hidden">
      <div class="px-6 py-4">
        <nav class="flex flex-col gap-1 text-sm">
          <RouterLink to="/" class="text-gray-600 hover:text-gray-800 py-1.5" @click="mobileMenuOpen = false">阅读</RouterLink>
          <RouterLink to="/history" class="text-gray-600 hover:text-gray-800 py-1.5" @click="mobileMenuOpen = false">历史记录</RouterLink>
          <RouterLink to="/profile" class="text-gray-600 hover:text-gray-800 py-1.5" @click="mobileMenuOpen = false">个人</RouterLink>
        </nav>
        <div v-if="!auth.user.logged_in" class="flex gap-2 pt-3 border-t border-gray-100 mt-2">
          <LoginButtons size="sm" />
        </div>
        <div v-else class="flex items-center gap-3 text-sm pt-3 border-t border-gray-100 mt-2">
          <span class="text-gray-500">{{ auth.user.user_id }}</span>
          <button @click="auth.logout" class="text-gray-400 hover:text-red-500">退出</button>
        </div>
      </div>
    </div>

    <main class="flex-1 pt-12">
      <RouterView />
    </main>
  </div>
</template>
