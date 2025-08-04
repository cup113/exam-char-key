<script lang="ts" setup>
import { ref } from 'vue';
import { useQueryStore } from '@/stores/query';

const queryStore = useQueryStore();
const showSelectionWarning = ref(false);

function checkSelectionWarning() {
    if (queryStore.chars.length === 0) {
        showSelectionWarning.value = false;
        return;
    }

    const selectedCount = queryStore.chars.filter(char => char.selected).length;
    if (selectedCount >= 5) {
        showSelectionWarning.value = true;
        return;
    }

    let firstSelectedIndex = -1;
    let lastSelectedIndex = -1;
    let selectedCharsCount = 0;

    queryStore.chars.forEach((char, index) => {
        if (char.selected) {
            if (firstSelectedIndex === -1) {
                firstSelectedIndex = index;
            }
            lastSelectedIndex = index;
            selectedCharsCount++;
        }
    });

    if (selectedCharsCount > 1 && (lastSelectedIndex - firstSelectedIndex + 1) > selectedCharsCount) {
        showSelectionWarning.value = true;
        return;
    }

    showSelectionWarning.value = false;
}

function toggleCharSelection(index: number) {
    queryStore.chars[index].selected = !queryStore.chars[index].selected;
    queryStore.queryIndex.clear();
    queryStore.chars.forEach((char, idx) => {
        if (char.selected) {
            queryStore.queryIndex.add(idx);
        }
    });
    checkSelectionWarning();
}
</script>

<template>
    <div class="min-h-10" v-if="queryStore.chars.length > 0">
        <div class="flex flex-wrap gap-1 text-lg justify-center">
            <div v-for="(char, index) in queryStore.chars" :key="index" class="p-1 rounded-md cursor-pointer"
                :class="{ 'bg-warning-300': char.selected, 'hover:bg-primary-500': !char.selected }"
                @click="toggleCharSelection(index)">
                {{ char.char }}
            </div>
        </div>
        <div v-if="showSelectionWarning" class="mt-2 p-2 bg-yellow-100 border border-yellow-300 rounded text-yellow-800 text-sm">
            <p>提示：本产品更适合一次查询一个汉字或词语。建议分次查询。</p>
            <p>在深度思考模式下，系统会自动提供整句翻译和上下文分析。</p>
        </div>
    </div>
    <div class="min-h-10 text-center text-secondary-500" v-else>
        暂无文本，请<strong>点击原文内容</strong>选择上下文吧！
    </div>
</template>
