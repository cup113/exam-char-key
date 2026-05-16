<script setup lang="ts">
import { computed, ref } from 'vue'
import { useWordsStore } from '@/stores/words'
import type { TrackedWord } from '@/types'
import { useAuthStore } from '@/stores/auth'
import type { TextSegment } from '@/types'

const props = defineProps<{
  editableText: string
  editing: boolean
  editText: string
  textSegments: TextSegment[]
}>()

const emit = defineEmits<{
  startEditing: []
  saveEditing: []
  cancelEditing: []
  'update:editText': [value: string]
  wordClick: [id: string]
}>()

const wordsStore = useWordsStore()
const auth = useAuthStore()

const searchQuery = ref('')

const searchSites = [
  { key: 'ctext-pre-qin', label: 'ctext 秦汉',
    url: (q: string) => `https://ctext.org/pre-qin-and-han?searchu=${encodeURIComponent(q)}` },
  { key: 'ctext-post-han', label: 'ctext 汉后',
    url: (q: string) => `https://ctext.org/post-han?searchu=${encodeURIComponent(q)}` },
  { key: 'shidianguji', label: '识典古籍',
    url: (q: string) => `https://www.shidianguji.com/search/${encodeURIComponent(q)}` },
  { key: 'guwendao', label: '古文岛',
    url: (q: string) => `https://www.guwendao.net/search.aspx?value=${encodeURIComponent(q)}` },
]

function searchOn(key: string) {
  const q = searchQuery.value.trim()
  if (!q) return
  const site = searchSites.find(s => s.key === key)
  if (site) window.open(site.url(q), '_blank', 'noopener')
}

const segmentOffsets = computed(() => {
  const offsets: number[] = []
  let cursor = 0
  for (const seg of props.textSegments) {
    if (seg.type === 'text') {
      offsets.push(cursor)
      cursor += seg.content.length
    } else {
      offsets.push(seg.word.offset)
      cursor = seg.word.offset + seg.word.word.length
    }
  }
  return offsets
})

const getTrackedWordClass = (w: TrackedWord) => {
  const isActive = w.id === wordsStore.activeWordId
  const base = 'tracked-word inline cursor-pointer transition-all duration-200 rounded'
  if (isActive) {
    return `${base} border-b-2 border-blue-600 dark:border-blue-400 bg-blue-200 dark:bg-blue-800/50 ring-2 ring-blue-300 dark:ring-blue-600`
  }
  if (w.status === 'loading') {
    return `${base} border-b-2 border-dashed border-yellow-400 bg-yellow-50 dark:bg-yellow-950/30 hover:bg-yellow-100 dark:hover:bg-yellow-900/30`
  }
  if (w.status === 'done' && (w.quickAnswer || w.dictResult || w.deepThink)) {
    return `${base} border-b-2 border-blue-500 bg-blue-50 dark:bg-blue-950/30 hover:bg-blue-100 dark:hover:bg-blue-900/30`
  }
  if (w.status === 'error') {
    return `${base} border-b-2 border-dashed border-red-400 bg-red-50 dark:bg-red-950/30 hover:bg-red-50 dark:hover:bg-red-900/30`
  }
  return `${base} border-b-2 border-dashed border-blue-300 hover:bg-blue-50 dark:hover:bg-blue-950/20`
}
</script>

<template>
  <div class="flex items-center justify-between mb-4">
    <div class="flex items-center gap-2 min-w-0">
      <h1 class="text-xl sm:text-2xl font-bold shrink-0">划词阅读</h1>
      <span v-if="auth.quota && auth.user.logged_in" title="已用查询次数/每日总配额 · 剩余免费次数"
        class="hidden sm:inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs
               bg-gray-100 dark:bg-gray-800 text-gray-500 dark:text-gray-400 whitespace-nowrap">
        <span>{{ auth.quota.used }}/{{ auth.quota.limit }}</span>
        <span>·</span>
        <span :class="auth.quota.remaining < 5 ? 'text-red-500' : ''">剩{{ auth.quota.remaining }}</span>
      </span>
    </div>
    <div class="flex gap-2 text-sm shrink-0">
      <button v-if="!editing && wordsStore.trackedWords.length > 0" @click="wordsStore.clearAll"
        class="text-gray-400 dark:text-gray-500 hover:text-red-500" data-umami-event="home-text-untrack">清空追踪</button>
      <button v-if="!editing" @click="emit('startEditing')"
        class="px-3 py-1 border border-gray-300 dark:border-gray-600 rounded hover:bg-gray-100 dark:hover:bg-gray-800" data-umami-event="home-text-edit">编辑文本</button>
    </div>
  </div>

  <div v-if="editing" class="space-y-3">
    <textarea :value="editText"
      @input="emit('update:editText', ($event.target as HTMLTextAreaElement).value)"
      class="w-full min-h-48 p-4 border border-gray-200 dark:border-gray-700 rounded-lg text-lg leading-loose resize-y focus:outline-none focus:ring-2 focus:ring-blue-300 dark:bg-gray-900 dark:text-gray-100 font-sans"></textarea>
    <div class="flex gap-2 justify-end">
      <button @click="emit('cancelEditing')"
        class="px-4 py-1.5 border border-gray-300 dark:border-gray-600 rounded text-sm hover:bg-gray-100 dark:hover:bg-gray-800" data-umami-event="home-text-cancel">取消</button>
      <button @click="emit('saveEditing')"
        class="px-4 py-1.5 bg-blue-600 text-white rounded text-sm hover:bg-blue-500" data-umami-event="home-text-save">保存</button>
    </div>
  </div>

  <div v-else
    class="min-h-48 p-4 border border-gray-200 dark:border-gray-700 dark:bg-gray-900 dark:text-gray-100 rounded-lg text-lg leading-loose whitespace-pre-wrap select-text"
    style="-webkit-touch-callout:none; touch-action: manipulation" @contextmenu.prevent>
    <template v-if="textSegments.length === 0">
      <span data-offset="0">{{ editableText }}</span>
    </template>
    <template v-else>
      <span v-for="(seg, i) in textSegments" :key="i">
        <span v-if="seg.type === 'text'" :data-offset="segmentOffsets[i]">{{ seg.content }}</span>
        <span v-else :data-offset="segmentOffsets[i]" :class="getTrackedWordClass(seg.word)" @click.stop="emit('wordClick', seg.word.id)">
          {{ seg.word.word }}
           <span v-if="seg.word.quickAnswer.length > 0" class="text-sm text-yellow-800 dark:text-yellow-300">({{ seg.word.quickAnswer }})</span>
          <span v-if="seg.word.status === 'loading'" class="ml-0.5">
            <span class="animate-spin inline-block w-3 h-3 border border-yellow-400 border-t-transparent rounded-full align-middle"></span>
          </span>
        </span>
      </span>
    </template>
  </div>

  <p class="text-sm text-gray-400 dark:text-gray-500 mt-4">💡 提示：选中任意词语，即可触发查询。</p>

      <p class="text-xs text-gray-400 dark:text-gray-500 mt-4">需要查找其他文章？输入篇名、作者或文章开头几个字搜索全文，复制后粘贴到上方阅读区即可。</p>

  <div class="mt-2 flex flex-wrap items-start gap-2 p-3 border border-gray-200 dark:border-gray-700 rounded-lg bg-gray-50 dark:bg-gray-900/50">
    <div class="flex items-center gap-1.5 w-full sm:w-auto">
      <span class="text-sm text-gray-500 dark:text-gray-400 whitespace-nowrap">📖 搜索</span>
      <input v-model="searchQuery" placeholder="篇名、作者或文章开头…"
        class="flex-1 min-w-0 px-2.5 py-1 border border-gray-300 dark:border-gray-600 rounded text-sm
               focus:outline-none focus:ring-2 focus:ring-blue-300 dark:bg-gray-800 dark:text-gray-100
               placeholder-gray-400 dark:placeholder-gray-500"
        @keyup.enter="searchOn('ctext-pre-qin')">
    </div>
    <div class="flex flex-wrap gap-1.5">
      <button v-for="site in searchSites" :key="site.key" @click="searchOn(site.key)"
        class="px-2.5 py-1 rounded text-xs font-medium border transition-colors whitespace-nowrap
               border-gray-300 dark:border-gray-600
               text-gray-600 dark:text-gray-400
               hover:bg-gray-200 dark:hover:bg-gray-700
               active:bg-gray-300 dark:active:bg-gray-600">
        {{ site.label }}
      </button>
    </div>
  </div>
</template>

<style scoped>
.dark .tracked-word.loading {
  border-bottom-color: #f59e0b;
  background-color: #451a03;
}
.dark .tracked-word.done {
  border-bottom-color: #3b82f6;
  background-color: #172554;
}
.dark .tracked-word.error {
  border-bottom-color: #ef4444;
  background-color: #450a0a;
}
</style>
