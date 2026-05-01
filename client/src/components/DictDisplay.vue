<script setup lang="ts">
import { computed } from 'vue'

interface DictEntry {
  brief: string
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

function scoreBg(score: number): string {
  if (score >= 0.35) return 'bg-amber-200'
  if (score >= 0.15) return 'bg-amber-100'
  if (score > 0) return 'bg-amber-50'
  return ''
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
  const fw = props.queryWord || ''
  return entries.map(e => ({
    score: Math.max(...answers.map(ans => charJaccard(e.brief, ans, fw))),
    exampleScores: (e.examples || []).map(ex => charJaccard(ex, props.context || '', fw + "，。、：（）")),
  }))
}

const basicScores = computed(() => computeScores(parsed.value?.basic_explanation))
const detailedScores = computed(() => computeScores(parsed.value?.detailed_explanation))
</script>

<template>
  <template v-if="parsed">
    <div v-if="parsed.basic_explanation?.length">
      <h4 class="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">基本解释</h4>
      <div v-for="(item, i) in parsed.basic_explanation" :key="'b'+i"
        class="mb-2 last:mb-0 flex gap-2 px-2 py-1.5 -mx-2 rounded-lg transition-colors"
        :class="scoreBg(basicScores[i]?.score || 0)">
        <span
          class="shrink-0 mt-0.5 inline-flex items-center justify-center w-5 h-5 rounded-full bg-gray-200 text-gray-600 text-xs font-bold">
          {{ i + 1 }}
        </span>
        <div class="min-w-0">
          <p class="text-sm">{{ item.brief }}</p>
          <p v-if="item.examples?.length" class="text-xs text-gray-500 mt-0.5 space-x-1">
            <span v-for="(ex, ei) in item.examples" :key="ei" class="inline-block"
              :class="(detailedScores[i]?.exampleScores?.[ei] || 0) > 0 ? 'bg-amber-100 mr-0.5 rounded' : ''">
              ({{ ei + 1 }}) {{ ex }}
            </span>
          </p>
        </div>
      </div>
    </div>
    <div v-if="parsed.detailed_explanation?.length" class="mt-3">
      <h4 class="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">详细解释</h4>
      <div v-for="(item, i) in parsed.detailed_explanation" :key="'d'+i"
        class="mb-2 last:mb-0 flex gap-2 px-2 py-1.5 -mx-2 rounded-lg transition-colors"
        :class="scoreBg(detailedScores[i]?.score || 0)">
        <span
          class="shrink-0 mt-0.5 inline-flex items-center justify-center w-5 h-5 rounded-full bg-gray-200 text-gray-600 text-xs font-bold">
          {{ i + 1 }}
        </span>
        <div class="min-w-0">
          <p class="text-sm">
            {{ item.brief }}
            <span v-if="item.english" class="text-xs text-gray-400 ml-1">[{{ item.english }}]</span>
          </p>
          <p v-if="item.examples?.length" class="text-xs text-gray-500 mt-0.5">
            <span v-for="(ex, ei) in item.examples" :key="ei" class="inline-block"
              :class="(detailedScores[i]?.exampleScores?.[ei] || 0) > 0 ? 'bg-amber-100 mr-0.5 rounded' : ''">
              ({{ ei + 1 }}) {{ ex }}
            </span>
          </p>
        </div>
      </div>
    </div>
  </template>
  <p v-else-if="dictResult" class="text-sm leading-relaxed whitespace-pre-wrap">{{ dictResult }}</p>
</template>
