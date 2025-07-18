export type JsonType<T> = T extends Date ? string
    : T extends Function | undefined | symbol ? never
    : T extends object ? { [K in keyof T]: JsonType<T[K]> } : T;

export class PassageAnnotation {
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

export type TextAnnotationResult = JsonType<PassageAnnotation>[];

export type ResponseChunk = { type: "text", result: TextAnnotationResult } | { type: "ai-instant", result: AiResult } | { type: "ai-thought", result: AiResult } | { type: "ai-usage", result: AiUsageResult } | { type: "zdic", result: ZdicResult } | { type: "search-original", result: AiResult };

export interface FrontendHandler {
    updateTextAnnotations: (annotations: PassageAnnotation[]) => void;
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
