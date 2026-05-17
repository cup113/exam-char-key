<script setup lang="ts">
import { ref } from 'vue'

export interface ConfirmButton {
  label: string
  value: string
  variant?: 'primary' | 'danger' | 'default'
}

export interface ConfirmState {
  show: boolean
  title: string
  message: string
  buttons: ConfirmButton[]
  resolve: (value: string) => void
}

const props = defineProps<{
  state: ConfirmState
}>()

function handleClick(value: string) {
  props.state.resolve(value)
  props.state.show = false
}

function btnClass(variant?: string): string {
  switch (variant) {
    case 'primary': return 'bg-blue-600 text-white hover:bg-blue-500'
    case 'danger': return 'bg-red-600 text-white hover:bg-red-500'
    default: return 'border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800'
  }
}
</script>

<template>
  <Teleport to="body">
    <div v-if="state.show" class="fixed inset-0 z-50 flex items-center justify-center bg-black/30" @click.self="handleClick('cancel')">
      <div class="bg-white dark:bg-gray-900 rounded-xl p-6 w-[90vw] max-w-96 space-y-4 shadow-2xl">
        <h3 class="text-lg font-bold">{{ state.title }}</h3>
        <p class="text-sm text-gray-600 dark:text-gray-300 leading-relaxed">{{ state.message }}</p>
        <div class="flex justify-end gap-2">
          <button v-for="btn in state.buttons" :key="btn.value"
            @click="handleClick(btn.value)"
            :class="['px-4 py-1.5 rounded text-sm transition-colors', btnClass(btn.variant)]">
            {{ btn.label }}
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>
