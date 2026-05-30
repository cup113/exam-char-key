<script setup lang="ts">
import { computed } from 'vue'
import DictDisplay from '@/components/DictDisplay.vue'
import DeepAnalysisSplit from '@/components/DeepAnalysisSplit.vue'
import type { CorpusEntry } from '@/types'
import { typeLabel, deepMeaning, aiAnswerForDict as buildAiAnswer } from '@/utils/wordAnalysis'

interface WordLike {
  word: string
  quickAnswer: string
  dictResult: string
  deepThink: string
  corpusEntries: CorpusEntry[]
  mode: string
  quickStatus?: string
  dictStatus?: string
  deepStatus?: string
  corpusStatus?: string
}

const props = withDefaults(defineProps<{
  word: WordLike | null
  readonly?: boolean
}>(), {
  readonly: false,
})

function aiAnswerForDict(word: WordLike): string[] | string {
  return buildAiAnswer(word.quickAnswer, word.deepThink)
}

const allFailed = computed(() => {
  if (!props.word) return false
  return (
    props.word.quickStatus === 'error' &&
    props.word.corpusStatus === 'error' &&
    props.word.dictStatus === 'error' &&
    props.word.deepStatus === 'error'
  )
})

const idle = computed(() => {
  if (!props.word) return true
  return (
    props.word.quickStatus === 'idle' &&
    props.word.corpusStatus === 'idle' &&
    props.word.dictStatus === 'idle' &&
    props.word.deepStatus === 'idle'
  )
})
</script>

<template>
  <div v-if="allFailed"
    class="text-center text-gray-400 dark:text-gray-500 text-sm mt-20">
    全部查询失败，请重试
  </div>
  <div v-else-if="word" class="space-y-4">
    <div v-if="word.quickAnswer || word.deepThink"
      class="rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 shadow-sm">
      <div class="px-4 py-2 border-b border-gray-100 dark:border-gray-800">
        <span class="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide">AI 解答</span>
      </div>
      <div class="px-4 py-3 space-y-2">
        <div v-if="!readonly && word.quickStatus === 'loading' && !word.quickAnswer"
          class="animate-pulse h-6 bg-gray-200 dark:bg-gray-700 rounded"></div>
        <div v-if="!readonly && word.quickStatus === 'error' && !word.quickAnswer"
          class="text-sm text-red-500">快速查询失败</div>
        <div v-if="word.quickAnswer" class="flex items-start gap-2">
          <span class="text-base shrink-0 mt-0.5">⚡</span>
          <p class="text-base font-bold leading-relaxed">{{ word.quickAnswer }}</p>
        </div>
        <div v-if="!readonly && word.deepStatus === 'loading' && !deepMeaning(word.deepThink)"
          class="animate-pulse h-6 bg-gray-200 dark:bg-gray-700 rounded"></div>
        <div v-if="!readonly && word.deepStatus === 'error' && !deepMeaning(word.deepThink)"
          class="text-sm text-red-500">深度分析失败</div>
        <div v-if="deepMeaning(word.deepThink)" class="flex items-start gap-2">
          <span class="text-base shrink-0 mt-0.5">🧠</span>
          <p class="text-base font-bold leading-relaxed">{{ deepMeaning(word.deepThink) }}</p>
        </div>
      </div>
    </div>

    <DeepAnalysisSplit v-if="word.deepThink" :deep-think="word.deepThink" />
    <div v-if="!readonly && word.deepStatus === 'loading' && !word.deepThink"
      class="rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 shadow-sm p-4">
      <div class="animate-pulse space-y-2">
        <div class="h-4 bg-gray-200 dark:bg-gray-700 rounded w-3/4"></div>
        <div class="h-4 bg-gray-200 dark:bg-gray-700 rounded"></div>
        <div class="h-4 bg-gray-200 dark:bg-gray-700 rounded w-5/6"></div>
      </div>
    </div>
    <div v-if="!readonly && word.deepStatus === 'error'"
      class="rounded-xl border border-red-200 dark:border-red-800 bg-white dark:bg-gray-900 shadow-sm p-4 text-sm text-red-500">
      深度分析失败
    </div>

    <div v-if="word.dictResult || (!readonly && word.dictStatus === 'loading')"
      class="rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 shadow-sm">
      <div class="px-4 py-2 border-b border-gray-100 dark:border-gray-800">
        <span class="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide">📖 汉典释义</span>
      </div>
      <div class="px-4 py-3">
        <div v-if="!readonly && word.dictStatus === 'loading' && !word.dictResult"
          class="animate-pulse h-20 bg-gray-200 dark:bg-gray-700 rounded"></div>
        <DictDisplay v-if="word.dictResult" :dict-result="word.dictResult" :ai-answer="aiAnswerForDict(word)" />
      </div>
    </div>
    <div v-if="!readonly && word.dictStatus === 'error' && !word.dictResult"
      class="rounded-xl border border-red-200 dark:border-red-800 bg-white dark:bg-gray-900 shadow-sm p-4 text-sm text-red-500">
      汉典查询失败
    </div>

    <div v-if="word.corpusEntries.length > 0 || (!readonly && word.corpusStatus === 'loading')"
      class="rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 shadow-sm">
      <div class="px-4 py-2 border-b border-gray-100 dark:border-gray-800">
        <span class="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide">📚 语料库参考</span>
      </div>
      <div class="px-4 py-3 space-y-3">
        <div v-if="!readonly && word.corpusStatus === 'loading' && word.corpusEntries.length === 0"
          class="animate-pulse h-16 bg-gray-200 dark:bg-gray-700 rounded"></div>
        <template v-for="entry in word.corpusEntries" :key="entry.id">
          <div class="pb-3 border-b border-gray-100 dark:border-gray-800 last:border-b-0 last:pb-0">
            <div class="flex items-center gap-1.5 mb-1">
              <span class="text-xs px-1.5 py-0.5 rounded bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-300 font-medium">{{ typeLabel(entry.type) }}</span>
              <span class="text-sm text-gray-600 dark:text-gray-300">「{{ entry.context }}」</span>
            </div>
            <p class="text-sm leading-relaxed text-gray-700 dark:text-gray-200">{{ entry.answer }}</p>
          </div>
        </template>
      </div>
    </div>
    <div v-if="!readonly && word.corpusStatus === 'error' && word.corpusEntries.length === 0"
      class="rounded-xl border border-red-200 dark:border-red-800 bg-white dark:bg-gray-900 shadow-sm p-4 text-sm text-red-500">
      语料库查询失败
    </div>
  </div>
  <div v-else-if="idle"
    class="text-center text-gray-400 dark:text-gray-500 text-sm mt-20">
    选中词语后点击查询
  </div>
</template>
