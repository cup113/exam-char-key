<script setup lang="ts">
import { useQueryStore } from '@/stores/query';
import AiIcon from './icons/AiIcon.vue';
import FlashIcon from './icons/FlashIcon.vue';
const queryStore = useQueryStore();
</script>

<template>
    <div class="ec-standard-card">
        <div>
            <ai-icon></ai-icon>
            <flash-icon></flash-icon>
            <span class="ml-1 text-secondary-400 text-sm">快速回答，仅供参考</span>
        </div>
        <p class="text-center text-xl font-bold mx-auto px-4 rounded-xl text-warning-700"
            v-show="queryStore.aiInstantResponse">
            {{ queryStore.aiInstantResponse }}
        </p>
    </div>
</template>
