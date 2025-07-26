import { update_from_query } from './utils';
import { defineStore } from 'pinia';
import { type ResponseChunk, type FrontendHandler, SearchTarget, User, FreqResult } from './types';
import { useUserStore } from './user';
import { Sha256 } from '@aws-crypto/sha256-js';

export const useApiStore = defineStore("api", () => {
    async function call_get(url: string) {
        const userStore = useUserStore();
        const headers = new Headers();
        if (userStore.token) {
            headers.append("Authorization", `Bearer ${userStore.token}`);
        }

        return fetch(url, {
            headers,
        });
    }

    async function call_post(url: string, body_json: any) {
        const userStore = useUserStore();
        const headers = new Headers();
        headers.append("Content-Type", "application/json");
        if (userStore.token) {
            headers.append("Authorization", `Bearer ${userStore.token}`);
        }
        return fetch(url, {
            method: "POST",
            headers,
            body: JSON.stringify(body_json),
        });
    }

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

    async function guardJsonResponse(fetched: Promise<Response>) {
        try {
            const response = await fetched;
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return await response.json();
        } catch (error) {
            console.error('Error fetching data:', error);
            throw error;
        }
    }

    async function guardStreamingResponse(fetched: Promise<Response>) {
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

    async function queryFlash(
        queryWord: string,
        querySentence: string,
        frontendHandler: FrontendHandler,
    ) {
        const { reader, decoder } = await guardStreamingResponse(call_get(`/api/query/flash?q=${encodeURIComponent(queryWord)}&context=${encodeURIComponent(querySentence)}`));

        await readStream(reader, decoder, frontendHandler);
    }

    async function queryThinking(
        queryWord: string,
        querySentence: string,
        frontendHandler: FrontendHandler,
    ) {
        const { reader, decoder } = await guardStreamingResponse(call_get(`/api/query/thinking?q=${encodeURIComponent(queryWord)}&context=${encodeURIComponent(querySentence)}`));

        await readStream(reader, decoder, frontendHandler);
    }

    async function searchOriginalText(excerpt: string, target: SearchTarget, frontendHandler: FrontendHandler) {
        const { reader, decoder } = await guardStreamingResponse(
            call_get(`/api/search-original?excerpt=${encodeURIComponent(excerpt)}&target=${target}`));

        await readStream(reader, decoder, frontendHandler);
    }

    async function queryFreq(query: string, page: number): Promise<FreqResult> {
        try {
            const response = await guardJsonResponse(call_get(`/api/query/freq-info?q=${encodeURIComponent(query)}&page=${page}`));

            return new FreqResult(response);
        } catch (e) {
            return FreqResult.empty();

        }
    }

    async function sha256(password: string) {
        const array = await new Sha256(password).digest();
        return Array.from(new Uint8Array(array))
            .map((b) => b.toString(16).padStart(2, "0"))
            .join("");
    }

    async function register(email: string, password: string, updateToken: (token: string) => void, updateUser: (user: User) => void) {
        await guardJsonResponse(call_post("/api/auth/register", { email, password: await sha256(password) }));
        await login(email, password, updateToken, updateUser);
    }

    async function login(email: string, password: string, updateToken: (token: string) => void, updateUser: (user: User) => void) {
        const response = await guardJsonResponse(call_post("/api/auth/login", { email, password: await sha256(password) }));
        updateToken(response.token);
        updateUser(new User(response.user));
        await getUserInfo(updateUser, updateToken);
    }

    async function getBalanceDetails(page: number = 1) {
        const response = await guardJsonResponse(call_get(`/api/balance-details?page=${page}`));
        return await response;
    }

    async function adoptAnswer(context: string, query: string, answer: string) {
        await guardJsonResponse(call_post('/api/adopt-answer', { context, query, answer }));
    }

    async function getUserInfo(updateUser: (user: User) => void, updateToken: (token: string) => void) {
        const authResult = await guardJsonResponse(call_get("/api/user"));
        updateUser(new User(authResult.user));
        updateToken(authResult.token);
    }

    return {
        queryFlash,
        queryThinking,
        queryFreq,
        searchOriginalText,
        getBalanceDetails,
        register,
        login,
        adoptAnswer,
        getUserInfo,
    }
})
