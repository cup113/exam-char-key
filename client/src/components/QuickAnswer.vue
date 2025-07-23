<script setup lang="ts">
import { useQueryStore } from '@/stores/query';
import AiIcon from './icons/AiIcon.vue';
import FlashIcon from './icons/FlashIcon.vue';
const queryStore = useQueryStore();
</script>

<template>
    <div class="relative w-xs lg:w-md min-h-12 px-4 py-2 mt-10 flex flex-col gap-2 bg-primary-200 rounded-b-lg">
        <div class="flex items-center absolute p-1 left-0 right-0 -top-10 bg-primary-500 rounded-t-lg">
            <ai-icon></ai-icon>
            <flash-icon></flash-icon>
        </div>
        <p class="text-center text-xl font-bold mx-auto px-4 rounded-xl text-warning-700"
            v-show="queryStore.aiInstantResponse">
            {{ queryStore.aiInstantResponse }}
        </p>
    </div>
</template>
