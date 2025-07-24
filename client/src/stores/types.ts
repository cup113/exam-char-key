export type JsonType<T> = T extends Date ? string
    : T extends Function | undefined | symbol ? never
    : T extends object ? { [K in keyof T]: JsonType<T[K]> } : T;

export class Note {
    public context: string;
    public core_detail: string;
    public detail: string;
    public index_range: [number, number];
    public name_passage: string;

    constructor(raw: Omit<JsonType<Note>, "get_keyword">) {
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

    public get_freq() {
        return this.textbook_freq * 6 + this.guwen_freq + this.query_freq * 3;
    }
}

export interface HistoryRecord {
    id: string;
    level: string;
    front: string;
    back: string;
    userModifiedBack?: string; // 用户修改的答案
    additions: never[];
    createdAt: string;
}

export interface AiResult {
    content: string;
    stopped: boolean;
}
export interface AiUsageResult {
    prompt_tokens: number;
    input_unit_price: number;
    completion_tokens: number;
    output_unit_price: number;
}

export interface ZdicResult {
    basic_explanations: string[];
    detailed_explanations: string[];
    phrase_explanations: string[];
}

export type ResponseChunk = { type: "freq", result: JsonType<FreqResult> } | { type: "ai-instant", result: AiResult } | { type: "ai-thought", result: AiResult } | { type: "ai-usage", result: AiUsageResult } | { type: "zdic", result: ZdicResult } | { type: "search-original", result: AiResult };

export interface FrontendHandler {
    updateFreqInfo: (freqResult: FreqResult) => void;
    updateInstant: (contentChunk: string) => void;
    updateThought: (contentChunk: string) => void;
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
