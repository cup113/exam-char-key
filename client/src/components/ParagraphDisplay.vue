<script lang="ts" setup>
import { useQueryStore } from '@/stores/query';

const queryStore = useQueryStore();

function selectChunk(indexPara: number, indexChunk: number) {
    queryStore.selectChunk(indexPara, indexChunk);
}

function selectWholeParagraph(indexPara: number) {
    queryStore.selectWholeParagraph(indexPara);
}
</script>

<template>
    <div class="inline-block">
        <div v-for="(para, paraIndex) in queryStore.paragraphs" :key="paraIndex">
            <div 
                class="inline-block font-mono mr-2 text-base font-bold cursor-pointer w-8 text-center rounded hover:bg-blue-200 transition-colors"
                v-if="queryStore.paragraphs.length >= 2" 
                @click="selectWholeParagraph(paraIndex)"
                title="点击全选/取消全选该段落">
                ({{ paraIndex + 1 }})
            </div>
            <div class="inline-block">{{ para.leadingPunctuation }}</div>
            <div v-for="(chunk, index) in para.chunks" :key="index" class="inline-block">
                <span class="cursor-pointer"
                    :class="{ 'bg-warning-300': chunk.selected, 'hover:bg-primary-500': !chunk.selected }"
                    @click="selectChunk(paraIndex, index)">{{ chunk.text }}</span>
                <span>{{ chunk.nextPunctuation }}</span>
            </div>
        </div>
    </div>
</template>