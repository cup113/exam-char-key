import { defineStore } from 'pinia';
import { useLocalStorage } from '@vueuse/core';
import { computed, ref, watch } from 'vue';
import { nanoid } from 'nanoid';

type JsonType<T> = T extends Date ? string
    : T extends Function | undefined | symbol ? never
    : T extends object ? { [K in keyof T]: JsonType<T[K]> } : T;

class PassageAnnotation {
    public context: string;
    public core_detail: string;
    public detail: string;
    public index_range: [number, number];
    public name_passage: string;

    constructor(raw: JsonType<PassageAnnotation>) {
        this.context = raw.context;
        this.core_detail = raw.core_detail;
        this.detail = raw.detail;
        this.index_range = raw.index_range;
        this.name_passage = raw.name_passage;
    }

    public get_keyword() {
        return this.context.substring(this.index_range[0], this.index_range[1]);
    }
}

export interface HistoryRecord {
    id: string;
    level: string;
    front: string;
    back: string;
    userModifiedBack?: string; // 用户修改的答案
    additions: any[];
}

export const useQueryStore = defineStore("query", () => {
    const querySentence = useLocalStorage("EC_querySentence", "");
    const usage = useLocalStorage("EC_usage", 0); // 1e-7 yuan
    const history = useLocalStorage<HistoryRecord[]>("EC_history", []);
    const MAX_HISTORY = 100;

    const queryWord = ref("");
    const textAnnotations = ref(new Array<PassageAnnotation>());
    const aiInstantResponse = ref("");
    const aiThoughtResponse = ref("");
    const currentRecorded = ref(false);
    const zdicResponse = ref({ basic_explanations: new Array<string>(), detailed_explanations: new Array<string>() });


    const queryIndex = ref(new Set<number>());

    watch(querySentence, (newSentence, oldSentence) => {
        if (newSentence !== oldSentence) {
            queryIndex.value.clear();
            if (newSentence.length <= 2 && newSentence.length >= 1) {
                queryIndex.value.add(0);
                if (newSentence.length === 2) {
                    queryIndex.value.add(1);
                }
            }
        }
    });

    function toggle_index(index: number) {
        if (queryIndex.value.has(index)) {
            queryIndex.value.delete(index);
        } else {
            queryIndex.value.add(index);
        }
        queryWord.value = Array.from(queryIndex.value).sort().map(i => querySentence.value[i]).join();
    }

    const instantStructured = computed(() => {
        const lines = aiInstantResponse.value.split("\n");
        const result = {
            think: '',
            answer: '',
            explain: '',
            conf: NaN,
        };

        lines.forEach(line => {
            if (line.startsWith("think/")) {
                result.think = line.substring("think/".length);
            } else if (line.startsWith("answer/")) {
                result.answer = line.substring("answer/".length);
            } else if (line.startsWith("explain/")) {
                result.explain = line.substring("explain/".length);
            } else if (line.startsWith("conf/")) {
                result.conf = parseInt(line.substring("conf/".length));
            }
        });

        return result
    });

    const thoughtStructured = computed(() => {
        const lines = aiThoughtResponse.value.split("\n");
        const result = {
            think: '',
            candidates: new Array<{ answer: string, explanation: string }>(),
            answers: new Array<{ answer: string, conf: number }>(),
        };

        let multiLineArea: '' | 'candidates' | 'answers' = '';

        lines.forEach(line => {
            if (line.startsWith('think/')) {
                result.think = line.substring("think/".length);
                multiLineArea = '';
            } else if (line.startsWith('candidates/')) {
                multiLineArea = 'candidates';
            } else if (line.startsWith('answers/')) {
                multiLineArea = 'answers';
            } else if (multiLineArea === 'candidates') {
                const slashIndex = line.indexOf('/');
                result.candidates.push({
                    answer: line.substring(0, slashIndex),
                    explanation: line.substring(slashIndex + 1),
                });
            } else if (multiLineArea === 'answers') {
                const slashIndex = line.indexOf('/');
                result.answers.push({
                    answer: line.substring(0, slashIndex),
                    conf: parseInt(line.substring(slashIndex + 1)),
                });
            }
        });

        return result;
    });

    function update_from_query(type: string, result: any) {
        switch (type) {
            case "text":
                textAnnotations.value = result.map((raw: JsonType<PassageAnnotation>) => new PassageAnnotation(raw));
                break;
            case "ai-instant":
                aiInstantResponse.value += result.content;
                break;
            case "ai-thought":
                aiThoughtResponse.value += result.content;
                break;
            case 'ai-usage':
                usage.value += result.prompt_tokens * 8 + result.completion_tokens * 20;
                break;
            case "zdic":
                zdicResponse.value = result;
                break;
            default:
                console.error(`Unknown type: ${type}`);
                break;
        }
    }

    async function queryInstant() {
        const response = await fetch(`/api/query?q=${encodeURIComponent(queryWord.value)}&context=${encodeURIComponent(querySentence.value)}`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        if (!response.body) {
            throw new Error("No response body");
        }

        aiInstantResponse.value = "";

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let done = false;

        while (!done) {
            const { value, done: streamDone } = await reader.read();
            done = streamDone;
            if (value) {
                const data = decoder.decode(value, { stream: true });
                const chunks = data.trim().split("\n");
                for (const chunk of chunks) {
                    const { type, result } = JSON.parse(chunk);
                    update_from_query(type, result);
                }
            }
        }
    }

    async function queryThought() {
        const response = await fetch(`/api/query?q=${encodeURIComponent(queryWord.value)}&context=${encodeURIComponent(querySentence.value)}&instant=0`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        if (!response.body) {
            throw new Error("No response body");
        }

        aiThoughtResponse.value = "";

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let done = false;
        while (!done) {
            const { value, done: streamDone } = await reader.read();
            done = streamDone;
            if (value) {
                const data = decoder.decode(value, { stream: true });
                const chunks = data.trim().split("\n");
                for (const chunk of chunks) {
                    const { type, result } = JSON.parse(chunk);
                    update_from_query(type, result);
                }
            }
        }
    }

    async function query() {
        currentRecorded.value = false;
        await Promise.all([queryInstant(), queryThought()]);
        console.log("Request Ended");
    }

    function export_history(selected: HistoryRecord[]) {
        const json = {
            version: 1,
            title: `文言文字词梳理 ${new Date().toLocaleString()}`,
            records: selected.map(r => ({
                id: r.id,
                level: r.level,
                front: r.front,
                back: r.userModifiedBack ?? r.back,
                additions: r.additions
            }))
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

    function format_front(sentence: string, indices: Set<number>) {
        const chars = Array.from(sentence);
        indices.forEach(i => {
            chars[i] = `<strong>${chars[i]}</strong>`;
        });
        return chars.join('');
    };

    function adopt_answer(answer: string) {
        currentRecorded.value = true;
        const newRecord: HistoryRecord = {
            id: nanoid(),
            level: "A",
            front: format_front(querySentence.value, queryIndex.value), // 新增高亮逻辑
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
        usage,
        textAnnotations,
        aiInstantResponse,
        instantStructured,
        aiThoughtResponse,
        thoughtStructured,
        zdicResponse,
        queryIndex,
        history,
        currentRecorded,
        toggle_index,
        export_history,
        delete_history,
        adopt_answer,
        query,
    }
});
