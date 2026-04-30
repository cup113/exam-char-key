<script setup lang="ts">
import { computed } from 'vue'
import type { TrackedWord } from '@/stores/words'

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

interface DictEntry {
  brief: string
  english?: string
  examples?: string[]
}

interface ParsedDict {
  basic_explanation?: DictEntry[]
  detailed_explanation?: DictEntry[]
}

const parsedDict = computed<ParsedDict | null>(() => {
  const raw = props.activeWord?.dictResult
  if (!raw) return null
  try {
    return JSON.parse(raw)
  } catch {
    return null
  }
})
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
    </div>

    <div class="flex-1 overflow-y-auto p-5 space-y-4">
      <div v-if="activeWord?.quickAnswer" class="p-4 bg-blue-50 rounded-xl border border-blue-100">
        <h3 class="text-xs font-bold text-blue-700 mb-2 uppercase tracking-wide">⚡ 快速回答</h3>
        <p class="text-sm leading-relaxed whitespace-pre-wrap">{{ activeWord.quickAnswer }}</p>
      </div>

      <div v-if="activeWord?.dictResult" class="p-4 bg-emerald-50 rounded-xl border border-emerald-100">
        <!-- TODO merge with HistoryView -->
        <!-- TODO aesthetic layout -->
        <h3 class="text-xs font-bold text-emerald-700 mb-2 uppercase tracking-wide">📖 汉典释义</h3>
        <template v-if="parsedDict">
          <div v-if="parsedDict.basic_explanation?.length" class="mb-3">
            <h4 class="text-xs font-semibold text-emerald-800 mb-1.5">基本解释</h4>
            <div v-for="(item, i) in parsedDict.basic_explanation" :key="'b'+i" class="mb-1.5 last:mb-0">
              <p class="text-sm">{{ item.brief }}</p>
              <p v-if="item.examples?.length" class="text-xs text-emerald-600 mt-0.5">
                {{ item.examples.join('、') }}
              </p>
            </div>
          </div>
          <div v-if="parsedDict.detailed_explanation?.length">
            <h4 class="text-xs font-semibold text-emerald-800 mb-1.5">详细解释</h4>
            <div v-for="(item, i) in parsedDict.detailed_explanation" :key="'d'+i" class="mb-1.5 last:mb-0">
              <p class="text-sm">
                {{ item.brief }}
                <span v-if="item.english" class="text-xs text-gray-500 ml-1">[{{ item.english }}]</span>
              </p>
              <p v-if="item.examples?.length" class="text-xs text-emerald-600 mt-0.5">
                {{ item.examples.join('、') }}
              </p>
            </div>
          </div>
        </template>
        <p v-else class="text-sm leading-relaxed whitespace-pre-wrap">{{ activeWord.dictResult }}</p>
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
