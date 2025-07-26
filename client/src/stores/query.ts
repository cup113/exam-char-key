import { defineStore } from 'pinia';
import { useLocalStorage } from '@vueuse/core';
import { computed, reactive, ref, type Ref } from 'vue';
import { nanoid } from 'nanoid';
import { SearchTarget, type HistoryRecord, type FrontendHandler, FreqResult } from './types';
import { format_front, parse_ai_thought_response } from './utils';
import { useApiStore } from './api';
import { useHistoryStore } from './history';
import { useUserStore } from './user';

export const useQueryStore = defineStore("query", () => {
    const activeText = useLocalStorage("EC_activeText", "");
    const searchTarget = useLocalStorage<SearchTarget>("EC_searchTarget", SearchTarget.None);
    const querySentence = ref("");
    const queryIndex = ref(new Set<number>());
    const queryWord = computed(() => {
        return Array.from(queryIndex.value).sort((a, b) => a - b).map(i => querySentence.value[i]).join('');
    });
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

    const aiThoughtStructured = computed(() => {
        return parse_ai_thought_response(aiThoughtResponse.value);
    });

    async function queryFrequency(query: string, page: number = 1) {
        freqInfo.value = await useApiStore().queryFreq(query, page);
    }

    async function query() {
        const apiStore = useApiStore();

        currentRecorded.value = false;
        lastQuery.sentence = querySentence.value;
        lastQuery.word = queryWord.value;
        lastQuery.index = queryIndex.value;

        await Promise.all([
            apiStore.queryFlash(queryWord.value, querySentence.value, getFrontendHandler()),
            apiStore.queryThinking(queryWord.value, querySentence.value, getFrontendHandler()),
            queryFrequency(queryWord.value),
        ]);
        console.log("Request Ended");
    }

    async function searchOriginal() {
        await useApiStore().searchOriginalText(activeText.value, searchTarget.value, getFrontendHandler());
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
        searchOriginal,
        adopt_answer,
        query,
        queryFrequency,
    }
});
