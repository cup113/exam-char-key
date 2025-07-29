import { defineStore } from 'pinia';
import { useLocalStorage } from '@vueuse/core';
import { computed, reactive, ref, type Ref } from 'vue';
import { nanoid } from 'nanoid';
import { SearchTarget, type HistoryRecord, type FrontendHandler, FreqResult } from './types';
import { format_front, parse_ai_thought_response } from './utils';
import { useApiStore } from './api';
import { useHistoryStore } from './history';
import { useUserStore } from './user';

const exampleText = `（示例文本）可点击上方“添加/修改文本内容”，将你想要查询的文本内容填至此处。
点击文本加入上下文，然后继续在下方执行查询功能。
采苓子者，名濂，字仲德，姓郑氏。浦阳白麟溪人。
颇潜心于《易》，人不能知，谓其善别药，荐为医官。采苓子曰：“吾闻诸礼，医虽良技，不得与士齿，吾能安于医邪？”竟弃去，放情丘壑间，被古冠服。一苍头持九节筇随其后。采苓子或坐石支颐，历玩烟岫；或箫歌于云水苍茫之中，其声激烈，如出金石；或入走蓝山泽畔，采苓而采之，心旷心冲，外物之胶葛者，悉不足以参其内。年愈五十，髭须皆黑，无华皓者。
或曰：“采苓子其隐者欤？古之幽人狷士，凡欲寄其高情远韵者，莫不餐菊而纫兰。”采苓子曰：“以苓为事，殆类是欤？”或曰：“采苓子非隐者欤？苓乃大苦，有和药之功焉。其将出而医世，采苓所以志之欤？”采苓子笑曰：“谓予为隐耶，吾从而隐之；谓予为非隐邪，吾从而非隐之。隐固非也，非隐亦非也。大块⑥既授我以形，显之、微之、潜之、昭之，一将听之。苟参之以人焉，则神分不全矣。神分则真漓，真漓则道戾，道既戾则吾将觅我且不可得，况听为隐与非隐者邪？”
金华宋濂闻而异之，因与采苓子游，同步白麟溪滨，见其目光炯炯，射松桂上如月，疑其有道。`;

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