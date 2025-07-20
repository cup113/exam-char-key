import { defineStore } from 'pinia';
import { useLocalStorage } from '@vueuse/core';
import { computed, ref, type Ref } from 'vue';
import { nanoid } from 'nanoid';
import { PassageAnnotation, SearchTarget, type HistoryRecord, type FrontendHandler } from './types';
import { format_front, parse_ai_thought_response } from './utils';
import { queryInstant, queryThought, searchOriginalText } from './api';
import { useHistoryStore } from './history';
import { useSettingsStore } from './settings';

export const useQueryStore = defineStore("query", () => {
    const activeText = useLocalStorage("EC_activeText", "");
    const searchTarget = useLocalStorage<SearchTarget>("EC_searchTarget", SearchTarget.None);
    const querySentence = useLocalStorage("EC_querySentence", "");
    const queryIndex = ref(new Set<number>());
    const queryWord = computed(() => {
        return Array.from(queryIndex.value).sort((a, b) => a - b).map(i => querySentence.value[i]).join('');
    });
    const displayWord = ref("");

    const textAnnotations = ref(new Array<PassageAnnotation>());
    const aiInstantResponse = ref("");
    const aiThoughtResponse = ref("");
    const currentRecorded = ref(true);
    const zdicResponse = ref({ basic_explanations: new Array<string>(), detailed_explanations: new Array<string>(), phrase_explanations: new Array<string>() });

    const aiThoughtStructured = computed(() => {
        return parse_ai_thought_response(aiThoughtResponse.value);
    });

    async function query() {
        currentRecorded.value = false;
        displayWord.value = queryWord.value;
        await Promise.all([
            queryInstant(queryWord.value, querySentence.value, getFrontendHandler()),
            queryThought(queryWord.value, querySentence.value, getFrontendHandler()),
        ]);
        console.log("Request Ended");
    }

    async function searchOriginal() {
        await searchOriginalText(activeText.value, searchTarget.value, getFrontendHandler());
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
            updateTextAnnotations: (annotations: PassageAnnotation[]) => {
                textAnnotations.value = annotations;
            },
            updateInstant: getLazyEmptyUpdater(aiInstantResponse),
            updateThought: getLazyEmptyUpdater(aiThoughtResponse),
            updateUsage: useSettingsStore().updateUsage,
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
            front: format_front(querySentence.value, queryIndex.value), // TODO fix stress
            back: answer,
            additions: [],
            createdAt: new Date().toLocaleString(),
        };
        const historyStore = useHistoryStore();
        historyStore.insertHistory(newRecord);
    }

    return {
        activeText,
        searchTarget,
        querySentence,
        queryWord,
        displayWord,
        queryIndex,
        textAnnotations,
        aiInstantResponse,
        aiThoughtResponse,
        aiThoughtStructured,
        zdicResponse,
        currentRecorded,
        searchOriginal,
        adopt_answer,
        query,
    }
});
