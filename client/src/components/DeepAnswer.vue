<script setup lang="ts">
import { useQueryStore } from '@/stores/query';
import AiIcon from './icons/AiIcon.vue';
import BrainIcon from './icons/BrainIcon.vue';
import { CollapsibleRoot, CollapsibleTrigger, CollapsibleContent } from 'reka-ui';
const queryStore = useQueryStore();
</script>

<template>
    <div class="relative w-xs lg:w-md min-h-24 px-4 py-4 shadow-lg flex flex-col gap-4">
        <div class="absolute flex items-center bg-primary-500 left-0 top-2 p-1 rounded-lg">
            <ai-icon></ai-icon>
            <brain-icon></brain-icon>
        </div>
        <div class="text-center text-xl font-bold text-warning-700 mx-auto px-4 rounded-xl min-h-6">
            <p v-for="answer in queryStore.aiThoughtStructured.answers" :key="answer">
                <span>{{ answer }}</span>
            </p>
        </div>
        <div class="indent-4">
            {{ queryStore.aiThoughtStructured.explain }}
        </div>
        <collapsible-root>
            <collapsible-trigger class="w-full p-1 bg-secondary-200 rounded-lg">
                深度思考内容 ({{ queryStore.aiThoughtResponse.length }} 字符)
            </collapsible-trigger>
            <collapsible-content class="py-2">
                <p class="text-secondary-400 text-sm indent-4" v-show="queryStore.aiThoughtStructured.think">
                    {{ queryStore.aiThoughtStructured.think }}</p>
            </collapsible-content>
        </collapsible-root>
    </div>
</template>
