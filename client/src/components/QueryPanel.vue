<script setup lang="ts">
import DictDisplay from '@/components/DictDisplay.vue'
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
</script>

<template>
  <aside id="query-panel"
    class="flex flex-col bg-white border-l border-gray-200 shadow-2xl"
    :class="[
      'lg:fixed lg:right-0 lg:top-12 lg:bottom-0 lg:w-108 lg:transition-transform lg:duration-300 lg:z-30',
      show ? 'lg:translate-x-0' : 'lg:translate-x-full',
      'max-lg:fixed max-lg:inset-x-0 max-lg:bottom-0 max-lg:max-h-[80vh] max-lg:rounded-t-2xl max-lg:shadow-[0_-8px_30px_rgba(0,0,0,0.15)] max-lg:z-30',
      show ? 'max-lg:translate-y-0' : 'max-lg:translate-y-full',
      'transition-transform duration-300',
    ]">
    <div class="flex items-center justify-between px-5 py-4 border-b border-gray-100">
      <div>
        <h2 class="text-lg font-bold">「{{ activeWord?.word }}」</h2>
        <span class="text-xs text-gray-400">{{ activeWord?.mode === 'deep' ? '深度查询' : '快速确认' }}</span>
      </div>
      <button @click="emit('close')" class="text-gray-400 hover:text-gray-800 text-lg">✕</button>
    </div>

    <div v-if="activeWord" class="px-5 py-3 text-sm flex items-center gap-2 border-b border-gray-50">
      <span v-if="activeWord.status === 'loading'" class="relative flex h-2.5 w-2.5">
        <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75"></span>
        <span class="relative inline-flex rounded-full h-2.5 w-2.5 bg-blue-500"></span>
      </span>
      <span v-else-if="activeWord.status === 'done'" class="h-2.5 w-2.5 rounded-full bg-green-400"></span>
      <span v-else-if="activeWord.status === 'error'" class="h-2.5 w-2.5 rounded-full bg-red-400"></span>
      <span v-else class="h-2.5 w-2.5 rounded-full bg-gray-400"></span>
      <span :class="{
        'text-blue-600': activeWord.status === 'loading',
        'text-green-600': activeWord.status === 'done',
        'text-red-600': activeWord.status === 'error',
        'text-gray-600': activeWord.status === 'pending'
      }">{{ activeWord.statusText }}</span>
      <button v-if="activeWord.status === 'loading' || activeWord.status === 'pending'"
        @click="handleCancel"
        class="ml-auto px-2 py-1 text-xs text-red-600 border border-red-200 rounded hover:bg-red-50 transition-colors">
        取消
      </button>
      <button v-if="activeWord.status === 'error'"
        @click="handleRetry"
        class="ml-auto px-2 py-1 text-xs text-blue-600 border border-blue-200 rounded hover:bg-blue-50 transition-colors">
        重试
      </button>
    </div>

    <div class="flex-1 overflow-y-auto p-5 space-y-4">
      <div v-if="activeWord?.quickAnswer" class="p-4 bg-blue-50 rounded-xl border border-blue-100">
        <h3 class="text-xs font-bold text-blue-700 mb-2 uppercase tracking-wide">⚡ 快速回答</h3>
        <p class="text-sm leading-relaxed whitespace-pre-wrap">{{ activeWord.quickAnswer }}</p>
      </div>

      <div v-if="activeWord?.corpusEntries?.length" class="p-4 bg-amber-50 rounded-xl border border-amber-100">
        <h3 class="text-xs font-bold text-amber-700 mb-2 uppercase tracking-wide">📚 语料库参考</h3>
        <div v-for="entry in activeWord.corpusEntries" :key="entry.id"
          class="mb-3 pb-3 border-b border-amber-100 last:border-b-0 last:mb-0 last:pb-0">
          <p class="text-xs text-amber-600 mb-1">
            <span class="font-semibold">语境：</span>「{{ entry.context }}」
          </p>
          <p class="text-sm leading-relaxed">{{ entry.answer }}</p>
        </div>
      </div>

      <div v-if="activeWord?.dictResult" class="p-4 bg-emerald-50 rounded-xl border border-emerald-100">
        <h3 class="text-xs font-bold text-emerald-700 mb-2 uppercase tracking-wide">📖 汉典释义</h3>
        <DictDisplay :dict-result="activeWord.dictResult" />
      </div>

      <div v-if="activeWord?.deepThink" class="p-4 bg-purple-50 rounded-xl border border-purple-100">
        <h3 class="text-xs font-bold text-purple-700 mb-2 uppercase tracking-wide">🧠 深度分析</h3>
        <p class="text-sm leading-relaxed whitespace-pre-wrap">{{ activeWord.deepThink }}</p>
      </div>

      <div v-if="!activeWord?.quickAnswer && !activeWord?.dictResult && !activeWord?.deepThink && activeWord?.status !== 'loading'"
        class="text-center text-gray-400 text-sm mt-20">
        选中词语后点击查询
      </div>
    </div>

    <div v-if="activeWord && activeWord.status === 'done' && loggedIn"
      class="border-t border-gray-100 p-4 space-y-2">
      <textarea :value="savedAnswer"
        @input="emit('update:savedAnswer', ($event.target as HTMLTextAreaElement).value)"
        class="w-full p-2 border border-gray-200 rounded-lg text-sm resize-none focus:outline-none focus:ring-1 focus:ring-blue-300"
        rows="2" placeholder="可修改 AI 回答后保存，或输入你自己的答案..."></textarea>
      <div class="flex items-center gap-2">
        <button @click="emit('save')"
          class="flex-1 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-500 transition-colors">
          保存到历史
        </button>
        <span v-if="saveSuccess" class="text-green-600 text-sm">已保存</span>
      </div>
    </div>

    <div v-if="show"
      class="max-lg:flex lg:hidden items-center justify-center py-2 border-t border-gray-100 cursor-pointer"
      @click="emit('close')">
      <div class="w-10 h-1 bg-gray-300 rounded-full"></div>
    </div>
  </aside>
</template>
