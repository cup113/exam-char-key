<script setup lang="ts">
import { useQueryStore } from '@/stores/query';
const queryStore = useQueryStore();
</script>

<template>
    <div class="w-xs lg:w-md min-h-24 px-4 py-2 shadow-lg flex flex-col gap-2">
        <h2 class="text-2xl font-bold text-center">AI 快速回答</h2>
        <p class="text-center text-xl font-bold mx-auto px-4 rounded-xl text-warning-700"
            v-show="queryStore.aiInstantResponse">
            {{ queryStore.aiInstantResponse }}
        </p>
    </div>
</template>
