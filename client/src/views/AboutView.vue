<script lang="ts" setup>
import router from '@/router';
import { onMounted } from 'vue';

onMounted(() => {
  const isNewUser = localStorage.getItem('EC_visited') === null;
  if (!isNewUser) {
    router.replace('/query');
  }
});
</script>

<template>
  <div class="max-w-4xl mx-auto px-4 py-8" data-guide-step="0.1">
    <div class="text-center mb-12">
      <h1 class="text-3xl md:text-4xl font-bold text-primary-800 mb-4">Exam Char Key</h1>
      <p class="text-lg text-secondary-600 max-w-2xl mx-auto">
        一个专注于古代汉字解释和AI辅助学习的中文语言学习平台
      </p>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-2 gap-8 mb-12">
      <div class="bg-white rounded-xl shadow-md p-6 border border-secondary-200">
        <h2 class="text-xl font-semibold text-primary-700 mb-3">🎯 核心功能</h2>
        <ul class="space-y-2 text-secondary-700">
          <li class="flex items-start">
            <span class="text-primary-500 mr-2">•</span>
            <span><strong>AI快速回答:</strong> 迅速获取语境中的文言释义</span>
          </li>
          <li class="flex items-start">
            <span class="text-primary-500 mr-2">•</span>
            <span><strong>AI深度回答:</strong> 结合网络资料让 AI 深度思考再回答</span>
          </li>
          <li class="flex items-start">
            <span class="text-primary-500 mr-2">•</span>
            <span><strong>汉典集成:</strong> 实时查询汉典定义</span>
          </li>
          <li class="flex items-start">
            <span class="text-primary-500 mr-2">•</span>
            <span><strong>教材集成:</strong> 提供教材中的注释原文</span>
          </li>
          <li class="flex items-start">
            <span class="text-primary-500 mr-2">•</span>
            <span><strong>频率分析:</strong> 统计字符在不同上下文中的使用频率</span>
          </li>
        </ul>
      </div>

      <div class="bg-white rounded-xl shadow-md p-6 border border-secondary-200">
        <h2 class="text-xl font-semibold text-primary-700 mb-3">🤖 AI 能力</h2>
        <ul class="space-y-2 text-secondary-700">
          <li class="flex items-start">
            <span class="text-primary-500 mr-2">•</span>
            <span><strong>多AI模型:</strong> 集成Qwen模型，适用于不同任务</span>
          </li>
          <li class="flex items-start">
            <span class="text-primary-500 mr-2">•</span>
            <span><strong>上下文理解:</strong> 特别针对中文语言细微差别的训练</span>
          </li>
          <li class="flex items-start">
            <span class="text-primary-500 mr-2">•</span>
            <span><strong>实时处理:</strong> 流式AI响应，提升用户体验</span>
          </li>
        </ul>
      </div>
    </div>

    <div class="bg-white rounded-xl shadow-md p-6 border border-secondary-200 mb-12">
      <h2 class="text-xl font-semibold text-primary-700 mb-4">📚 教育工具</h2>
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div class="flex items-start">
          <div class="bg-primary-100 p-3 rounded-lg mr-4">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-primary-600" fill="none" viewBox="0 0 24 24"
              stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <div>
            <h3 class="font-medium text-secondary-800">历史记录跟踪</h3>
            <p class="text-secondary-600 text-sm">跟踪您的查询和学习进度，支持导出功能用于复习</p>
          </div>
        </div>
        <div class="flex items-start">
          <div class="bg-primary-100 p-3 rounded-lg mr-4">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-primary-600" fill="none" viewBox="0 0 24 24"
              stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                d="M7 8h10M7 12h4m1 8l-4-4H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-3l-4 4z" />
            </svg>
          </div>
          <div>
            <h3 class="font-medium text-secondary-800">交互式界面</h3>
            <p class="text-secondary-600 text-sm">现代化的Vue.js前端，响应式设计</p>
          </div>
        </div>
      </div>
    </div>

    <div class="text-center">
      <RouterLink to="/query"
        class="inline-block bg-primary-600 hover:bg-primary-700 text-white font-medium py-3 px-8 rounded-lg transition duration-300">
        开始使用
      </RouterLink>
    </div>
  </div>
</template>