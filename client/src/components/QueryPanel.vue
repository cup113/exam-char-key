<script setup lang="ts">
import { computed } from 'vue'
import DictDisplay from '@/components/DictDisplay.vue'
import DeepAnalysisSplit from '@/components/DeepAnalysisSplit.vue'
import { useWordsStore } from '@/stores/words'
import type { TrackedWord } from '@/stores/words'

const wordsStore = useWordsStore()

const props = defineProps<{
  show: boolean
  activeWord: TrackedWord | null
  savedAnswer: string
  saveSuccess: boolean
  loggedIn: boolean
}>()

const emit = defineEmits<{
  close: []
  'update:savedAnswer': [value: string]
  save: []
}>()

const deepMeaning = computed(() => {
  if (!props.activeWord?.deepThink) return ''
  for (const line of props.activeWord.deepThink.split('\n')) {
    const trimmed = line.trim()
    const match = trimmed.match(/^\[词义\]\s*(.*)$/)
    if (match) return match[1]
  }
  return ''
})

const aiAnswerForDict = computed(() => {
  const answers: string[] = []
  if (props.activeWord?.quickAnswer) answers.push(props.activeWord.quickAnswer)
  if (deepMeaning.value) answers.push(deepMeaning.value)
  return answers.length > 0 ? answers : ''
})

const hasAiContent = computed(() =>
  !!(props.activeWord?.quickAnswer || deepMeaning.value)
)

const showEmpty = computed(() =>
  !hasAiContent.value &&
  !props.activeWord?.deepThink &&
  !props.activeWord?.corpusEntries?.length &&
  !props.activeWord?.dictResult &&
  props.activeWord?.status !== 'loading'
)

function typeLabel(type: string): string {
  const map: Record<string, string> = {
    textbook: '教材',
    mock_exam: '模考',
    user_query: '用户查询',
  }
  return map[type] || type
}

const handleCancel = () => {
  if (props.activeWord) {
    wordsStore.removeWord(props.activeWord.id)
  }
}

const handleRetry = () => {
  if (props.activeWord) {
    wordsStore.retryWord(props.activeWord.id)
  }
}

const handleUpgrade = () => {
  if (props.activeWord) {
    wordsStore.upgradeToDeep(props.activeWord.id)
  }
}
</script>

<template>
  <aside id="query-panel"
    class="flex flex-col bg-white dark:bg-[#1a1b23] border-l border-gray-200 dark:border-gray-700 shadow-2xl"
    :class="[
      'lg:fixed lg:right-0 lg:top-12 lg:bottom-0 lg:w-108 lg:transition-transform lg:duration-300 lg:z-30',
      show ? 'lg:translate-x-0' : 'lg:translate-x-full',
      'max-lg:fixed max-lg:inset-x-0 max-lg:bottom-0 max-lg:max-h-[80vh] max-lg:rounded-t-2xl max-lg:shadow-[0_-8px_30px_rgba(0,0,0,0.15)] max-lg:z-30',
      show ? 'max-lg:translate-y-0' : 'max-lg:translate-y-full',
      'transition-transform duration-300',
    ]">
    <div class="flex items-center justify-between px-5 py-4 border-b border-gray-100 dark:border-gray-800">
      <div>
        <h2 class="text-lg font-bold">「{{ activeWord?.word }}」</h2>
        <span class="text-xs text-gray-400 dark:text-gray-500">{{ activeWord?.mode === 'deep' ? '深度查询' : '快速确认' }}</span>
      </div>
      <button @click="emit('close')" class="text-gray-400 dark:text-gray-500 hover:text-gray-800 dark:hover:text-white text-lg"  data-umami-event="home-panel-close">✕</button>
    </div>

    <div v-if="activeWord" class="px-5 py-3 text-sm flex items-center gap-2 border-b border-gray-50 dark:border-gray-800">
      <span v-if="activeWord.status === 'loading'" class="relative flex h-2.5 w-2.5">
        <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75"></span>
        <span class="relative inline-flex rounded-full h-2.5 w-2.5 bg-blue-500"></span>
      </span>
      <span v-else-if="activeWord.status === 'done'" class="h-2.5 w-2.5 rounded-full bg-green-400"></span>
      <span v-else-if="activeWord.status === 'error'" class="h-2.5 w-2.5 rounded-full bg-red-400"></span>
      <span v-else class="h-2.5 w-2.5 rounded-full bg-gray-400"></span>
      <span :class="{
        'text-blue-600 dark:text-blue-400': activeWord.status === 'loading',
        'text-green-600 dark:text-green-400': activeWord.status === 'done',
        'text-red-600 dark:text-red-400': activeWord.status === 'error',
        'text-gray-600 dark:text-gray-300': activeWord.status === 'pending'
      }">{{ activeWord.statusText }}</span>
      <button v-if="activeWord.status === 'pending' || activeWord.status === 'loading'"
        @click="handleCancel"
        class="ml-auto px-2 py-1 text-xs text-red-600 dark:text-red-400 border border-red-200 dark:border-red-800 rounded hover:bg-red-50 dark:hover:bg-red-950/30 transition-colors" data-umami-event="home-panel-cancel">
        取消
      </button>
      <div v-else-if="activeWord.status === 'error'" class="ml-auto flex items-center gap-2">
        <button @click="handleRetry"
          class="px-2 py-1 text-xs text-blue-600 dark:text-blue-400 border border-blue-200 dark:border-blue-800 rounded hover:bg-blue-50 dark:hover:bg-blue-950/30 transition-colors" data-umami-event="home-panel-retry">
          重试
        </button>
        <button @click="handleCancel"
          class="px-2 py-1 text-xs text-gray-600 dark:text-gray-300 border border-gray-200 dark:border-gray-700 rounded hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors" data-umami-event="home-panel-clear">
          清除
        </button>
      </div>
      <div v-else-if="activeWord.status === 'done'" class="ml-auto flex items-center gap-2">
        <button v-if="activeWord.mode === 'quick'"
          @click="handleUpgrade"
          class="px-2 py-1 text-xs text-purple-600 dark:text-purple-400 border border-purple-200 dark:border-purple-800 rounded hover:bg-purple-50 dark:hover:bg-purple-950/30 transition-colors" data-umami-event="home-panel-upgrade">
          升级深度思考
        </button>
        <button @click="handleCancel"
          class="px-2 py-1 text-xs text-gray-600 dark:text-gray-300 border border-gray-200 dark:border-gray-700 rounded hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors" data-umami-event="home-panel-clear">
          清除
        </button>
      </div>
    </div>

    <div class="flex-1 overflow-y-auto p-5 space-y-4">
      <div v-if="hasAiContent"
        class="rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 shadow-sm">
        <div class="px-4 py-2 border-b border-gray-100 dark:border-gray-800">
          <span class="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide">AI 解答</span>
        </div>
        <div class="px-4 py-3 space-y-2">
          <div v-if="activeWord?.quickAnswer" class="flex items-start gap-2">
            <span class="text-base shrink-0 mt-0.5">⚡</span>
            <p class="text-base font-bold leading-relaxed">{{ activeWord.quickAnswer }}</p>
          </div>
          <div v-if="deepMeaning" class="flex items-start gap-2">
            <span class="text-base shrink-0 mt-0.5">🧠</span>
            <p class="text-base font-bold leading-relaxed">{{ deepMeaning }}</p>
          </div>
        </div>
      </div>

      <DeepAnalysisSplit v-if="activeWord?.deepThink" :deep-think="activeWord.deepThink" />

      <div v-if="activeWord?.dictResult"
        class="rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 shadow-sm">
        <div class="px-4 py-2 border-b border-gray-100 dark:border-gray-800">
          <span class="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide">📖 汉典释义</span>
        </div>
        <div class="px-4 py-3">
          <DictDisplay
            :dict-result="activeWord.dictResult"
            :ai-answer="aiAnswerForDict"
            :context="activeWord.context"
            :query-word="activeWord.word" />
        </div>
      </div>
      <div v-if="activeWord?.corpusEntries?.length"
        class="rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 shadow-sm">
        <div class="px-4 py-2 border-b border-gray-100 dark:border-gray-800">
          <span class="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide">📚 语料库参考</span>
        </div>
        <div class="px-4 py-3 space-y-3">
          <div v-for="entry in activeWord.corpusEntries" :key="entry.id"
            class="pb-3 border-b border-gray-100 dark:border-gray-800 last:border-b-0 last:pb-0">
            <div class="flex items-center gap-1.5 mb-1">
              <span class="text-xs px-1.5 py-0.5 rounded bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-300 font-medium">{{ typeLabel(entry.type) }}</span>
              <span class="text-sm text-gray-600 dark:text-gray-300">「{{ entry.context }}」</span>
            </div>
            <p class="text-sm leading-relaxed text-gray-700 dark:text-gray-200">{{ entry.answer }}</p>
          </div>
        </div>
      </div>

      <div v-if="showEmpty"
        class="text-center text-gray-400 dark:text-gray-500 text-sm mt-20">
        选中词语后点击查询
      </div>
    </div>

    <div v-if="activeWord && activeWord.status === 'done' && loggedIn"
      class="border-t border-gray-100 dark:border-gray-800 p-4 space-y-2">
      <textarea :value="savedAnswer"
        @input="emit('update:savedAnswer', ($event.target as HTMLTextAreaElement).value)"
        class="w-full p-2 border border-gray-200 dark:border-gray-700 rounded-lg text-sm resize-none focus:outline-none focus:ring-1 focus:ring-blue-300 dark:bg-gray-900 dark:text-gray-100"
        rows="2" placeholder="可修改 AI 回答后保存，或输入你自己的答案..."></textarea>
      <div class="flex items-center gap-2">
        <button @click="emit('save')"
          class="flex-1 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-500 transition-colors">
          保存到历史
        </button>
        <span v-if="saveSuccess" class="text-green-600 dark:text-green-400 text-sm">已保存</span>
      </div>
    </div>

    <div v-if="show"
      class="max-lg:flex lg:hidden items-center justify-center py-2 border-t border-gray-100 dark:border-gray-800 cursor-pointer"
      @click="emit('close')" data-umami-event="home-panel-close">
      <div class="w-10 h-1 bg-gray-300 dark:bg-gray-600 rounded-full"></div>
    </div>
  </aside>
</template>
