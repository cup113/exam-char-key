import { FreqResult, type ResponseChunk } from './types';
import type { FrontendHandler } from './types';

export function stress_keyword(sentence: string, keyword: string): string {
    const indices = new Set<number>();
    let start = 0;
    while (true) {
        start = sentence.indexOf(keyword, start);
        if (start === -1) {
            break;
        }
        for (let i = 0; i < keyword.length; i++) {
            indices.add(start + i);
        }
        start += keyword.length;
    }
    return format_front(sentence, indices);
}

export function format_front(sentence: string, indices: Set<number>): string {
    const chars = Array.from(sentence);
    Array.from(indices).reverse().forEach(i => {
        chars[i] = `<strong>${chars[i]}</strong>`;
    });
    const DUPLICATE_TAG_REGEX = /\<\/strong\>\<strong\>/g
    return chars.join('').replace(DUPLICATE_TAG_REGEX, '');
}

export function add_sep(num: number): string {
    if (num < 0) {
        return `-${add_sep(-num)}`;
    }
    let result = "";
    while (true) {
        const last_three = (num % 1000).toString();
        num = Math.floor(num / 1000);
        if (!(num > 0)) {
            result = last_three + result;
            break;
        } else {
            result = "," + last_three.padStart(3, "0") + result;
        }
    }
    return result;
}

export function update_from_query(responseChunk: ResponseChunk, frontendHandler: FrontendHandler) {
    switch (responseChunk.type) {
        case "freq":
            frontendHandler.updateFreqInfo(new FreqResult(responseChunk.data));
            break;
        case "ai-flash":
            frontendHandler.updateFlash(responseChunk.data);
            break;
        case "ai-thinking":
            frontendHandler.updateThinking(responseChunk.data.content);
            break;
        case 'ai-usage':
            frontendHandler.updateUsage(responseChunk.data);
            break;
        case "zdic":
            frontendHandler.updateZdic(responseChunk.data);
            break;
        case "search-original":
            frontendHandler.updateSearchOriginal(responseChunk.data.content);
            break;
        default:
            console.error(`Unknown type: ${JSON.stringify(responseChunk)}`);
            break;
    }
}

export interface AiThoughtStructured {
    think: string;
    explain: string;
    answers: string[];
}

export function parse_ai_thought_response(response: string): AiThoughtStructured {
    const lines = response.split("\n");

    const result: AiThoughtStructured = {
        think: '',
        explain: '',
        answers: new Array<string>(),
    };

    let area: 'think' | 'explain' | 'answers' | '' = '';

    lines.forEach(line => {
        let startIndex = 0;
        let endIndex = line.length;

        if (line.startsWith("<think>")) {
            area = 'think';
            startIndex = line.indexOf('>') + 1;
        } else if (line.startsWith("<explain>")) {
            area = 'explain';
            startIndex = line.indexOf('>') + 1;
        } else if (line.startsWith("<answers>")) {
            area = 'answers';
            startIndex = line.indexOf('>') + 1;
        }

        if (line.endsWith("</think>") || line.endsWith("</explain>") || line.endsWith("</answers>")) {
            endIndex = line.lastIndexOf('<');
        }

        if (area) {
            const text = line.substring(startIndex, endIndex);
            if (area === 'answers') {
                result.answers.push(...(text.trim() ? text.split("；") : []));
            } else {
                result[area] += text + '\n';
            }
        }

        if (endIndex !== line.length) {
            area = '';
        }
    });

    return result;
}
