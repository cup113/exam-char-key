<script setup lang="ts">
import { useQueryStore } from '@/stores/query';
const queryStore = useQueryStore();
</script>

<template>
    <div class="w-96 min-h-24 px-4 py-2 shadow-lg flex flex-col gap-2">
        <h2 class="text-2xl font-bold text-center">汉典基本解释</h2>
        <ol class="indent-4">
            <li v-for="item, i in queryStore.zdicResponse.basic_explanations" :key="i">
                {{ i + 1 }}. {{ item }}
            </li>
        </ol>
        <h2 v-if="queryStore.zdicResponse.detailed_explanations.length" class="text-2xl font-bold text-center">汉典详细解释
        </h2>
        <ol class="detail flex flex-col gap-1 indent-4">
            <li v-for="item in queryStore.zdicResponse.detailed_explanations" v-html="item"></li>
        </ol>
        <h2 v-if="queryStore.zdicResponse.phrase_explanations.length" class="text-2xl font-bold text-center">汉典补充解释
        <ol class="flex flex-col gap-1 indent-4">
            <li v-for="item in queryStore.zdicResponse.phrase_explanations" v-html="item"></li>
        </ol>
        </h2>
    </div>
</template>

<style>
.detail li:nth-child(1) {
    display: none;
}

.detail .cino {
    color: green;
    font-weight: bolder;
    font-size: 0.875rem;
}

.detail .encs {
    color: green;
    font-size: 0.75rem;
    font-family: Georgia, 'Times New Roman', Times, serif;
}

.detail .diczx1,
.detail .diczx2,
.detail .smcs {
    color: rgb(87, 87, 87);
    font-size: 0.875rem;
}
</style>
