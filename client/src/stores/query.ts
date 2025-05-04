import { defineStore } from 'pinia';
import { useLocalStorage } from '@vueuse/core';
import { computed, ref, watch } from 'vue';
import { nanoid } from 'nanoid';
import { PassageAnnotation, type HistoryRecord } from './types';
import { format_front } from './utils';
import { queryInstant, queryThought } from './api';

export const useQueryStore = defineStore("query", () => {
    const querySentence = useLocalStorage("EC_querySentence", "");
    const usage = useLocalStorage("EC_usage", 0); // 1e-7 yuan
    const history = useLocalStorage<HistoryRecord[]>("EC_history", []);
    const MAX_HISTORY = 100;

    const queryWord = ref("");
    const queryIndex = ref(new Set<number>());
    const textAnnotations = ref(new Array<PassageAnnotation>());
    const aiInstantResponse = ref("");
    const aiThoughtResponse = ref("");
    const currentRecorded = ref(false);
    const zdicResponse = ref({ basic_explanations: new Array<string>(), detailed_explanations: new Array<string>(), phrase_explanations: new Array<string>() });

    const instantStructured = computed(() => {
        const lines = aiInstantResponse.value.split("\n");
        const result = {
            think: '',
            explain: '',
            answer: '',
        };

        let area: 'think' | 'explain' | 'answer' | '' = '';

        lines.forEach(line => {
            let startIndex = 0;
            let endIndex = line.length;

            if (line.startsWith("<think>")) {
                area = 'think';
                startIndex = line.indexOf('>') + 1;
            } else if (line.startsWith("<explain>")) {
                area = 'explain';
                startIndex = line.indexOf('>') + 1;
            } else if (line.startsWith("<answer>")) {
                area = 'answer';
                startIndex = line.indexOf('>') + 1;
            }

            if (line.endsWith("</think>") || line.endsWith("</explain>") || line.endsWith("</answer>")) {
                endIndex = line.lastIndexOf('<');
            }

            if (area) {
                result[area] += line.substring(startIndex, endIndex) + '\n';
            }

            if (endIndex !== line.length) {
                area = '';
            }
        });

        return result
    });

    const thoughtStructured = computed(() => {
        const lines = aiThoughtResponse.value.split("\n");
        const result = {
            think: '',
            explain: '',
            answers: new Array<string>(),
        };

        let area: 'think' | 'explain' | 'answers' | '' = '';

        lines.forEach(line => {
            let startIndex = 0;
            let endIndex = line.length;

            if (line.startsWith("<think>")) {
                area = 'think';
                startIndex = line.indexOf('>') + 1;
            } else if (line.startsWith("<explain>")) {
                area = 'explain';
                startIndex = line.indexOf('>') + 1;
            } else if (line.startsWith("<answers>")) {
                area = 'answers';
                startIndex = line.indexOf('>') + 1;
            }

            if (line.endsWith("</think>") || line.endsWith("</explain>") || line.endsWith("</answers>")) {
                endIndex = line.lastIndexOf('<');
            }

            if (area) {
                const text = line.substring(startIndex, endIndex);
                if (area === 'answers') {
                    result.answers.push(...(text.trim() ? text.split("；") : []));
                } else {
                    result[area] += text + '\n';
                }
            }

            if (endIndex !== line.length) {
                area = '';
            }
        });

        return result;
    });

    async function query() {
        currentRecorded.value = false;
        await Promise.all([
            queryInstant(queryWord, querySentence, aiInstantResponse, textAnnotations, aiThoughtResponse, usage, zdicResponse),
            queryThought(queryWord, querySentence, aiThoughtResponse, textAnnotations, aiInstantResponse, usage, zdicResponse)
        ]);
        console.log("Request Ended");
    }

    function export_history(selected: HistoryRecord[]) {
        const json = {
            version: 3,
            title: `文言文字词梳理 ${new Date().toLocaleString()}`,
            records: selected.map(r => ({
                id: r.id,
                level: r.level,
                front: r.front,
                back: r.userModifiedBack ?? r.back,
                additions: r.additions
            })),
            footer: "",
            deckType: "type",
        };
        const blob = new Blob([JSON.stringify(json, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `history_${Date.now()}.json`;
        a.click();
        URL.revokeObjectURL(url);
    };

    function delete_history(selected: HistoryRecord[]) {
        history.value = history.value.filter(record => !selected.some(item => item.id === record.id));
    }

    function adopt_answer(answer: string) {
        currentRecorded.value = true;
        const newRecord: HistoryRecord = {
            id: nanoid(),
            level: "A",
            front: format_front(querySentence.value, queryIndex.value),
            back: answer,
            additions: [],
        };
        history.value.unshift(newRecord);
        if (history.value.length > MAX_HISTORY) {
            history.value.pop();
        }
    }

    return {
        querySentence,
        queryWord,
        queryIndex,
        usage,
        textAnnotations,
        aiInstantResponse,
        instantStructured,
        aiThoughtResponse,
        thoughtStructured,
        zdicResponse,
        history,
        currentRecorded,
        export_history,
        delete_history,
        adopt_answer,
        query,
    }
});
