import { update_from_query } from './utils';
import { type Ref } from 'vue';
import type { ResponseChunk, PassageAnnotation, ZdicResult } from './types';

async function readStream(
    reader: ReadableStreamDefaultReader<Uint8Array>,
    decoder: TextDecoder,
    textAnnotations: Ref<PassageAnnotation[]>,
    aiInstantResponse: Ref<string>,
    aiThoughtResponse: Ref<string>,
    usage: Ref<number>,
    zdicResponse: Ref<ZdicResult>
) {
    let done = false;
    while (!done) {
        const { value, done: streamDone } = await reader.read();
        done = streamDone;
        if (value) {
            const data = decoder.decode(value, { stream: true });
            const chunks = data.trim().split("\n");
            for (const chunk of chunks) {
                try {
                    const responseChunk: ResponseChunk = JSON.parse(chunk);
                    update_from_query(
                        responseChunk,
                        textAnnotations,
                        aiInstantResponse,
                        aiThoughtResponse,
                        usage,
                        zdicResponse
                    );
                } catch (error) {
                    console.error('Error parsing JSON chunk:', error);
                }
            }
        }
    }
}

export async function queryInstant(
    queryWord: Ref<string>,
    querySentence: Ref<string>,
    aiInstantResponse: Ref<string>,
    textAnnotations: Ref<PassageAnnotation[]>,
    aiThoughtResponse: Ref<string>,
    usage: Ref<number>,
    zdicResponse: Ref<ZdicResult>
) {
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

    await readStream(reader, decoder, textAnnotations, aiInstantResponse, aiThoughtResponse, usage, zdicResponse);
}

export async function queryThought(
    queryWord: Ref<string>,
    querySentence: Ref<string>,
    aiThoughtResponse: Ref<string>,
    textAnnotations: Ref<PassageAnnotation[]>,
    aiInstantResponse: Ref<string>,
    usage: Ref<number>,
    zdicResponse: Ref<ZdicResult>
) {
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

    await readStream(reader, decoder, textAnnotations, aiInstantResponse, aiThoughtResponse, usage, zdicResponse);
}
