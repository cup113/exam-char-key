<script setup lang="ts">
import { useQueryStore } from '@/stores/query';
import DictionaryIcon from './icons/DictionaryIcon.vue';
const queryStore = useQueryStore();
</script>

<template>
    <div class="relative w-xs lg:w-md min-h-24 px-4 py-4 shadow-lg flex flex-col gap-2">
        <div class="absolute flex items-center font-bold text-sm -top-2 -left-0 p-1 rounded-lg bg-primary-500">
            <dictionary-icon></dictionary-icon>
            汉典
        </div>
        <h3 class="text-lg font-bold text-center">基本解释</h3>
        <ol class="indent-4">
            <li v-for="item, i in queryStore.zdicResponse.basic_explanations" :key="i">
                {{ i + 1 }}. {{ item }}
            </li>
        </ol>
        <h3 v-if="queryStore.zdicResponse.detailed_explanations.length" class="text-lg font-bold text-center">详细解释
        </h3>
        <ol class="detail flex flex-col gap-1 indent-4">
            <li v-for="item in queryStore.zdicResponse.detailed_explanations" v-html="item"></li>
        </ol>
        <h2 v-if="queryStore.zdicResponse.phrase_explanations.length" class="text-lg font-bold text-center">补充解释
        </h2>
        <ol class="flex flex-col gap-1 indent-4">
            <li v-for="item in queryStore.zdicResponse.phrase_explanations" v-html="item"></li>
        </ol>
    </div>
</template>

<style lang="css">
@reference "tailwindcss";

.detail li:nth-child(1) {
    @apply hidden;
}

.detail .cino {
    @apply font-bold text-sm;
}

.detail .encs {
    @apply text-amber-700 text-xs font-serif;
}

.detail .diczx1,
.detail .diczx2,
.detail .smcs {
    @apply text-stone-700 text-sm;
}
</style>
