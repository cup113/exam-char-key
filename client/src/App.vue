<script setup lang="ts">
import { onMounted } from 'vue'
import { RouterView } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()

onMounted(() => auth.fetchUser())
</script>

<template>
  <div class="min-h-screen bg-gray-50 text-gray-800 font-sans flex flex-col">
    <header
      class="fixed top-0 left-0 right-0 h-12 bg-white border-b border-gray-200 flex items-center justify-between px-6 z-40">
      <div class="flex items-center gap-6">
        <a href="/" class="font-bold text-lg">📖 划词查询</a>
        <nav class="flex gap-4 text-sm">
          <a href="/" class="text-gray-500 hover:text-gray-800">阅读</a>
          <a href="/history" class="text-gray-500 hover:text-gray-800">历史记录</a>
          <a href="/profile" class="text-gray-500 hover:text-gray-800">个人</a>
        </nav>
      </div>
      <div class="flex items-center gap-4 text-sm">
        <span v-if="auth.user.logged_in" class="text-gray-500">{{ auth.user.user_id }}</span>
        <a v-if="!auth.user.logged_in" href="http://localhost:8000/auth/github/login"
          class="px-3 py-1 bg-gray-900 text-white rounded hover:bg-gray-700">GitHub 登录</a>
        <a v-if="!auth.user.logged_in" href="http://localhost:8000/auth/gitee/login"
          class="px-3 py-1 bg-green-600 text-white rounded hover:bg-green-500">Gitee 登录</a>
        <button v-if="auth.user.logged_in" @click="auth.logout" class="text-gray-400 hover:text-red-500">退出</button>
      </div>
    </header>
    <main class="flex-1 pt-12">
      <RouterView />
    </main>
  </div>
</template>
