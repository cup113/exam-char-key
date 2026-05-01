<script setup lang="ts">
defineProps<{
  show: boolean
  x: number
  y: number
}>()

const emit = defineEmits<{
  quick: []
  deep: []
}>()
</script>

<template>
  <Teleport to="body">
    <div v-if="show"
      class="fixed bg-gray-900 text-white px-3 py-2 rounded-lg shadow-2xl flex gap-2 text-sm z-50 animate-in fade-in select-none"
      :style="{ top: y + 'px', left: x + 'px', transform: 'translateX(-50%)' }">
      <button @click.stop="emit('quick')" @touchend.prevent="emit('quick')" class="hover:text-blue-300 transition-colors" data-umami-event="home-tooltip-quick">⚡ 快速确认</button>
      <div class="w-px bg-gray-600"></div>
      <button @click.stop="emit('deep')" @touchend.prevent="emit('deep')" class="hover:text-purple-300 transition-colors" data-umami-event="home-tooltip-deep">🧠 深度查询</button>
    </div>
  </Teleport>
</template>
