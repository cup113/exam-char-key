<script lang="ts" setup>
import { computed } from 'vue';

interface Props {
    currentPage: number;
    totalPages: number;
}

const props = defineProps<Props>();
const emit = defineEmits<{
    (e: 'page-changed', page: number): void;
}>();

const canGoPrev = computed(() => props.currentPage > 1);
const canGoNext = computed(() => props.currentPage < props.totalPages);

function goToPage(page: number) {
    if (page >= 1 && page <= props.totalPages && page !== props.currentPage) {
        emit('page-changed', page);
    }
}
</script>

<template>
    <div class="flex justify-between items-center mt-4" v-show="totalPages > 1">
        <button @click="goToPage(currentPage - 1)" :disabled="!canGoPrev"
            class="px-3 py-1 rounded bg-gray-200 disabled:opacity-50">
            上一页
        </button>

        <span class="text-sm">
            第 {{ currentPage }} 页，共 {{ totalPages }} 页
        </span>

        <button @click="goToPage(currentPage + 1)" :disabled="!canGoNext"
            class="px-3 py-1 rounded bg-gray-200 disabled:opacity-50">
            下一页
        </button>
    </div>
</template>