import { update_from_query } from './utils';
import { defineStore } from 'pinia';
import { type ResponseChunk, type FrontendHandler, SearchTarget, User, FreqResult } from './types';
import { useUserStore } from './user';
import { Sha256 } from '@aws-crypto/sha256-js';

export const useApiStore = defineStore("api", () => {
    const abortControllers = new Map<string, AbortController>();

    function getAbortController(id: string): AbortController {
        const controller = new AbortController();
        abortControllers.set(id, controller);
        return controller;
    }

    function removeAbortController(id: string) {
        abortControllers.delete(id);
    }

    function abortRequest(id: string) {
        const controller = abortControllers.get(id);
        if (controller) {
            controller.abort();
            abortControllers.delete(id);
        }
    }

    function isAbortError(error: unknown): boolean {
        return error instanceof Error && error.name === 'AbortError';
    }

    async function call_get(url: string, requestId?: string) {
        const userStore = useUserStore();
        const headers = new Headers();
        if (userStore.token) {
            headers.append("Authorization", `Bearer ${userStore.token}`);
        }

        const options: RequestInit = { headers };
        if (requestId) {
            const controller = getAbortController(requestId);
            options.signal = controller.signal;
        }

        return fetch(url, options);
    }

    async function call_post(url: string, body_json: any, requestId?: string) {
        const userStore = useUserStore();
        const headers = new Headers();
        headers.append("Content-Type", "application/json");
        if (userStore.token) {
            headers.append("Authorization", `Bearer ${userStore.token}`);
        }

        const options: RequestInit = {
            method: "POST",
            headers,
            body: JSON.stringify(body_json),
        };
        if (requestId) {
            const controller = getAbortController(requestId);
            options.signal = controller.signal;
        }

        return fetch(url, options);
    }

    async function readStream(
        reader: ReadableStreamDefaultReader<Uint8Array>,
        decoder: TextDecoder,
        frontendHandler: FrontendHandler,
    ) {
        let done = false;
        while (!done) {
            try {
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
            } catch (error) {
                if (!isAbortError(error)) {
                    console.error('Error reading stream:', error);
                }
                done = true;
            }
        }
    }

    async function guardJsonResponse(fetched: Promise<Response>, allowStatus: number[], requestId?: string) {
        try {
            const response = await fetched;
            if (requestId) {
                removeAbortController(requestId);
            }
            if (!response.ok) {
                if (allowStatus.includes(response.status)) {
                    return response;
                }
                const message = alertMessageConverter(response.status);
                showErrorAlert(message, response.url, `状态码: ${response.status} ${response.statusText}`);
                throw new Error('handled');
            }
            return await response.json();
        } catch (error) {
            if (requestId) {
                removeAbortController(requestId);
            }
            if (!isAbortError(error)) {
                if (error instanceof Error && error.message == 'handled') {
                    throw error;
                }
                console.error('Error fetching data:', error);
                showErrorAlert('发生未知错误，请联系管理员');
                throw error;
            }
        }
    }

    async function guardStreamingResponse(fetched: Promise<Response>, allowStatus: number[], requestId?: string) {
        try {
            const response = await fetched;

            if (requestId) {
                removeAbortController(requestId);
            }

            if (!response.ok) {
                const message = alertMessageConverter(response.status);
                if (allowStatus.includes(response.status)) {
                    return { reader: null, decoder: null, response };
                }
                showErrorAlert(message, response.url, `状态码: ${response.status} ${response.statusText}`);
                throw new Error('handled');
            }
            if (!response.body) {
                throw new Error("No response body");
            }

            const reader = response.body.getReader();
            const decoder = new TextDecoder();

            return { reader, decoder, response };
        } catch (error) {
            if (requestId) {
                removeAbortController(requestId);
            }
            if (!isAbortError(error)) {
                if (error instanceof Error && error.message == 'handled') {
                    throw error;
                }
                console.error('Error in streaming response:', error);
                showErrorAlert('发生未知错误，请联系管理员');
                throw error;
            }

            return { reader: null, decoder: null, response: null };
        }
    }

    function showErrorAlert(message: string, url?: string, detail?: string) {
        let alertMessage = message;
        if (url) {
            alertMessage += `\nURL: ${url}`;
        }
        if (detail) {
            alertMessage += `\n${detail}`;
        }
        alert(alertMessage);
    }

    function alertMessageConverter(status: number): string {
        const userStore = useUserStore();
        switch (status) {
            case 401:
                return '您尚未登录或登录已过期，请重新登录。';
            case 402:
                return '您的余额不足。' + (userStore.isGuest ? '请前往设置页面注册以获得更多额度。' : '请联系网站管理员提升每日额度，或等到明天再前来查询。');
            case 404:
                return '请求的资源未找到。';
            case 500:
                return '服务器内部错误，请稍后重试。';
            case 503:
                return '服务暂时不可用，请稍后重试。';
            default:
                if (status >= 400 && status < 500) {
                    return `客户端错误 (${status})，请检查您的请求。`;
                } else if (status >= 500) {
                    return `服务器错误 (${status})，请稍后重试或联系管理员。`;
                } else {
                    return `请求失败 (${status})。`;
                }
        }
    }

    async function queryFlash(
        queryWord: string,
        querySentence: string,
        frontendHandler: FrontendHandler,
        requestId?: string
    ) {
        try {
            const { reader, decoder } = await guardStreamingResponse(
                call_get(`/api/query/flash?q=${encodeURIComponent(queryWord)}&context=${encodeURIComponent(querySentence)}`, requestId),
                [], requestId,
            );

            if (reader && decoder) {
                await readStream(reader, decoder, frontendHandler);
            }
        } catch (error) {
            if (!isAbortError(error)) {
                console.error('Error in queryFlash:', error);
            }
        }
    }

    async function queryThinking(
        queryWord: string,
        querySentence: string,
        enableDeepThinking: number,
        frontendHandler: FrontendHandler,
        requestId?: string
    ) {
        try {
            const { reader, decoder } = await guardStreamingResponse(
                call_get(`/api/query/thinking?q=${encodeURIComponent(queryWord)}&context=${encodeURIComponent(querySentence)}&deep=${enableDeepThinking}`, requestId),
                [], requestId,
            );

            if (reader && decoder) {
                await readStream(reader, decoder, frontendHandler);
            }
        } catch (error) {
            if (!isAbortError(error)) {
                console.error('Error in queryThinking:', error);
            }
        }
    }

    async function extractModelTest(prompt: string, frontendHandler: FrontendHandler, requestId: string) {
        try {
            const { reader, decoder } = await guardStreamingResponse(
                call_post(`/api/extract-model-test`, { prompt }, requestId), [], requestId
            );

            if (reader && decoder) {
                await readStream(reader, decoder, frontendHandler);
            }
        } catch (error) {
            if (!isAbortError(error)) {
                console.error('Error in extractModelTest:', error);
            }
        }
    }

    async function queryFreq(query: string, page: number, requestId?: string): Promise<FreqResult> {
        const response = await guardJsonResponse(
            call_get(`/api/query/freq-info?q=${encodeURIComponent(query)}&page=${page}`, requestId),
            [404], requestId
        );

        if (response.status === 404) {
            return FreqResult.empty();
        }

        const result = new FreqResult(response);
        result.notes.sort((a, b) => {
            if (a.query.length !== b.query.length) {
                return a.query.length - b.query.length;
            }
            if (a.type !== b.type) {
                if (a.type === "textbook") {
                    return -1;
                }
                if (b.type === "textbook") {
                    return 1;
                }
            }
            return a.query.localeCompare(b.query);
        });
        return result;
    }

    async function sha256(password: string) {
        const array = await new Sha256(password).digest();
        return Array.from(new Uint8Array(array))
            .map((b) => b.toString(16).padStart(2, "0"))
            .join("");
    }

    async function register(email: string, password: string, updateToken: (token: string) => void, updateUser: (user: User) => void) {
        await guardJsonResponse(call_post("/api/auth/register", { email, password: await sha256(password) }), []);
        await login(email, password, updateToken, updateUser);
    }

    async function login(email: string, password: string, updateToken: (token: string) => void, updateUser: (user: User) => void) {
        const response = await guardJsonResponse(call_post("/api/auth/login", { email, password: await sha256(password) }), []);
        updateToken(response.token);
        updateUser(new User(response.user));
        await getUserInfo(updateUser, updateToken);
    }

    async function getBalanceDetails(page: number = 1) {
        const response = await guardJsonResponse(call_get(`/api/balance-details?page=${page}`), []);
        return await response;
    }

    async function adoptAnswer(context: string, query: string, answer: string) {
        await guardJsonResponse(call_post('/api/adopt-answer', { context, query, answer }), []);
    }

    async function getUserInfo(updateUser: (user: User) => void, updateToken: (token: string) => void) {
        const authResult = await guardJsonResponse(call_get("/api/user"), []);
        updateUser(new User(authResult.user));
        updateToken(authResult.token);
    }

    return {
        queryFlash,
        queryThinking,
        queryFreq,
        extractModelTest,
        getBalanceDetails,
        register,
        login,
        adoptAnswer,
        getUserInfo,
        abortRequest,
        isAbortError,
    }
})