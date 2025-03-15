import { defineStore } from 'pinia';
import { useLocalStorage } from '@vueuse/core';
import { ref } from 'vue';

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
    const queryWord = useLocalStorage("EC_queryWord", "");

    const textAnnotations = ref(new Array<PassageAnnotation>());
    const aiInstantResponse = ref("");

    async function query(word: string) {
        queryWord.value = word;
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
                const { type, result } = JSON.parse(data);
                switch (type) {
                    case "text":
                        textAnnotations.value = result.map((raw: JsonType<PassageAnnotation>) => new PassageAnnotation(raw));
                        break;
                    case "ai-instant":
                        aiInstantResponse.value += result.content;
                        break;
                    default:
                        console.error(`Unknown type: ${type}`);
                        break;
                }
            }
        }
        console.log("Stream ended");
    }

    return {
        querySentence,
        queryWord,
        textAnnotations,
        aiInstantResponse,
        query,
    }
});
