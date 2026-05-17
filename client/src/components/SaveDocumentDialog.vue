<script setup lang="ts">
import { ref, computed } from 'vue'

const props = defineProps<{
  defaultTitle: string
  savedResult?: { id: number; title: string; public_uuid?: string | null } | null
}>()

const emit = defineEmits<{
  save: [payload: { title: string; isPublic: boolean }]
  cancel: []
  dismiss: []
}>()

const title = ref(props.defaultTitle)
const isPublic = ref(false)
const copied = ref(false)

const shareUrl = computed(() => {
  if (!props.savedResult?.public_uuid) return ''
  return `${window.location.origin}/shared/${props.savedResult.public_uuid}`
})

function copyLink() {
  if (!shareUrl.value) return
  navigator.clipboard.writeText(shareUrl.value).then(() => {
    copied.value = true
    setTimeout(() => { copied.value = false }, 2000)
  })
}

function selectInput(e: FocusEvent) {
  const input = e.target as HTMLInputElement
  input.select()
}
</script>

<template>
  <Teleport to="body">
    <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/30" @click.self="emit('cancel')">
      <div class="bg-white dark:bg-gray-900 rounded-xl p-6 w-[90vw] max-w-96 space-y-4 shadow-2xl">
        <h3 class="text-lg font-bold">保存文档</h3>

        <div v-if="!savedResult">
          <label class="block text-sm text-gray-500 dark:text-gray-400 mb-1">标题</label>
          <input v-model="title"
            class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-300 dark:bg-gray-800 dark:text-gray-100">
        </div>

        <label v-if="!savedResult" class="flex items-center gap-2 text-sm">
          <input type="checkbox" v-model="isPublic"
            class="rounded border-gray-300 dark:border-gray-600">
          <span class="dark:text-gray-200">公开分享（生成链接）</span>
        </label>

        <div v-if="savedResult" class="text-sm space-y-2">
          <p class="text-green-600 dark:text-green-400 font-medium">✅ 文档已保存</p>
          <div v-if="shareUrl" class="flex items-center gap-2">
            <input :value="shareUrl"
              class="flex-1 px-2 py-1 text-xs border border-gray-300 dark:border-gray-600 rounded bg-gray-50 dark:bg-gray-800 dark:text-gray-200 select-all"
              readonly @focus="selectInput">
            <button @click="copyLink"
              class="shrink-0 px-2 py-1 text-xs bg-blue-600 text-white rounded hover:bg-blue-500">{{ copied ? '已复制' : '复制' }}</button>
          </div>
        </div>

        <div v-if="!savedResult" class="flex justify-end gap-2">
          <button @click="emit('cancel')"
            class="px-4 py-1.5 border border-gray-300 dark:border-gray-600 rounded text-sm hover:bg-gray-100 dark:hover:bg-gray-800 dark:text-gray-300">取消</button>
          <button @click="emit('save', { title: title.trim() || props.defaultTitle, isPublic })"
            class="px-4 py-1.5 bg-blue-600 text-white rounded text-sm hover:bg-blue-500">保存</button>
        </div>
        <div v-else class="flex justify-end">
          <button @click="emit('dismiss')"
            class="px-4 py-1.5 border border-gray-300 dark:border-gray-600 rounded text-sm hover:bg-gray-100 dark:hover:bg-gray-800 dark:text-gray-300">关闭</button>
        </div>
      </div>
    </div>
  </Teleport>
</template>
