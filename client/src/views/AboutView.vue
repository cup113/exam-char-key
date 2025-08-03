<script lang="ts" setup>
import FlashIcon from '@/components/icons/FlashIcon.vue';
import BrainIcon from '@/components/icons/BrainIcon.vue';
import BookIcon from '@/components/icons/BookIcon.vue';
import DictionaryIcon from '@/components/icons/DictionaryIcon.vue';
import GithubIcon from '@/components/icons/GithubIcon.vue';

const features = [
  {
    icon: FlashIcon,
    title: 'AI快速回答',
    description: '迅速获取语境中的文言释义'
  },
  {
    icon: BrainIcon,
    title: 'AI深度回答',
    description: '结合字典资料让 AI 深度思考再回答'
  },
  {
    icon: DictionaryIcon,
    title: '汉典集成',
    description: '实时查询汉典定义'
  },
  {
    icon: BookIcon,
    title: '教材集成',
    description: '提供教材中的注释原文'
  }
];

// 使用指南数据
const guideSteps = [
  '点击"开始使用"，在查询页面输入文本，或使用默认文本。',
  '点击文本内容选中上下文，然后点击上下文中的字词。',
  '点击"查询"同时获取 AI 快速回答、深度思考、汉典搜索结果、教材数据等。',
  '点击"保存记录"选取你最满意的答案采纳。更多功能见"历史"界面。',
  '点击"设置"进行深度配置，注册账号获得更多额度。'
];
</script>

<template>
  <div class="max-w-4xl mx-auto px-4 py-8">
    <div class="text-center mb-10">
      <h1 class="text-3xl md:text-4xl font-bold text-primary-800 mb-4">Exam Char Key</h1>
      <p class="text-lg text-secondary-600 max-w-2xl mx-auto">
        专注于<strong>文言文词语释义</strong>，集成 AI 助手的文言文学习辅助平台
      </p>
      <!-- 将"开始使用"按钮移到更显眼的位置 -->
      <div class="mt-8">
        <RouterLink to="/query"
          class="inline-block bg-primary-600 hover:bg-primary-700 text-white font-medium text-lg py-3 px-8 rounded-lg transition duration-300 shadow-lg">
          开始使用
        </RouterLink>
      </div>
    </div>

    <div class="bg-white rounded-xl shadow-md p-6 border border-secondary-200 mb-8">
      <h2 class="text-xl font-semibold text-primary-700 mb-4">🎯 核心功能</h2>
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div v-for="(feature, index) in features" :key="index" class="flex items-start">
          <div class="bg-primary-100 p-2 rounded-lg mr-3 mt-1">
            <component :is="feature.icon" class="h-5 w-5 text-primary-600" />
          </div>
          <div>
            <h3 class="font-medium text-secondary-800">{{ feature.title }}</h3>
            <p class="text-secondary-600 text-sm">{{ feature.description }}</p>
          </div>
        </div>
      </div>
    </div>

    <div class="bg-white rounded-xl shadow-md p-6 border border-secondary-200 mb-8">
      <h2 class="text-xl font-semibold text-primary-700 mb-4">📖 使用指南</h2>
      <div class="prose prose-primary max-w-none">
        <ol class="list-decimal pl-5 space-y-2 text-secondary-700">
          <li v-for="(step, index) in guideSteps" :key="index">{{ step }}</li>
        </ol>
      </div>
    </div>
    <div class="bg-white rounded-xl shadow-md p-6 border border-secondary-200 mb-8">
      <h2 class="text-xl font-semibold text-primary-700 mb-4">🔗 相关链接</h2>
      <div class="flex flex-wrap justify-center gap-6">
        <a href="https://github.com/cup113/exam-char-key" target="_blank"
          class="flex items-center text-primary-700 hover:text-primary-800 bg-primary-50 hover:bg-primary-100 py-2 px-4 rounded-lg transition duration-300">
          <GithubIcon class="h-5 w-5 mr-2" />
          <span class="font-medium">GitHub 仓库</span>
        </a>
        <a href="https://leximory.com" target="_blank"
          class="flex items-center text-primary-700 hover:text-primary-800 bg-primary-50 hover:bg-primary-100 py-2 px-4 rounded-lg transition duration-300">
          <BookIcon class="h-5 w-5 mr-2" />
          <span class="font-medium">[友链] Leximory</span>
          <span class="ml-2 text-sm text-primary-800 hidden sm:inline">—— 语言学地学语言</span>
        </a>
      </div>
    </div>

    <div class="bg-white rounded-xl shadow-md p-6 border border-secondary-200 mb-8 text-sm text-secondary-600">
      <div class="flex flex-col md:flex-row md:justify-between md:items-center gap-4">
        <div>
          <p>© 2025 Jason Li</p>
          <p class="mt-1">本项目基于 MIT 协议开源。</p>
        </div>
        <div>
          <a href="https://github.com/cup113/exam-char-key" target="_blank">
            <img src="https://img.shields.io/github/v/tag/cup113/exam-char-key?label=%E5%BD%93%E5%89%8D%E7%89%88%E6%9C%AC" alt="GitHub tag (latest SemVer)">
          </a>
        </div>
        <div class="flex flex-wrap gap-4">
          <RouterLink to="/query"
            class="inline-block bg-primary-600 hover:bg-primary-700 text-white font-medium py-2 px-4 rounded-lg transition duration-300">
            开始使用
          </RouterLink>
        </div>
      </div>
    </div>
  </div>
</template>