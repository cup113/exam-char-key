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
        </div>
        <p class="text-center text-xl font-bold mx-auto px-4 rounded-xl text-warning-700"
            v-show="queryStore.aiInstantResponse">
            {{ queryStore.aiInstantResponse }}
        </p>
    </div>
</template>
