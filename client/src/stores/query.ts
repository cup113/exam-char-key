import { defineStore } from 'pinia';
import { useLocalStorage } from '@vueuse/core';
import { computed, reactive, ref, type Ref } from 'vue';
import { nanoid } from 'nanoid';
import { SearchTarget, type HistoryRecord, type FrontendHandler, FreqResult } from './types';
import { format_front, parse_ai_thought_response } from './utils';
import { useApiStore } from './api';
import { useHistoryStore } from './history';
import { useUserStore } from './user';

const exampleText = `示例文本：《离骚》（节选）
可点击上方“添加/修改文本内容”，将你想要查询的文本内容填至此处。
帝高阳之苗裔兮，朕皇考曰伯庸。
摄提贞于孟陬兮，惟庚寅吾以降。
皇览揆余初度兮，肇锡余以嘉名。
名余曰正则兮，字余曰灵均。
纷吾既有此内美兮，又重之以修能。
扈江离与辟芷兮，纫秋兰以为佩。
汩余若将不及兮，恐年岁之不吾与。
朝搴阰之木兰兮，夕揽洲之宿莽。
日月忽其不淹兮，春与秋其代序。
惟草木之零落兮，恐美人之迟暮。
不抚壮而弃秽兮，何不改乎此度？
乘骐骥以驰骋兮，来吾道夫先路！`;

export const useQueryStore = defineStore("query", () => {
    const activeText = useLocalStorage("EC_activeText", exampleText);
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

    const requestIds = {
        queryFlash: "",
        queryThinking: "",
        queryFreq: "",
        searchOriginal: "",
    };

    const aiThoughtStructured = computed(() => {
        return parse_ai_thought_response(aiThoughtResponse.value);
    });

    async function queryFrequency(query: string, page: number = 1, requestId?: string) {
        freqInfo.value = await useApiStore().queryFreq(query, page, requestId);
    }

    async function query(simple: boolean) {
        const apiStore = useApiStore();
        const userStore = useUserStore();

        userStore.deepThinking = !simple;

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