import { update_from_query } from './utils';
import type { ResponseChunk, FrontendHandler, SearchTarget } from './types';

async function readStream(
    reader: ReadableStreamDefaultReader<Uint8Array>,
    decoder: TextDecoder,
    frontendHandler: FrontendHandler,
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
                    update_from_query(responseChunk, frontendHandler);
                } catch (error) {
                    console.error('Error parsing JSON chunk:', error);
                }
            }
        }
    }
}

async function guardResponse(fetched: Promise<Response>) {
    const response = await fetched;

    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }
    if (!response.body) {
        throw new Error("No response body");
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();

    return { reader, decoder, response };
}

export async function queryFlash(
    queryWord: string,
    querySentence: string,
    frontendHandler: FrontendHandler,
) {
    const { reader, decoder } = await guardResponse(
        fetch(`/api/query/flash?q=${encodeURIComponent(queryWord)}&context=${encodeURIComponent(querySentence)}`)
    );

    await readStream(reader, decoder, frontendHandler);
}

export async function queryThinking(
    queryWord: string,
    querySentence: string,
    frontendHandler: FrontendHandler,
) {
    const { reader, decoder } = await guardResponse(
        fetch(`/api/query/thinking?q=${encodeURIComponent(queryWord)}&context=${encodeURIComponent(querySentence)}`)
    );

    await readStream(reader, decoder, frontendHandler);
}

export async function searchOriginalText(excerpt: string, target: SearchTarget, frontendHandler: FrontendHandler) {
    const { reader, decoder } = await guardResponse(
        fetch(`/api/search-original?excerpt=${encodeURIComponent(excerpt)}&target=${target}`));

    await readStream(reader, decoder, frontendHandler);
}
