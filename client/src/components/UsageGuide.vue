<script setup lang="ts">
import { version } from '../../package.json'
import { ref } from 'vue'

defineProps<{
  show: boolean
}>()

const emit = defineEmits<{
  dismiss: []
}>()

const activeTab = ref<'guide' | 'about'>('guide')
</script>

<template>
  <Teleport to="body">
    <div v-if="show" class="fixed inset-0 z-50 flex items-center justify-center bg-black/30" @click.self="emit('dismiss')">
      <div class="bg-white dark:bg-gray-900 rounded-xl p-6 w-[90vw] max-w-lg max-h-[85vh] overflow-y-auto space-y-4 shadow-2xl">
        <div class="flex items-center justify-between">
          <h2 class="text-lg font-bold">使用指南</h2>
          <button @click="emit('dismiss')"
            class="text-gray-400 dark:text-gray-500 hover:text-gray-800 dark:hover:text-white text-lg">✕</button>
        </div>

        <div class="flex gap-0 border-b border-gray-200 dark:border-gray-700">
          <button @click="activeTab = 'guide'"
            :class="['px-3 py-2 text-sm font-medium transition-colors border-b-2 -mb-px',
                     activeTab === 'guide'
                       ? 'text-blue-600 dark:text-blue-400 border-blue-600 dark:border-blue-400'
                       : 'text-gray-500 dark:text-gray-400 border-transparent hover:text-gray-700 dark:hover:text-gray-300']">
            📖 使用指南
          </button>
          <button @click="activeTab = 'about'"
            :class="['px-3 py-2 text-sm font-medium transition-colors border-b-2 -mb-px',
                     activeTab === 'about'
                       ? 'text-blue-600 dark:text-blue-400 border-blue-600 dark:border-blue-400'
                       : 'text-gray-500 dark:text-gray-400 border-transparent hover:text-gray-700 dark:hover:text-gray-300']">
            ❤️ 关于 &amp; 致谢
          </button>
        </div>

        <div v-if="activeTab === 'guide'" class="space-y-3 text-sm text-gray-700 dark:text-gray-300 leading-relaxed">
          <details open class="group">
            <summary
              class="font-semibold text-base text-gray-900 dark:text-gray-100 cursor-pointer list-none flex items-center gap-1.5">
              <span class="transition-transform group-open:rotate-90 inline-block">▶</span>
              📝 文本与搜索
            </summary>
            <div class="mt-2 space-y-3 pl-5 border-l-2 border-blue-200 dark:border-blue-800 ml-0.5">
              <div>
                <div class="font-semibold mb-0.5">
                  <span class="inline-flex items-center justify-center w-4.5 h-4.5 rounded-full bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300 text-[10px] mr-1 shrink-0">1</span>
                  输入文本
                </div>
                <p>在文本区粘贴或输入文言文原文。点击「编辑文本」可随时修改内容。</p>
              </div>
              <div>
                <div class="font-semibold mb-0.5">
                  <span class="inline-flex items-center justify-center w-4.5 h-4.5 rounded-full bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300 text-[10px] mr-1 shrink-0">2</span>
                  搜索全文
                </div>
                <p>在文本区下方的搜索栏中，输入篇名、作者或文章开头几个字，可跳转至 <strong>ctext（中国哲学书电子化计划）、识典古籍、古文岛</strong> 搜索全文文言文用例。</p>
              </div>
            </div>
          </details>

          <details open class="group">
            <summary
              class="font-semibold text-base text-gray-900 dark:text-gray-100 cursor-pointer list-none flex items-center gap-1.5">
              <span class="transition-transform group-open:rotate-90 inline-block">▶</span>
              🔍 查询与分析
            </summary>
            <div class="mt-2 space-y-3 pl-5 border-l-2 border-green-200 dark:border-green-800 ml-0.5">
              <div>
                <div class="font-semibold mb-0.5">
                  <span class="inline-flex items-center justify-center w-4.5 h-4.5 rounded-full bg-green-100 dark:bg-green-900 text-green-700 dark:text-green-300 text-[10px] mr-1 shrink-0">3</span>
                  划词查询
                </div>
                <p>选中任意字词（限 20 字以内），弹出操作栏。点击「快速分析」获取 AI 释义 + <strong>汉典字典注解</strong>（实时爬取汉典网的结构化释义），或「深度分析」获取更详细的 AI 解析。</p>
              </div>
              <div>
                <div class="font-semibold mb-0.5">
                  <span class="inline-flex items-center justify-center w-4.5 h-4.5 rounded-full bg-green-100 dark:bg-green-900 text-green-700 dark:text-green-300 text-[10px] mr-1 shrink-0">4</span>
                  查看结果
                </div>
                <p>右侧面板展示每词的：快捷回答、汉典字典释义、语料匹配、深度分析。点击已追踪的词可回看结果。汉典释义中，蓝色数字 badge 表示该义项与当前词语<strong>相关度高</strong>，灰色表示相关度低。</p>
              </div>
              <div>
                <div class="font-semibold mb-0.5">
                  <span class="inline-flex items-center justify-center w-4.5 h-4.5 rounded-full bg-green-100 dark:bg-green-900 text-green-700 dark:text-green-300 text-[10px] mr-1 shrink-0">5</span>
                  追踪词操作
                </div>
                <p>点击已追踪的词可高亮定位到原文；点击词条上的 ✕ 可移除单个追踪词。</p>
              </div>
            </div>
          </details>

          <details class="group">
            <summary
              class="font-semibold text-base text-gray-900 dark:text-gray-100 cursor-pointer list-none flex items-center gap-1.5">
              <span class="transition-transform group-open:rotate-90 inline-block">▶</span>
              💾 数据管理
            </summary>
            <div class="mt-2 space-y-3 pl-5 border-l-2 border-purple-200 dark:border-purple-800 ml-0.5">
              <div>
                <div class="font-semibold mb-0.5">
                  <span class="inline-flex items-center justify-center w-4.5 h-4.5 rounded-full bg-purple-100 dark:bg-purple-900 text-purple-700 dark:text-purple-300 text-[10px] mr-1 shrink-0">6</span>
                  保存结果
                </div>
                <p>在右侧面板可点击「保存到历史」，将 AI 回答存入<strong>历史记录</strong>。历史页面支持按词语搜索、批量删除，并可导出为 <strong>JSON / Word / Anki</strong> 格式用于复习。</p>
              </div>
              <div>
                <div class="font-semibold mb-0.5">
                  <span class="inline-flex items-center justify-center w-4.5 h-4.5 rounded-full bg-purple-100 dark:bg-purple-900 text-purple-700 dark:text-purple-300 text-[10px] mr-1 shrink-0">7</span>
                  管理文档
                </div>
                <p class="mb-1">登录后可通过「文档」菜单：</p>
                <ul class="list-disc list-inside space-y-0.5">
                  <li><strong>保存当前分析</strong> — 存档原文 + 所有查询结果，后续随时打开继续学习</li>
                  <li><strong>打开文档</strong> — 加载历史存档，继续上次的分析</li>
                  <li>支持<strong>公开分享</strong>，生成链接给他人查看，对方可继续查询</li>
                </ul>
              </div>
            </div>
          </details>

          <div
            class="flex items-start gap-2 p-3 rounded-lg bg-blue-50 dark:bg-blue-950/40 border border-blue-200 dark:border-blue-800">
            <span class="text-base shrink-0">⚡</span>
            <div>
              <div class="font-semibold text-sm text-gray-900 dark:text-gray-100">配额说明</div>
              <p class="text-xs mt-0.5">每位用户每日有查询次数限制，显示在页面顶部。登录后可获得更高配额。游客使用共享免费额度。</p>
            </div>
          </div>
        </div>

        <div v-if="activeTab === 'about'" class="space-y-4 text-sm text-gray-700 dark:text-gray-300 leading-relaxed">
          <div>
            <div class="font-semibold text-base text-gray-900 dark:text-gray-100 mb-1">关于本应用</div>
            <p class="text-xs text-gray-500">版本 {{ version }}</p>
            <div class="flex flex-col gap-1 mt-2">
              <a href="https://github.com/cup113/exam-char-key" target="_blank" rel="noopener noreferrer"
                class="text-blue-600 dark:text-blue-400 hover:underline text-xs">GitHub 开源仓库</a>
              <a href="https://f.kdocs.cn/g/iuGauWIo/" target="_blank" rel="noopener noreferrer"
                class="text-blue-600 dark:text-blue-400 hover:underline text-xs">反馈建议</a>
            </div>
          </div>

          <hr class="border-gray-200 dark:border-gray-700">

          <div>
            <div class="font-semibold text-base text-gray-900 dark:text-gray-100 mb-2">数据来源致谢</div>
            <ul class="space-y-3">
              <li class="flex items-start gap-2.5">
                <img src="https://zdic.net/images/logo.png" alt="汉典"
                  class="shrink-0 h-7 w-auto object-contain bg-white dark:bg-gray-800 rounded p-0.5">
                <div>
                  <a href="https://www.zdic.net" target="_blank" rel="noopener noreferrer"
                    class="font-medium text-blue-600 dark:text-blue-400 hover:underline">汉典 (zdic.net)</a>
                  <p class="text-xs text-gray-500 dark:text-gray-400 mt-0.5">字典释义数据。本应用实时爬取汉典网的结构化释义，为用户提供权威的字词注解。</p>
                </div>
              </li>
              <li class="flex items-start gap-2.5">
                <img src="https://lf-welfare.amemv.com/obj/douyin-welfare-image/guji/shidian/static/image/home-title.68039153.png" alt="识典古籍"
                  class="shrink-0 h-7 w-auto object-contain bg-white dark:bg-gray-800 rounded p-0.5">
                <div>
                  <a href="https://www.shidianguji.com" target="_blank" rel="noopener noreferrer"
                    class="font-medium text-blue-600 dark:text-blue-400 hover:underline">识典古籍</a>
                  <p class="text-xs text-gray-500 dark:text-gray-400 mt-0.5">古籍搜索支持。</p>
                </div>
              </li>
              <li class="flex items-start gap-2.5">
                <img src="https://ctext.org/favicon.ico" alt="ctext"
                  class="shrink-0 w-5 h-5 object-contain">
                <div>
                  <a href="https://ctext.org" target="_blank" rel="noopener noreferrer"
                    class="font-medium text-blue-600 dark:text-blue-400 hover:underline">中国哲学书电子化计划 (ctext.org)</a>
                  <p class="text-xs text-gray-500 dark:text-gray-400 mt-0.5">提供先秦两汉及汉后全文搜索接口。</p>
                </div>
              </li>
              <li class="flex items-start gap-2.5">
                <img src="https://www.guwendao.net/favicon.ico" alt="古文岛"
                  class="shrink-0 w-5 h-5 object-contain">
                <div>
                  <a href="https://www.guwendao.net" target="_blank" rel="noopener noreferrer"
                    class="font-medium text-blue-600 dark:text-blue-400 hover:underline">古文岛</a>
                  <p class="text-xs text-gray-500 dark:text-gray-400 mt-0.5">文言文搜索支持。</p>
                </div>
              </li>
            </ul>
          </div>

          <hr class="border-gray-200 dark:border-gray-700">

          <p class="text-xs text-gray-500 dark:text-gray-400">本应用仅供非商用学习用途。所有第三方数据版权归各自版权方所有。</p>
        </div>
      </div>
    </div>
  </Teleport>
</template>
