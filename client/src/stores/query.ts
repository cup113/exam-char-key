import { defineStore } from 'pinia';
import { useLocalStorage } from '@vueuse/core';
import { computed, reactive, ref, watch, type Ref } from 'vue';
import { nanoid } from 'nanoid';
import { SearchTarget, type HistoryRecord, type FrontendHandler, FreqResult } from './types';
import { format_front, parse_ai_thought_response } from './utils';
import { useApiStore } from './api';
import { useHistoryStore } from './history';
import { useUserStore } from './user';

const exampleText = "工欲善其事，必先利其器。";

export interface Paragraph {
    leadingPunctuation: string;
    chunks: Chunk[];
}

export interface Chunk {
    text: string;
    start: number;
    nextPunctuation: string;
    selected: boolean;
}

export const useQueryStore = defineStore("query", () => {
    const activeText = useLocalStorage("EC_activeText", exampleText);
    const searchTarget = useLocalStorage<SearchTarget>("EC_searchTarget", SearchTarget.None);
    const querySentence = ref("");
    const queryIndex = ref(new Set<number>());
    const queryWord = computed(() => {
        return Array.from(queryIndex.value).sort((a, b) => a - b).map(i => querySentence.value[i]).join('');
    });
    const paragraphs = reactive(new Array<Paragraph>());
    const chars = ref<Array<{ char: string, selected: boolean }>>([]);

    const PUNCTUATIONS = {
        NONSTOP: ['，', '；', '：', '“', "”", "‘", "’"],
        STOP: ['。', '！', '？'],
        getFull() {
            return this.NONSTOP.join('') + this.STOP.join('');
        }
    };

    const PUNCTUATIONS_REGEX = new RegExp(`[${PUNCTUATIONS.getFull()}]`, 'g');

    const lastQuery = reactive({
        sentence: '',
        index: new Set<number>(),
        word: '',
    });

    const freqInfo = ref<FreqResult>(FreqResult.empty());
    const aiInstantResponse = ref("");
    const aiThoughtResponse = ref("");
    const currentRecorded = ref(true);
    const zdicResponse = ref({ basic_explanations: new Array<string>(), detailed_explanations: new Array<string>(), phrase_explanations: new Array<string>() });

    const requestIds = {
        queryFlash: "",
        queryThinking: "",
        queryFreq: "",
        searchOriginal: "",
    };

    const aiThoughtStructured = computed(() => {
        return parse_ai_thought_response(aiThoughtResponse.value);
    });

    watch(querySentence, () => {
        chars.value = querySentence.value.split('').map(char => ({ char, selected: false }));
    }, { immediate: true });

    watch(activeText, () => {
        updateParagraphs(activeText.value);
    }, { immediate: true });

    watch(() => paragraphs, () => {
        const ELLIPSE = "……";

        querySentence.value = "";
        queryIndex.value.clear();

        const addPart = (part: string) => querySentence.value += part;

        paragraphs.forEach(paragraph => {
            let lastChunk: any = null;
            paragraph.chunks.forEach((chunk, chunkIndex) => {
                if (chunk.selected) {
                    if (chunkIndex === 0) {
                        addPart(paragraph.leadingPunctuation ?? "");
                    } else if (lastChunk) {
                        addPart(lastChunk.nextPunctuation);
                    } else if (querySentence.value.length !== 0) {
                        addPart(ELLIPSE); // previous paragraphs selected, but this chunk is not the first in this paragraph.
                    }
                    addPart(chunk.text);
                    lastChunk = chunk;
                    if (chunkIndex === paragraph.chunks.length - 1) {
                        addPart(chunk.nextPunctuation);
                    }
                } else {
                    if (lastChunk) {
                        if (['。', '！', '？'].includes(lastChunk.nextPunctuation[0])) {
                            // If it ends with patterns like 。”, we also deem it as a stop, so the first punctuation is chosen.
                            addPart(lastChunk.nextPunctuation);
                        }
                        addPart(ELLIPSE);
                        lastChunk = null;
                    }
                }
            });
        });

        if (querySentence.value.endsWith(ELLIPSE)) {
            querySentence.value = querySentence.value.slice(0, querySentence.value.length - ELLIPSE.length);
        }
    }, { immediate: true, deep: true });

    async function queryFrequency(query: string, page: number = 1, requestId?: string) {
        freqInfo.value = await useApiStore().queryFreq(query, page, requestId);
    }

    async function query() {
        const apiStore = useApiStore();
        const userStore = useUserStore();

        currentRecorded.value = false;
        lastQuery.sentence = querySentence.value;
        lastQuery.word = queryWord.value;
        lastQuery.index = queryIndex.value;

        for (const requestId of [requestIds.queryFlash, requestIds.queryThinking, requestIds.queryFreq]) {
            if (requestId) {
                apiStore.abortRequest(requestId);
            }
        }

        requestIds.queryFreq = nanoid();
        requestIds.queryFlash = nanoid();
        requestIds.queryThinking = nanoid();

        await Promise.all([
            queryFrequency(queryWord.value, 1, requestIds.queryFreq),
            apiStore.queryFlash(queryWord.value, querySentence.value, getFrontendHandler(), requestIds.queryFlash),
            apiStore.queryThinking(queryWord.value, querySentence.value, userStore.deepThinking, getFrontendHandler(), requestIds.queryThinking),
        ]);
        console.log("Request Ended");
    }

    async function searchOriginal() {
        const apiStore = useApiStore();

        if (requestIds.searchOriginal) {
            apiStore.abortRequest(requestIds.searchOriginal);
        }

        requestIds.searchOriginal = nanoid();

        await apiStore.searchOriginalText(activeText.value, searchTarget.value, getFrontendHandler(), requestIds.searchOriginal);
    }

    function getFrontendHandler(): FrontendHandler {
        function getLazyEmptyUpdater(reference: Ref<string>) {
            let isFirst = true;
            return (contentChunk: string) => {
                if (isFirst) {
                    reference.value = contentChunk;
                    isFirst = false;
                } else {
                    reference.value += contentChunk;
                }
            };
        }

        return {
            updateFlash: getLazyEmptyUpdater(aiInstantResponse),
            updateThinking: getLazyEmptyUpdater(aiThoughtResponse),
            updateUsage: useUserStore().updateUsage,
            updateZdic: (zdicResult) => {
                zdicResponse.value = zdicResult;
            },
            updateSearchOriginal: getLazyEmptyUpdater(activeText),
            updateExtract: () => { },
        };
    }

    function adopt_answer(answer: string) {
        currentRecorded.value = true;
        const newRecord: HistoryRecord = {
            id: nanoid(),
            level: "A",
            front: format_front(lastQuery.sentence, lastQuery.index),
            back: answer,
            additions: [],
            createdAt: new Date().toLocaleString(),
        };
        const historyStore = useHistoryStore();
        historyStore.insertHistory(newRecord);
        const apiStore = useApiStore();
        apiStore.adoptAnswer(lastQuery.sentence, lastQuery.word, answer);
    }

    function updateParagraphs(text: string) {
        const fullText = text.trim();
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
    }

    function selectChunk(indexPara: number, indexChunk: number) {
        const paragraph = paragraphs[indexPara];
        const chunk = paragraph.chunks[indexChunk];
        chunk.selected = !chunk.selected;
    }

    function selectWholeParagraph(indexPara: number) {
        const paragraph = paragraphs[indexPara];
        const allSelected = paragraph.chunks.every(chunk => chunk.selected);
        paragraph.chunks.forEach(chunk => {
            chunk.selected = !allSelected;
        });
    }

    function clearChunkSelection() {
        paragraphs.forEach(paragraph => paragraph.chunks.forEach(chunk => chunk.selected = false));
    }

    return {
        activeText,
        searchTarget,
        querySentence,
        queryWord,
        lastQuery,
        queryIndex,
        freqInfo,
        aiInstantResponse,
        aiThoughtResponse,
        aiThoughtStructured,
        zdicResponse,
        currentRecorded,
        chars,
        paragraphs,
        searchOriginal,
        adopt_answer,
        query,
        queryFrequency,
        updateParagraphs,
        selectChunk,
        selectWholeParagraph,
        clearChunkSelection,
    }
});