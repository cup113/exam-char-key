<script setup lang="ts">
import { onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import LoginButtons from '@/components/LoginButtons.vue'

const auth = useAuthStore()

onMounted(() => auth.fetchUser())
</script>

<template>
  <div class="max-w-xl mx-auto p-10 pt-20">
    <h1 class="text-2xl font-bold mb-6">个人管理</h1>

    <template v-if="auth.user.logged_in">
      <section class="bg-white dark:bg-[#1a1b23] rounded-xl border border-gray-200 dark:border-gray-700 p-6">
        <h2 class="text-sm font-bold text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-4">账号信息</h2>
        <div class="space-y-3">
          <div class="flex justify-between">
            <span class="text-gray-500 dark:text-gray-400">用户 ID</span>
            <span class="font-mono text-sm">{{ auth.user.user_id }}</span>
          </div>
          <div class="flex justify-between">
            <span class="text-gray-500 dark:text-gray-400">登录方式</span>
            <span class="capitalize">{{ auth.user.provider }}</span>
          </div>
        </div>
      </section>
    </template>

    <div v-if="!auth.user.logged_in" class="text-center text-gray-400 dark:text-gray-500 py-20">
      <p class="mb-4">请先登录</p>
      <div class="flex gap-3 justify-center">
        <LoginButtons size="md" />
      </div>
    </div>
  </div>
</template>
