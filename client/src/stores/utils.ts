import { PassageAnnotation, type ResponseChunk } from './types';
import type { FrontendHandler } from './types';

export function format_front(sentence: string, indices: Set<number>): string {
    const chars = Array.from(sentence);
    Array.from(indices).reverse().forEach(i => {
        chars[i] = `<strong>${chars[i]}</strong>`;
    });
    return chars.join('');
}

export function update_from_query(responseChunk: ResponseChunk, frontendHandler: FrontendHandler) {
    switch (responseChunk.type) {
        case "text":
            frontendHandler.updateTextAnnotations(responseChunk.result.map((raw) => new PassageAnnotation(raw)));
            break;
        case "ai-instant":
            frontendHandler.updateInstant(responseChunk.result.content);
            break;
        case "ai-thought":
            frontendHandler.updateThought(responseChunk.result.content);
            break;
        case 'ai-usage':
            frontendHandler.updateUsage(responseChunk.result);
            break;
        case "zdic":
            frontendHandler.updateZdic(responseChunk.result);
            break;
        case "search-original":
            frontendHandler.updateSearchOriginal(responseChunk.result.content);
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
