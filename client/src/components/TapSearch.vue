<script lang="ts" setup>
import { useQueryStore } from '@/stores/query';
import { useUserStore } from '@/stores/user';
import { reactive, watch, computed, ref } from 'vue';
import { PopoverArrow, PopoverContent, PopoverClose, PopoverPortal, PopoverRoot, PopoverTrigger } from 'reka-ui';
import SearchIcon from './icons/SearchIcon.vue';
import AdoptIcon from './icons/AdoptIcon.vue';

const PUNCTUATIONS = {
    NONSTOP: ['，', '；', '：', '“', "”", "‘", "’"],
    STOP: ['。', '！', '？'],
    getFull() {
        return this.NONSTOP.join('') + this.STOP.join('');
    }
};
const PUNCTUATIONS_REGEX = new RegExp(`[${PUNCTUATIONS.getFull()}]`, 'g');

const userStore = useUserStore();

interface Paragraph {
    leadingPunctuation: string;
    chunks: Chunk[];
}

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
const paragraphs = reactive(new Array<Paragraph>());
const chars = reactive(new Array<Character>);
const aiAdoptSuggestions = computed(() => {
    return [queryStore.aiInstantResponse, ...queryStore.aiThoughtStructured.answers].map(answer => answer.replace("。", ""));
});
const adoptText = ref("");

watch(() => queryStore.activeText, () => {
    const fullText = queryStore.activeText.trim();
    const defaultSelected = fullText.length < 25;
    paragraphs.splice(0, paragraphs.length);
    fullText.split("\n").forEach(paragraphText => {
        const result = new Array<Chunk>();
        const text = paragraphText.trim();
        if (!text) {
            return; // Skip empty paragraphs
        }
        let leadingPunctuation = "";
        for (let i = 0; i < text.length;) {
            if (i === 0) {
                while (text[i].match(PUNCTUATIONS_REGEX)) {
                    leadingPunctuation += text[i];
                    i++;
                }
            }
            const subsequentText = text.slice(i);
            let nextPunctuationRelative = subsequentText.search(PUNCTUATIONS_REGEX);
            if (nextPunctuationRelative === -1) {
                result.push({ text: text.slice(i), start: i, nextPunctuation: '', selected: defaultSelected });
                break;
            }
            const textEndRelative = nextPunctuationRelative;
            while (nextPunctuationRelative < subsequentText.length - 1 && subsequentText[nextPunctuationRelative + 1].match(PUNCTUATIONS_REGEX)) {
                nextPunctuationRelative++;
            }
            const endRelative = nextPunctuationRelative + 1;
            const chunkText = subsequentText.slice(0, textEndRelative);
            const nextPunctuation = subsequentText.slice(textEndRelative, endRelative);
            result.push({ text: chunkText, start: i, nextPunctuation, selected: defaultSelected });
            i += endRelative;
        }
        if (result.length > 0) {
            paragraphs.push({ leadingPunctuation, chunks: result });
        }
    });
}, { immediate: true });

watch(paragraphs, () => {
    const ELLIPSE = "……";

    queryStore.querySentence = "";
    queryStore.queryIndex.clear();

    const addPart = (part: string) => queryStore.querySentence += part;

    paragraphs.forEach(paragraph => {
        let lastChunk: Chunk | null = null;
        paragraph.chunks.forEach((chunk, chunkIndex) => {
            if (chunk.selected) {
                if (chunkIndex === 0) {
                    addPart(paragraph.leadingPunctuation ?? "");
                } else if (lastChunk) {
                    addPart(lastChunk.nextPunctuation);
                } else if (queryStore.querySentence.length !== 0) {
                    addPart(ELLIPSE); // previous paragraphs selected, but this chunk is not the first in this paragraph.
                }
                addPart(chunk.text);
                lastChunk = chunk;
                if (chunkIndex === paragraph.chunks.length - 1) {
                    addPart(chunk.nextPunctuation);
                }
            } else {
                if (lastChunk) {
                    if (PUNCTUATIONS.STOP.includes(lastChunk.nextPunctuation)) {
                        addPart(lastChunk.nextPunctuation);
                    }
                    addPart(ELLIPSE);
                    lastChunk = null;
                }
            }
        });
    });

    if (queryStore.querySentence.endsWith(ELLIPSE)) {
        queryStore.querySentence = queryStore.querySentence.slice(0, queryStore.querySentence.length - ELLIPSE.length);
    }
}, { immediate: true, deep: true });

watch(() => queryStore.querySentence, () => {
    chars.splice(0, chars.length);
    queryStore.querySentence.split('').forEach(char => {
        chars.push({ char, selected: false });
    })
    queryStore.queryIndex.clear();
}, { immediate: true });

watch(chars, () => {
    queryStore.queryIndex.clear();

    chars.forEach((char, index) => {
        if (char.selected) {
            queryStore.queryIndex.add(index);
        }
    })
}, { immediate: true, deep: true });

function selectChunk(indexPara: number, indexChunk: number) {
    const paragraph = paragraphs[indexPara];
    const chunk = paragraph.chunks[indexChunk];
    chunk.selected = !chunk.selected;
}

function clearChunkSelection() {
    paragraphs.forEach(paragraph => paragraph.chunks.forEach(chunk => chunk.selected = false));
    queryStore.querySentence = "";
}

function selectChar(index: number) {
    if (chars[index].selected) {
        chars[index].selected = false;
    } else {
        chars[index].selected = true;
    }
}

function fillAdoptedAnswer(answer: string) {
    adoptText.value += answer;
}

function adoptAnswer() {
    queryStore.adopt_answer(adoptText.value);
    adoptText.value = "";
}

function toggleDeepThinking() {
    userStore.deepThinking = !userStore.deepThinking;
}

</script>

<template>
    <div class="max-w-2xs sm:max-w-md lg:max-w-3xl flex flex-col gap-4">
        <section class="flex flex-col items-center">
            <h2 class="text-xl font-bold mb-2">原文内容</h2>
            <div v-for="(para, paraIndex) in paragraphs" :key="paraIndex">
                <div class="inline-block font-mono mr-2">({{ paraIndex + 1 }})</div>
                <div class="inline-block">{{ para.leadingPunctuation }}</div>
                <div v-for="(chunk, index) in para.chunks" :key="index" class="inline-block">
                    <span class="cursor-pointer"
                        :class="{ 'bg-warning-300': chunk.selected, 'hover:bg-primary-500': !chunk.selected }"
                        @click="selectChunk(paraIndex, index)">{{ chunk.text }}</span>
                    <span>{{ chunk.nextPunctuation }}</span>
                </div>
            </div>
        </section>
        <section>
            <h2 class="text-xl font-bold mb-2 flex items-center justify-center gap-2">
                <span>已选中</span>
                <button @click="clearChunkSelection"
                    class="rounded-lg text-base font-normal cursor-pointer flex items-center gap-2 bg-warning-600 text-white px-2 hover:bg-warning-700">
                    <span>清空</span>
                </button>
            </h2>
            <div class="min-h-10 text-center text-secondary-500" v-if="chars.length === 0">暂无文本，请<strong>点击原文内容</strong>选择上下文吧！</div>
            <div class="min-h-10" v-else>
                <div class="flex flex-wrap gap-1 text-lg justify-center">
                    <div v-for="(char, index) in chars" :key="index" class="p-1 rounded-md cursor-pointer"
                        :class="{ 'bg-warning-300': char.selected, 'hover:bg-primary-500': !char.selected }"
                        @click="selectChar(index)">
                        {{ char.char }}
                    </div>
                </div>
            </div>
        </section>
        <section class="flex justify-center gap-4" v-show="queryStore.lastQuery.word || queryStore.queryWord">
            <button @click="queryStore.query(true)" :disabled="!queryStore.queryWord"
                class="rounded-lg text-lg cursor-pointer flex items-center gap-2 bg-primary-600 text-white px-4 py-2 hover:bg-primary-700 disabled:cursor-not-allowed">
                <search-icon></search-icon>
                <span>简单搜索</span>
            </button>
            <button @click="queryStore.query(false)" :disabled="!queryStore.queryWord"
                class="rounded-lg text-lg cursor-pointer flex items-center gap-2 bg-warning-600 text-white px-4 py-2 hover:bg-warning-700 disabled:cursor-not-allowed">
                <search-icon></search-icon>
                <span>深度搜索</span>
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
        <section v-show="chars.length > 0 && !queryStore.queryWord && !queryStore.lastQuery.word" class="text-center text-secondary-500">
            请<strong>点击“已选中”区域你想要查询的汉字</strong>，激活查询功能！
        </section>
    </div>
</template>