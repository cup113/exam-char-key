export type JsonType<T> = T extends Date ? string
    : T extends Function | undefined | symbol ? never
    : T extends Array<any> ? {
        [K in keyof T]: JsonType<T[K]>
    }
    : T extends object ? {
        [K in keyof T as T[K] extends Function | undefined | symbol ? never : K]: JsonType<T[K]>
    } : T;

export class Note {
    public context: string;
    public query: string;
    public answer: string;
    public type: "textbook" | "dataset" | "query";

    constructor(raw: Omit<JsonType<Note>, "get_keyword">) {
        this.context = raw.context;
        this.query = raw.query;
        this.answer = raw.answer;
        this.type = raw.type;
    }
}

export class FreqResultStat {
    query: string;
    freqTextbook: number;
    freqDataset: number;
    freqQuery: number;

    constructor(raw: Omit<JsonType<FreqResultStat>, "get_total_freq">) {
        this.query = raw.query;
        this.freqTextbook = raw.freqTextbook;
        this.freqDataset = raw.freqDataset;
        this.freqQuery = raw.freqQuery;
    }

    public get_total_freq() {
        return this.freqTextbook * 6 + this.freqDataset + this.freqQuery * 3;
    }
}

export class FreqResult {
    stat: FreqResultStat;
    notes: Note[];
    total_pages: number;

    constructor(raw: Omit<JsonType<FreqResult>, "get_freq">) {
        this.stat = new FreqResultStat(raw.stat);
        this.notes = raw.notes.map(note => new Note(note));
        this.total_pages = raw.total_pages;
    }

    public static empty() {
        return new FreqResult({
            stat: {
                query: "",
                freqTextbook: 0,
                freqDataset: 0,
                freqQuery: 0,
            },
            notes: [],
            total_pages: 1,
        });
    }
}

export interface BalanceDetail {
    id: string;
    user: string;
    amount: number;
    balance: number;
    description: string;
    created: string;
}

export class User {
    public id: string;
    public name: string;
    public email: string;
    public total_spent: number;
    public balance: number;
    public role: {
        id: string;
        name: string;
        daily_coins: number
    };

    constructor(raw: JsonType<User>) {
        this.id = raw.id;
        this.name = raw.name;
        this.email = raw.email;
        this.total_spent = raw.total_spent;
        this.balance = raw.balance;
        this.role = raw.role;
    }

    public static empty() {
        return new User({
            id: "",
            name: "",
            email: "",
            total_spent: 0,
            balance: 0,
            role: {
                id: "",
                name: "Guest",
                daily_coins: 0
            }
        })
    }
}

export interface HistoryRecord {
    id: string;
    level: string;
    front: string;
    back: string;
    additions: never[];
    createdAt: string;
}

export interface AiResult {
    content: string;
    stopped: boolean;
}

export interface AiUsageResult {
    prompt_tokens: number;
    completion_tokens: number;
}

export interface ZdicResult {
    basic_explanations: string[];
    detailed_explanations: string[];
    phrase_explanations: string[];
}

export type ResponseChunk = { type: "ai-flash", data: string } | { type: "ai-thinking", data: AiResult } | { type: "ai-usage", data: AiUsageResult } | { type: "zdic", data: ZdicResult } | { type: "search-original", data: AiResult };

export interface FrontendHandler {
    updateFlash: (contentChunk: string) => void;
    updateThinking: (contentChunk: string) => void;
    updateUsage: (usageResult: AiUsageResult) => void;
    updateZdic: (zdicResult: ZdicResult) => void;
    updateSearchOriginal: (contentChunk: string) => void;
}

export enum SearchTarget {
    None = "none",
    Sentence = "sentence",
    Paragraph = "paragraph",
    FullText = "full-text"
}
