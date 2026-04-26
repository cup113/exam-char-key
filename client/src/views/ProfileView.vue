<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()

interface QuotaInfo {
  used: number
  limit: number
  remaining: number
}

const quota = ref<QuotaInfo | null>(null)
const loading = ref(true)

onMounted(async () => {
  await auth.fetchUser()
  try {
    const resp = await fetch('http://localhost:8000/api/quota', { credentials: 'include' })
    if (resp.ok) {
      quota.value = await resp.json()
    }
  } catch {
    // ignore
  }
  loading.value = false
})
</script>

<template>
  <div class="max-w-xl mx-auto p-10 pt-20">
    <h1 class="text-2xl font-bold mb-6">个人管理</h1>

    <div v-if="loading" class="text-gray-400">加载中...</div>

    <template v-if="!loading && auth.user.logged_in">
      <section class="bg-white rounded-xl border border-gray-200 p-6 mb-6">
        <h2 class="text-sm font-bold text-gray-500 uppercase tracking-wide mb-4">账号信息</h2>
        <div class="space-y-3">
          <div class="flex justify-between">
            <span class="text-gray-500">用户 ID</span>
            <span class="font-mono text-sm">{{ auth.user.user_id }}</span>
          </div>
          <div class="flex justify-between">
            <span class="text-gray-500">登录方式</span>
            <span class="capitalize">{{ auth.user.provider }}</span>
          </div>
        </div>
      </section>

      <section class="bg-white rounded-xl border border-gray-200 p-6">
        <h2 class="text-sm font-bold text-gray-500 uppercase tracking-wide mb-4">今日额度</h2>
        <div v-if="quota" class="space-y-3">
          <div class="flex justify-between">
            <span class="text-gray-500">已用</span>
            <span>{{ quota.used }} 次</span>
          </div>
          <div class="flex justify-between">
            <span class="text-gray-500">每日上限</span>
            <span>{{ quota.limit }} 次</span>
          </div>
          <div class="flex justify-between font-medium">
            <span class="text-gray-500">剩余</span>
            <span :class="quota.remaining < 5 ? 'text-red-500' : 'text-green-600'">
              {{ quota.remaining }} 次
            </span>
          </div>
          <div class="w-full bg-gray-100 rounded-full h-2 mt-2">
            <div class="h-2 rounded-full transition-all duration-300"
              :class="quota.remaining < 5 ? 'bg-red-400' : 'bg-blue-400'"
              :style="{ width: (quota.used / quota.limit * 100) + '%' }">
            </div>
          </div>
        </div>
        <p v-else class="text-gray-400 text-sm">获取额度信息失败</p>
      </section>
    </template>

    <div v-if="!loading && !auth.user.logged_in" class="text-center text-gray-400 py-20">
      <p class="mb-4">请先登录</p>
      <div class="flex gap-3 justify-center">
        <a href="http://localhost:8000/auth/github/login"
          class="px-4 py-2 bg-gray-900 text-white rounded hover:bg-gray-700 text-sm">GitHub 登录</a>
        <a href="http://localhost:8000/auth/gitee/login"
          class="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-500 text-sm">Gitee 登录</a>
      </div>
    </div>
  </div>
</template>
