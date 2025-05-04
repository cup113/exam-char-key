import { PassageAnnotation, type ResponseChunk, type ZdicResult } from './types';
import type { Ref } from 'vue';

export function format_front(sentence: string, indices: Set<number>): string {
    const chars = Array.from(sentence);
    indices.forEach(i => {
        chars[i] = `<strong>${chars[i]}</strong>`;
    });
    return chars.join('');
}

export function update_from_query(
    responseChunk: ResponseChunk,
    textAnnotations: Ref<PassageAnnotation[]>,
    aiInstantResponse: Ref<string>,
    aiThoughtResponse: Ref<string>,
    usage: Ref<number>,
    zdicResponse: Ref<ZdicResult>
) {
    switch (responseChunk.type) {
        case "text":
            textAnnotations.value = responseChunk.result.map((raw) => new PassageAnnotation(raw));
            break;
        case "ai-instant":
            aiInstantResponse.value += responseChunk.result.content;
            break;
        case "ai-thought":
            aiThoughtResponse.value += responseChunk.result.content;
            break;
        case 'ai-usage':
            const usageResult = responseChunk.result;
            usage.value += usageResult.prompt_tokens * usageResult.input_unit_price + usageResult.completion_tokens * usageResult.output_unit_price;
            break;
        case "zdic":
            zdicResponse.value = responseChunk.result;
            break;
        default:
            console.error(`Unknown type: ${JSON.stringify(responseChunk)}`);
            break;
    }
}
