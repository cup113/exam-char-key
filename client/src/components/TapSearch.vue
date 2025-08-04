<script lang="ts" setup>
import { useQueryStore } from '@/stores/query';
import { computed, ref } from 'vue';
import { PopoverArrow, PopoverContent, PopoverClose, PopoverPortal, PopoverRoot, PopoverTrigger } from 'reka-ui';
import SearchIcon from './icons/SearchIcon.vue';
import AdoptIcon from './icons/AdoptIcon.vue';
import ParagraphDisplay from './ParagraphDisplay.vue';
import CharacterSelector from './CharacterSelector.vue';

const queryStore = useQueryStore();
const adoptText = ref("");

const aiAdoptSuggestions = computed(() => {
    return [queryStore.aiInstantResponse, ...queryStore.aiThoughtStructured.answers].map(answer => answer.replace("。", ""));
});

function clearChunkSelection() {
    queryStore.clearChunkSelection();
}

function fillAdoptedAnswer(answer: string) {
    adoptText.value += answer;
}

function adoptAnswer() {
    queryStore.adopt_answer(adoptText.value);
    adoptText.value = "";
}
</script>

<template>
    <div class="max-w-2xs sm:max-w-md lg:max-w-3xl flex flex-col gap-4">
        <section class="flex flex-col" :class="{ 'items-center': queryStore.paragraphs.length === 1 }">
            <h2 class="text-xl font-bold mb-2 w-full text-center">原文内容</h2>
            <ParagraphDisplay />
        </section>
        <section>
            <h2 class="text-xl font-bold mb-2 flex items-center justify-center gap-2">
                <span>已选中</span>
                <button @click="clearChunkSelection"
                    class="rounded-lg text-base font-normal cursor-pointer flex items-center gap-2 bg-warning-600 text-white px-2 hover:bg-warning-700">
                    <span>清空</span>
                </button>
            </h2>
            <CharacterSelector ref="charSelector" />
        </section>
        <section class="flex justify-center gap-4" v-show="queryStore.lastQuery.word || queryStore.queryWord">
            <button @click="queryStore.query()" :disabled="!queryStore.queryWord"
                class="rounded-lg text-lg cursor-pointer flex items-center gap-2 bg-warning-600 text-white px-4 py-2 hover:bg-warning-700 disabled:cursor-not-allowed">
                <search-icon></search-icon>
                <span>查询释义</span>
            </button>
            <popover-root>
                <popover-trigger as-child>
                    <button
                        class="rounded-lg text-lg flex items-center gap-2 bg-primary-600  text-white px-4 py-2 hover:bg-primary-700"
                        :class="queryStore.currentRecorded ? 'cursor-not-allowed' : 'cursor-pointer'"
                        :disabled="queryStore.currentRecorded"><adopt-icon></adopt-icon><span>保存记录</span></button>
                </popover-trigger>
                <popover-portal>
                    <popover-content side="top" class="bg-white shadow-sm w-2xs px-2 py-2">
                        <div class="flex flex-col gap-2">
                            <label class="w-full flex px-2 gap-4 items-center">
                                <strong class="w-12 text-center">{{ queryStore.lastQuery.word }}</strong>
                                <input type="text" class="min-w-20 flex-grow border rounded-md text-center p-1"
                                    v-model="adoptText">
                                <popover-close as-child>
                                    <button
                                        class="w-16 text-center p-1 rounded-lg bg-primary-600 text-white hover:bg-primary-700"
                                        @click="adoptAnswer">采纳</button>
                                </popover-close>
                            </label>
                            <div class="grid grid-cols-2 justify-around">
                                <button v-for="(suggestion, index) in aiAdoptSuggestions" :key="index"
                                    class="bg-primary-200 hover:bg-primary-300 p-1 border border-primary-500 cursor-pointer"
                                    @click="fillAdoptedAnswer(suggestion)">
                                    {{ suggestion }}</button>
                            </div>
                        </div>
                        <popover-arrow></popover-arrow>
                    </popover-content>
                </popover-portal>
            </popover-root>
        </section>
        <section v-show="queryStore.querySentence.length > 0 && !queryStore.queryWord && !queryStore.lastQuery.word" class="text-center text-secondary-500">
            请<strong>点击"已选中"区域你想要查询的汉字</strong>，激活查询功能！
        </section>
    </div>
</template>
