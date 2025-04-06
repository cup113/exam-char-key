<script setup lang="ts">
import { useQueryStore } from '@/stores/query';
const queryStore = useQueryStore();
</script>

<template>
    <section class="flex flex-col gap-2">
        <div class="text-center flex justify-center items-center gap-2">
            <input type="text" class="rounded-lg border border-gray-500 text-center p-1 w-96"
                v-model="queryStore.querySentence" placeholder="请输入要翻译词语的上下文">
            <span class="text-sm">已用量：{{ (queryStore.usage / 1e7).toFixed(4) }}</span>
        </div>
        <div class="flex justify-center items-center gap-4">
            <div class="flex">
                <div v-for="word, i in queryStore.querySentence"
                    class="cursor-pointer rounded-md hover:bg-gray-100 px-1 py-0"
                    :class="{ 'bg-green-100': queryStore.queryIndex.has(i), 'hover:bg-green-200': queryStore.queryIndex.has(i) }"
                    @click="queryStore.toggle_index(i)">{{ word }}</div>
            </div>
            <button @click="queryStore.query()"
                class="bg-blue-500 hover:bg-blue-600 active:bg-blue-700 text-white p-1 rounded-lg px-2">搜索</button>
        </div>
    </section>
</template>
