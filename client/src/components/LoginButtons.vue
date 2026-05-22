<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(defineProps<{
  size?: 'sm' | 'md'
}>(), {
  size: 'md',
})

const btnClass = computed(() =>
  props.size === 'sm' ? 'px-3 py-1.5 text-xs' : 'px-4 py-2 text-sm'
)
</script>

<template>
  <a href="/api/auth/github/login"
    class="bg-gray-900 text-white rounded hover:bg-gray-700 whitespace-nowrap"
    :class="btnClass" data-umami-event="login-github" title="登录后配额更高，可保存查询结果">GitHub 登录</a>
  <a href="/api/auth/gitee/login"
    class="bg-green-600 text-white rounded hover:bg-green-500 whitespace-nowrap"
    :class="btnClass" data-umami-event="login-gitee" title="登录后配额更高，可保存查询结果">Gitee 登录</a>
</template>
