<script setup lang="ts">
import { useQueryStore } from '@/stores/query';
const queryStore = useQueryStore();
</script>

<template>
    <div class="min-h-24 px-4 py-2 shadow-lg flex flex-col gap-2 w-full">
        <h2 class="text-2xl font-bold text-center">AI 深度回答</h2>
        <div class="text-center text-xl font-bold bg-green-200 mx-auto px-4 rounded-xl">
            <p v-for="answer in queryStore.thoughtStructured.answers" :key="answer">
                <span>{{ answer }}</span>
                <button @click="queryStore.adopt_answer(answer)" v-if="!queryStore.currentRecorded"
                    class="bg-green-500 hover:bg-green-600 text-white font-bold py-1 px-2 rounded-xl ml-2 text-base">
                    采用
                </button>
            </p>
        </div>
        <p class="text-gray-500 text-sm indent-4" v-show="queryStore.thoughtStructured.think">{{
            queryStore.thoughtStructured.think }}</p>
        <div class="indent-4">
            {{ queryStore.thoughtStructured.explain }}
        </div>
    </div>
</template>
