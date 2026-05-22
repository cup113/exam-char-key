<script setup lang="ts">
import { computed } from 'vue'

interface DictEntry {
  brief: string
  pos?: string
  english?: string
  examples?: string[]
}

interface ParsedDict {
  basic_explanation?: DictEntry[]
  detailed_explanation?: DictEntry[]
}

interface EntryScore {
  score: number
  exampleScores: number[]
}

const props = defineProps<{
  dictResult: string | null | undefined
  aiAnswer?: string | string[]
  context?: string
  queryWord?: string
}>()

const parsed = computed<ParsedDict | null>(() => {
  if (!props.dictResult) return null
  try {
    return JSON.parse(props.dictResult) as ParsedDict
  } catch {
    return null
  }
})

function charJaccard(a: string, b: string, filterChars: string = ''): number {
  if (!a || !b) return 0
  const strip = (s: string) => filterChars ? [...s].filter(c => !filterChars.includes(c)).join('') : s
  const setA = new Set(strip(a))
  const setB = new Set(strip(b))
  if (setA.size === 0 && setB.size === 0) return 0
  const intersection = new Set([...setA].filter(c => setB.has(c)))
  const union = new Set([...setA, ...setB])
  return intersection.size / union.size
}

function scoreStyle(score: number): string {
  if (score >= 0.5) return 'font-bold underline decoration-2 underline-offset-2 decoration-blue-400/50'
  if (score >= 0.25) return 'font-semibold'
  if (score > 0.1) return ''
  return 'text-gray-400 dark:text-gray-500'
}

const posColors: Record<string, string> = {
  '名': 'bg-blue-100 dark:bg-blue-900/50 text-blue-700 dark:text-blue-300',
  '动': 'bg-emerald-100 dark:bg-emerald-900/50 text-emerald-700 dark:text-emerald-300',
  '形': 'bg-orange-100 dark:bg-orange-900/50 text-orange-700 dark:text-orange-300',
  '副': 'bg-purple-100 dark:bg-purple-900/50 text-purple-700 dark:text-purple-300',
  '代': 'bg-pink-100 dark:bg-pink-900/50 text-pink-700 dark:text-pink-300',
  '介': 'bg-teal-100 dark:bg-teal-900/50 text-teal-700 dark:text-teal-300',
  '连': 'bg-cyan-100 dark:bg-cyan-900/50 text-cyan-700 dark:text-cyan-300',
  '助': 'bg-slate-100 dark:bg-slate-900/50 text-slate-700 dark:text-slate-300',
  '叹': 'bg-red-100 dark:bg-red-900/50 text-red-700 dark:text-red-300',
  '量': 'bg-yellow-100 dark:bg-yellow-900/50 text-yellow-700 dark:text-yellow-300',
  '数': 'bg-indigo-100 dark:bg-indigo-900/50 text-indigo-700 dark:text-indigo-300',
}

function posClass(pos: string | undefined): string {
  return pos ? (posColors[pos] || 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-300') : ''
}

function badgeClass(score: number): string {
  if (score >= 0.5) return 'bg-blue-500 text-white'
  if (score >= 0.25) return 'bg-blue-200 dark:bg-blue-800 text-blue-700 dark:text-blue-300'
  if (score > 0.1) return 'bg-gray-200 dark:bg-gray-700 text-gray-600 dark:text-gray-300'
  return 'bg-gray-100 dark:bg-gray-800 text-gray-400 dark:text-gray-500'
}

function computeScores(entries: DictEntry[] | undefined): EntryScore[] {
  if (!entries) return []
  let answers: string[]
  if (!props.aiAnswer) {
    answers = ['']
  } else if (Array.isArray(props.aiAnswer)) {
    answers = props.aiAnswer.length > 0 ? props.aiAnswer : ['']
  } else {
    answers = [props.aiAnswer]
  }
  const fw = (props.queryWord || '') + "，。、：（）"
  return entries.map(e => ({
    score: Math.max(...answers.map(ans => charJaccard(e.brief, ans, fw))),
    exampleScores: (e.examples || []).map(ex => charJaccard(ex, props.context || '', fw)),
  }))
}

const sections = computed(() => [
  { key: 'b', entries: parsed.value?.basic_explanation, title: '基本解释', scores: computeScores(parsed.value?.basic_explanation), showEnglish: false },
  { key: 'd', entries: parsed.value?.detailed_explanation, title: '详细解释', scores: computeScores(parsed.value?.detailed_explanation), showEnglish: true },
].filter(s => s.entries?.length))
</script>

<template>
  <template v-if="parsed">
    <template v-for="(sec, si) in sections" :key="sec.key">
      <div v-if="si > 0" class="mt-3"></div>
      <h4 class="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-2">{{ sec.title }}</h4>
      <div v-for="(item, i) in sec.entries" :key="sec.key + i"
        class="mb-2 last:mb-0 flex gap-2 px-2 py-1.5 -mx-2 rounded-lg">
        <span
          class="shrink-0 mt-0.5 inline-flex items-center justify-center w-5 h-5 rounded-full text-xs font-bold transition-colors"
          :class="badgeClass(sec.scores[i]?.score || 0)"
          :title="`与当前词语相关度: ${Math.round((sec.scores[i]?.score || 0) * 100)}%`">
          {{ i + 1 }}
        </span>
        <div class="min-w-0">
          <p class="text-sm" :class="scoreStyle(sec.scores[i]?.score || 0)">
            <span v-if="item.pos" class="pos-tag" :class="posClass(item.pos)">{{ item.pos }}</span>
            {{ item.brief }}
            <span v-if="sec.showEnglish && item.english" class="text-xs text-gray-400 dark:text-gray-500 ml-1">[{{ item.english }}]</span>
          </p>
          <p v-if="item.examples?.length" class="text-xs text-gray-500 dark:text-gray-400 mt-0.5 space-x-1">
            <span v-for="(ex, ei) in item.examples" :key="ei" class="inline-block"
              :class="(sec.scores[i]?.exampleScores?.[ei] || 0) > 0.1 ? 'font-medium' : 'text-gray-400 dark:text-gray-500'">
              ({{ ei + 1 }}) {{ ex }}
            </span>
          </p>
        </div>
      </div>
    </template>
  </template>
  <p v-else-if="dictResult" class="text-sm leading-relaxed whitespace-pre-wrap">{{ dictResult }}</p>
</template>

<style scoped>
.pos-tag {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 1.5rem;
  height: 1.25rem;
  border-radius: 0.25rem;
  font-size: 0.6875rem;
  font-weight: 700;
  line-height: 1;
  margin-right: 0.25rem;
  vertical-align: middle;
}
</style>
