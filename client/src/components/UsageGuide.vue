<script setup lang="ts">
defineProps<{
  show: boolean
}>()

const emit = defineEmits<{
  dismiss: []
}>()
</script>

<template>
  <Teleport to="body">
    <div v-if="show" class="fixed inset-0 z-50 flex items-center justify-center bg-black/30" @click.self="emit('dismiss')">
      <div class="bg-white dark:bg-gray-900 rounded-xl p-6 w-[90vw] max-w-lg max-h-[85vh] overflow-y-auto space-y-5 shadow-2xl">
        <div class="flex items-center justify-between">
          <h2 class="text-lg font-bold">使用指南</h2>
          <button @click="emit('dismiss')"
            class="text-gray-400 dark:text-gray-500 hover:text-gray-800 dark:hover:text-white text-lg">✕</button>
        </div>

        <div class="space-y-4 text-sm text-gray-700 dark:text-gray-300 leading-relaxed">
          <div>
            <div class="font-semibold text-base text-gray-900 dark:text-gray-100 mb-1">① 输入文本</div>
            <p>在文本区粘贴或输入文言文原文。点击「编辑文本」可随时修改内容。</p>
          </div>

          <div>
            <div class="font-semibold text-base text-gray-900 dark:text-gray-100 mb-1">② 划词查询</div>
            <p>选中任意字词，弹出操作栏。点击「快速分析」获取 AI 释义 + <strong>汉典字典注解</strong>（实时爬取汉典网的结构化释义），或「深度分析」获取更详细的 AI 解析。</p>
          </div>

          <div>
            <div class="font-semibold text-base text-gray-900 dark:text-gray-100 mb-1">③ 查看结果</div>
            <p>右侧面板展示每词的：快捷回答、汉典字典释义、语料匹配、深度分析。点击已追踪的词可回看结果。</p>
          </div>

          <div>
            <div class="font-semibold text-base text-gray-900 dark:text-gray-100 mb-1">④ 搜索全文</div>
            <p>在查询结果面板中，可一键跳转至 <strong>ctext（中国哲学书电子化计划）、识典古籍、古文岛</strong>，搜索当前词在全网的文言文用例。</p>
          </div>

          <div>
            <div class="font-semibold text-base text-gray-900 dark:text-gray-100 mb-1">⑤ 管理文档</div>
            <p class="mb-1">登录后可通过「文档」菜单：</p>
            <ul class="list-disc list-inside space-y-0.5">
              <li><strong>保存当前分析</strong> — 存档原文 + 所有查询结果，后续随时打开继续学习</li>
              <li><strong>打开文档</strong> — 加载历史存档，继续上次的分析</li>
              <li>支持<strong>公开分享</strong>，生成链接给他人查看</li>
            </ul>
          </div>

          <div>
            <div class="font-semibold text-base text-gray-900 dark:text-gray-100 mb-1">⑥ 追踪词操作</div>
            <p>点击已追踪的词可高亮定位到原文；点击词条上的 ✕ 可移除单个追踪词。</p>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>
