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

const props = defineProps<{
  dictResult: string | null | undefined
}>()

const parsed = computed<ParsedDict | null>(() => {
  if (!props.dictResult) return null
  try {
    return JSON.parse(props.dictResult) as ParsedDict
  } catch {
    return null
  }
})
</script>

<template>
  <template v-if="parsed">
    <div v-if="parsed.basic_explanation?.length">
      <h4 class="text-xs font-semibold text-emerald-800 mb-2">基本解释</h4>
      <div v-for="(item, i) in parsed.basic_explanation" :key="'b'+i"
        class="mb-2 last:mb-0 flex gap-2">
        <span
          class="shrink-0 mt-0.5 inline-flex items-center justify-center w-5 h-5 rounded-full bg-emerald-100 text-emerald-700 text-xs font-bold">
          {{ i + 1 }}
        </span>
        <div class="min-w-0">
          <p class="text-sm">{{ item.brief }}</p>
          <p v-if="item.examples?.length" class="text-xs text-emerald-600 mt-0.5">
            {{ item.examples.join('、') }}
          </p>
        </div>
      </div>
    </div>
    <div v-if="parsed.detailed_explanation?.length" class="mt-3">
      <h4 class="text-xs font-semibold text-emerald-800 mb-2">详细解释</h4>
      <div v-for="(item, i) in parsed.detailed_explanation" :key="'d'+i"
        class="mb-2 last:mb-0 flex gap-2">
        <span
          class="shrink-0 mt-0.5 inline-flex items-center justify-center w-5 h-5 rounded-full bg-emerald-100 text-emerald-700 text-xs font-bold">
          {{ i + 1 }}
        </span>
        <div class="min-w-0">
          <p class="text-sm">
            {{ item.brief }}
            <span v-if="item.english" class="text-xs text-gray-500 ml-1">[{{ item.english }}]</span>
          </p>
          <p v-if="item.examples?.length" class="text-xs text-emerald-600 mt-0.5">
            {{ item.examples.join('、') }}
          </p>
        </div>
      </div>
    </div>
  </template>
  <p v-else-if="dictResult" class="text-sm leading-relaxed whitespace-pre-wrap">{{ dictResult }}</p>
</template>
