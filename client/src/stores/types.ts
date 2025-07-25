export type JsonType<T> = T extends Date ? string
    : T extends Function | undefined | symbol ? never
    : T extends object ? { [K in keyof T]: JsonType<T[K]> } : T;

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

export class FreqResult {
    word: string;
    textbook_freq: number;
    guwen_freq: number;
    query_freq: number;
    notes: Note[];

    constructor(raw: Omit<JsonType<FreqResult>, "get_freq">) {
        this.word = raw.word;
        this.textbook_freq = raw.textbook_freq;
        this.guwen_freq = raw.guwen_freq;
        this.query_freq = raw.query_freq;
        this.notes = raw.notes.map(note => new Note(note));
    }

    public static empty() {
        return new FreqResult({
            word: "",
            textbook_freq: 0,
            guwen_freq: 0,
            query_freq: 0,
            notes: []
        });
    }

    public get_freq() {
        return this.textbook_freq * 6 + this.guwen_freq + this.query_freq * 3;
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
    public role: string;

    constructor(raw: JsonType<User>) {
        this.id = raw.id;
        this.name = raw.name;
        this.email = raw.email;
        this.total_spent = raw.total_spent;
        this.balance = raw.balance;
        this.role = raw.role;
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

export type ResponseChunk = { type: "freq", data: JsonType<FreqResult> } | { type: "ai-flash", data: string } | { type: "ai-thinking", data: AiResult } | { type: "ai-usage", data: AiUsageResult } | { type: "zdic", data: ZdicResult } | { type: "search-original", data: AiResult };

export interface FrontendHandler {
    updateFreqInfo: (freqResult: FreqResult) => void;
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
