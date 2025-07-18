<script lang="ts" setup>
import { useQueryStore } from '@/stores/query';
import { reactive, watch, computed, ref } from 'vue';
import { PopoverArrow, PopoverContent, PopoverClose, PopoverPortal, PopoverRoot, PopoverTrigger } from 'reka-ui';
import SearchIcon from './icons/SearchIcon.vue';
import AdoptIcon from './icons/AdoptIcon.vue';

const PUNCTUATIONS = ['，', '。', '；', '：', '！', '？', '“', '”', '‘', '’', '\n'];
const PUNCTUATIONS_REGEX = new RegExp(`[${PUNCTUATIONS.join('')}]`, 'g');

interface Chunk {
    text: string;
    start: number;
    nextPunctuation: string;
    selected: boolean;
}

interface Character {
    char: string;
    selected: boolean;
}

const queryStore = useQueryStore();
const chunks = reactive(new Array<Chunk>());
const chars = reactive(new Array<Character>);
const aiAdoptSuggestions = computed(() => {
    return [...queryStore.aiThoughtStructured.answers, queryStore.aiInstantResponse];
});
const adoptText = ref("");

watch(() => queryStore.activeText, () => {
    const result = new Array<Chunk>();
    const text = queryStore.activeText.trim();
    const defaultSelected = text.length <= 25; // If the text is short, the user probably wants to select the whole text.
    for (let i = 0; i < text.length;) {
        const subsequentText = text.slice(i);
        let nextPunctuationIndex = subsequentText.search(PUNCTUATIONS_REGEX);
        const textEnd = nextPunctuationIndex;
        while (nextPunctuationIndex < subsequentText.length - 1 && subsequentText[nextPunctuationIndex + 1].match(PUNCTUATIONS_REGEX)) {
            nextPunctuationIndex++;
        }
        if (nextPunctuationIndex === -1) {
            result.push({ text: text.slice(i), start: i, nextPunctuation: '', selected: defaultSelected });
            break;
        }
        const end = i + nextPunctuationIndex + 1;
        const chunkText = subsequentText.slice(0, textEnd);
        const nextPunctuation = subsequentText[nextPunctuationIndex];
        result.push({ text: chunkText, start: i, nextPunctuation, selected: defaultSelected });
        i = end;
    }
    chunks.splice(0, chunks.length, ...result);
}, { immediate: true });

watch(() => queryStore.querySentence, () => {
    chars.splice(0, chars.length);
    queryStore.querySentence.split('').forEach(char => {
        chars.push({ char, selected: false });
    })
    queryStore.queryIndex.clear();
}, { immediate: true });

function selectChunk(index: number) {
    chunks[index].selected = !chunks[index].selected;
    queryStore.querySentence = "";
    let lastIndex = chunks.length;
    for (let i = 0; i < chunks.length; i++) {
        if (chunks[i].selected) {
            if (lastIndex < i - 1) {
                queryStore.querySentence += "……";
            } else if (lastIndex === i - 1) {
                queryStore.querySentence += chunks[lastIndex].nextPunctuation;
            }
            queryStore.querySentence += chunks[i].text;
            lastIndex = i;
            if (i === chunks.length - 1) {
                queryStore.querySentence += chunks[i].nextPunctuation;
            }
        }
    }
}

function clearChunkSelection() {
    chunks.forEach(chunk => chunk.selected = false);
    queryStore.querySentence = "";
}

function selectChar(index: number) {
    if (chars[index].selected) {
        chars[index].selected = false;
        queryStore.queryIndex.delete(index);
    } else {
        chars[index].selected = true;
        queryStore.queryIndex.add(index);
    }
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
        <section>
            <h2 class="text-xl font-bold mb-2 text-center">原文内容</h2>
            <div v-for="(chunk, index) in chunks" :key="index" class="inline-flex">
                <span class="cursor-pointer"
                    :class="{ 'bg-accent-300': chunk.selected, 'hover:bg-primary-300': !chunk.selected }"
                    @click="selectChunk(index)">{{ chunk.text }}</span>
                <span>{{ chunk.nextPunctuation }}</span>
                <br v-if="chunk.nextPunctuation.includes('\n')">
            </div>
        </section>
        <section>
            <h2 class="text-xl font-bold mb-2 text-center">上下文</h2>
            <div v-if="chunks.length === 0">暂无文本</div>
            <div v-else>
                <div class="flex flex-wrap gap-1 text-lg justify-center">
                    <div v-for="(char, index) in chars" :key="index" class="p-1 rounded-md cursor-pointer"
                        :class="{ 'bg-accent-300': char.selected, 'hover:bg-primary-300': !char.selected }"
                        @click="selectChar(index)">
                        {{ char.char }}
                    </div>
                </div>
            </div>
        </section>
        <section class="flex justify-center gap-4">
            <button @click="queryStore.query"
                class="rounded-lg text-lg cursor-pointer flex items-center gap-2 bg-accent-600 text-white px-4 py-2 hover:bg-accent-700">
                <search-icon></search-icon>
                <span>搜索</span>
            </button>
            <popover-root>
                <popover-trigger as-child>
                    <button
                        class="rounded-lg text-lg flex items-center gap-2 bg-primary-600  text-white px-4 py-2 hover:bg-primary-700"
                        :class="queryStore.currentRecorded ? 'cursor-not-allowed' : 'cursor-pointer'"
                        :disabled="queryStore.currentRecorded"><adopt-icon></adopt-icon><span>采纳</span></button>
                </popover-trigger>
                <popover-portal>
                    <popover-content side="top" class="bg-white shadow-sm w-2xs px-2 py-2">
                        <div class="flex flex-col gap-2">
                            <label class="w-full flex px-2 gap-4 items-center">
                                <strong>{{ queryStore.queryWord }}</strong>
                                <input type="text" class="min-w-20 flex-grow border rounded-md text-center p-1" v-model="adoptText">
                                <popover-close as-child>
                                    <button
                                        class="w-16 text-center p-1 rounded-lg bg-primary-600 text-white hover:bg-primary-700" @click="adoptAnswer">采纳</button>
                                </popover-close>
                            </label>
                            <div class="flex flex-wrap gap-2 justify-around">
                                <button v-for="(suggestion, index) in aiAdoptSuggestions" :key="index"
                                    class="bg-primary-200 hover:bg-primary-300 rounded px-2 py-1 m-1 cursor-pointer"
                                    @click="fillAdoptedAnswer(suggestion)">
                                    {{ suggestion }}</button>
                            </div>
                        </div>
                        <popover-arrow></popover-arrow>
                    </popover-content>
                </popover-portal>
            </popover-root>
        </section>
    </div>
</template>
