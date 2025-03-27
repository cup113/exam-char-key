import { defineStore } from 'pinia';
import { useLocalStorage } from '@vueuse/core';
import { computed, ref } from 'vue';

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

export const useQueryStore = defineStore("query", () => {
    const querySentence = useLocalStorage("EC_querySentence", "");
    const usage = useLocalStorage("EC_usage", 0); // 1e-7 yuan

    const queryWord = ref("");
    const textAnnotations = ref(new Array<PassageAnnotation>());
    const aiInstantResponse = ref("");
    const aiThoughtResponse = ref("");
    const zdicResponse = ref({ basic_explanations: new Array<string>(), detailed_explanations: new Array<string>() });

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
        await Promise.all([queryInstant(), queryThought()]);
        console.log("Request Ended");
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
        query,
    }
});
