<script lang="ts" setup>
import { useQueryStore } from '@/stores/query';
import { stress_keyword } from '@/stores/utils';
import { computed, ref, watch } from 'vue';
import { FreqResult } from '@/stores/types';

import FrequencyIcon from './icons/FrequencyIcon.vue';
import MyPagination from './MyPagination.vue';

const queryStore = useQueryStore();

const stat = computed(() => queryStore.freqInfo.stat)

const currentPage = ref(1);
const itemsPerPage = 15;

// 处理页码变更
function handlePageChanged(page: number) {
    currentPage.value = page;
    queryStore.queryFrequency(queryStore.lastQuery.word, currentPage.value);
}

// 当查询改变时重置到第一页
watch(() => queryStore.freqInfo.stat.query, () => {
    currentPage.value = 1;
});

// 定义 badge 的显示文本和样式
const getTypeBadgeInfo = (type: string) => {
    switch (type) {
        case 'textbook':
            return { text: '课本原文', class: 'bg-primary-500 text-primary-800' };
        case 'dataset':
            return { text: '数据集', class: 'bg-secondary-100 text-secondary-800' };
        case 'query':
            return { text: '用户查询', class: 'bg-warning-200 text-warning-800' };
        default:
            throw new Error(`Unknown note type from FreqInfo: ${type}`)
    }
};
</script>

<template>
    <div class="ec-standard-card">
        <div>
            <FrequencyIcon />
            <strong class="ml-2">词频分析</strong>
        </div>
        <div>
            <div>
                <p>
                    <span>出现次数</span>
                    <span>：教科书</span> <strong>{{ stat.freqTextbook }}</strong>
                    <span>，古文语料库</span> {{ stat.freqDataset }}
                    <span>，用户查询</span> {{ stat.freqQuery }}
                </p>
            </div>
            <div>
                <div v-for="note, index in queryStore.freqInfo.notes" :key="note.query">
                    <div
                        class="flex flex-col text-center items-center bg-primary-100 shadow-md py-2 my-2 px-2 relative mt-7">
                        <span
                            class="absolute text-xs font-semibold px-2 py-1 rounded-t-lg whitespace-nowrap left-0 -top-5 right-0"
                            :class="getTypeBadgeInfo(note.type).class">
                            {{ (currentPage - 1) * itemsPerPage + index + 1 }}. {{ getTypeBadgeInfo(note.type).text }}
                        </span>
                        <div class="text-center px-2">
                            <span v-html="stress_keyword(note.context.trim(), note.query)" class="text-secondary-700">
                            </span>
                        </div>
                        <div class="flex">
                            <p class="w-full text-primary-700 font-bold">{{ note.answer.split('\n')[0] }}</p>
                        </div>
                    </div>
                </div>
                <MyPagination :current-page="currentPage" :total-pages="queryStore.freqInfo.total_pages"
                    @page-changed="handlePageChanged" />
            </div>
        </div>
    </div>
</template>