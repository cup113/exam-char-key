<script setup lang="ts">
import { useQueryStore } from '@/stores/query';
const queryStore = useQueryStore();
</script>

<template>
    <div class="w-96 min-h-24 px-4 py-2 shadow-lg flex flex-col gap-2">
        <h2 class="text-2xl font-bold text-center">AI 快速回答</h2>
        <p class="text-center text-xl font-bold bg-green-200 mx-auto px-4 rounded-xl"
            v-show="queryStore.instantStructured.answer">
            {{ queryStore.instantStructured.answer }}
        </p>
        <p class="text-gray-500 text-sm indent-4" v-show="queryStore.instantStructured.think">{{
            queryStore.instantStructured.think }}</p>
        <p class="indent-4" v-show="queryStore.instantStructured.explain">
            {{ queryStore.instantStructured.explain }}
        </p>
    </div>
</template>
