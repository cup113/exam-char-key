<script setup lang="ts">
import { useWordsStore, type TrackedWord } from '@/stores/words'
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

const getTrackedWordClass = (w: TrackedWord) => {
  const isActive = w.id === wordsStore.activeWordId
  const base = 'tracked-word inline cursor-pointer transition-all duration-200 rounded'
  if (isActive) {
    return `${base} border-b-2 border-blue-600 bg-blue-200 ring-2 ring-blue-300`
  }
  if (w.status === 'loading') {
    return `${base} border-b-2 border-dashed border-yellow-400 bg-yellow-50 hover:bg-yellow-100`
  }
  if (w.status === 'done' && (w.quickAnswer || w.dictResult || w.deepThink)) {
    return `${base} border-b-2 border-blue-500 bg-blue-50 hover:bg-blue-100`
  }
  if (w.status === 'error') {
    return `${base} border-b-2 border-dashed border-red-400 bg-red-50 hover:bg-red-50`
  }
  return `${base} border-b-2 border-dashed border-blue-300 hover:bg-blue-50`
}
</script>

<template>
  <div class="flex items-center justify-between mb-4">
    <h1 class="text-3xl font-bold">论语·为政</h1>
    <div class="flex gap-2 text-sm">
      <button v-if="!editing && wordsStore.trackedWords.length > 0" @click="wordsStore.clearAll"
        class="text-gray-400 hover:text-red-500">清空追踪</button>
      <button v-if="!editing" @click="emit('startEditing')"
        class="px-3 py-1 border border-gray-300 rounded hover:bg-gray-100">编辑文本</button>
    </div>
  </div>

  <div v-if="editing" class="space-y-3">
    <textarea :value="editText"
      @input="emit('update:editText', ($event.target as HTMLTextAreaElement).value)"
      class="w-full min-h-48 p-4 border border-gray-200 rounded-lg text-lg leading-loose resize-y focus:outline-none focus:ring-2 focus:ring-blue-300 font-sans"></textarea>
    <div class="flex gap-2 justify-end">
      <button @click="emit('cancelEditing')"
        class="px-4 py-1.5 border border-gray-300 rounded text-sm hover:bg-gray-100">取消</button>
      <button @click="emit('saveEditing')"
        class="px-4 py-1.5 bg-blue-600 text-white rounded text-sm hover:bg-blue-500">保存</button>
    </div>
  </div>

  <div v-else
    class="min-h-48 p-4 border border-gray-200 rounded-lg text-lg leading-loose whitespace-pre-wrap select-text">
    <template v-if="textSegments.length === 0">
      {{ editableText }}
    </template>
    <template v-else>
      <span v-for="(seg, i) in textSegments" :key="i">
        <span v-if="seg.type === 'text'">{{ seg.content }}</span>
        <span v-else :class="getTrackedWordClass(seg.word)" @click.stop="emit('wordClick', seg.word.id)">
          {{ seg.word.word }}
          <span v-if="seg.word.quickAnswer.length > 0" class="text-sm text-yellow-800">({{ seg.word.quickAnswer }})</span>
          <span v-if="seg.word.status === 'loading'" class="ml-0.5">
            <span class="animate-spin inline-block w-3 h-3 border border-yellow-400 border-t-transparent rounded-full align-middle"></span>
          </span>
        </span>
      </span>
    </template>
  </div>

  <p class="text-sm text-gray-400 mt-4">💡 提示：用鼠标选中任意词语，即可触发查询。</p>
</template>

<style scoped>
.tracked-word.loading {
  border-bottom: 2px dashed #f59e0b;
  background-color: #fef3c7;
}
.tracked-word.done {
  border-bottom: 2px solid #3b82f6;
  background-color: #dbeafe;
}
.tracked-word.error {
  border-bottom: 2px dashed #ef4444;
  background-color: #fee2e2;
}
</style>
