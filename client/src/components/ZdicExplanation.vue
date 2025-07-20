<script setup lang="ts">
import { useQueryStore } from '@/stores/query';
import { stress_keyword } from '@/stores/utils';
import DictionaryIcon from './icons/DictionaryIcon.vue';
import { computed } from 'vue';
const queryStore = useQueryStore();

const showHeading = computed(() => {
    return {
        basic: queryStore.zdicResponse.basic_explanations.length > 0,
        detailed: queryStore.zdicResponse.detailed_explanations.length > 0,
        phrase: queryStore.zdicResponse.phrase_explanations.length > 0,
    }
})

function format_basic(item: string) {
    return stress_keyword(item.replace(/[\~～]/g, queryStore.displayWord), queryStore.displayWord)
}

interface ZDicDetail {
    pinyin: string;
    partOfSpeech: string;
    senses: ZDicDetailSense[];
}

interface ZDicDetailSense {
    content: string;
    examples: string[];
}

function process_detail(lines: string[]) {
    const HEADINGS = ["详细字义", "词性变化", "常用词组"];
    const MARK = "◎";

    const details = new Array<ZDicDetail>();
    let activeDetail: ZDicDetail | null = null;

    lines.map(line => line.trim()).forEach(line => {
        if (HEADINGS.includes(line)) {
            return;
        }
        if (line.includes(MARK)) {
            const pinyin = line.match(/[a-zA-Z]{1,2}[aeiouüāáǎàīíǐìūúǔǔēéěèōóǒòěěèmng]{1,5}/)?.[0] ?? '';
            activeDetail = {
                pinyin,
                partOfSpeech: "",
                senses: [],
            };
            details.push(activeDetail);
        } else if (line.match(/〈(.{1,2})〉/)) {
            if (!activeDetail) {
                console.warn("Part of speech detected while activeDetail is null.");
                return;
            }
            activeDetail.partOfSpeech = line.match(/〈(.{1,2})〉/)?.[1] ?? "";
        } else if (line.match(/——(.*?)《(.*?)》/)) {
            if (!activeDetail) {
                console.warn("Example detected while activeDetail is null.");
                return;
            }
            if (!activeDetail.senses.length) {
                console.warn("Example detected while senses are empty.");
                return;
            }
            activeDetail.senses[activeDetail.senses.length - 1].examples.push(
                stress_keyword(line, queryStore.displayWord)
            );
        } else {
            if (!activeDetail) {
                console.warn("Senses detected while activeDetail is null.");
                return;
            }
            const number_match = line.match(/\((\d+)\)/);
            let content = line;
            if (number_match) {
                content = line.replace(/\((\d+)\)/, "").trim();
            }
            const example_match = content.match(/又如\:(.*)/);
            if (example_match?.index === 0 || !content.match(/\[[a-zA-Z\s,;]+\]/)) {
                // Lines like 又如:淹息(逗留休息);淹回(徘徊;逗留);淹泊(停留;滞留)
                if (!activeDetail.senses.length) {
                    console.warn("Example detected while senses are empty.");
                    return;
                }
                activeDetail.senses[activeDetail.senses.length - 1].examples.push(
                    stress_keyword(content, queryStore.displayWord)
                );
                return;
            }
            content = content.replace(/^[\u4e00-\u9fa5\;“”，。]+/, s => `<strong>${s}</strong>`)
            content = content.replace(/\[[a-zA-Z\s,;]+\]/, s => `<span class="zdic-english">${s}</span>`);
            content = content.replace(/如\:(.*)/, s => `<span class="zdic-example">${stress_keyword(s, queryStore.displayWord)}</span>`);
            activeDetail.senses.push({
                content,
                examples: [],
            });
        }
    });

    return details;
}

const details = computed(() => process_detail(queryStore.zdicResponse.detailed_explanations));

</script>

<template>
    <div class="relative w-xs lg:w-md min-h-24 px-4 py-4 shadow-lg flex flex-col gap-2">
        <div class="absolute flex items-center font-bold text-sm -top-2 -left-0 p-1 rounded-lg bg-primary-500">
            <dictionary-icon></dictionary-icon>
            汉典
        </div>
        <h3 class="text-lg font-bold text-center" v-if="showHeading.basic">基本解释</h3>
        <ol class="indent-4">
            <li v-for="item, i in queryStore.zdicResponse.basic_explanations" :key="i">
                <span class="font-mono text-sm mr-2">{{ i + 1 }}.</span>
                <span v-html="format_basic(item)"></span>
            </li>
        </ol>
        <h3 v-if="showHeading.detailed" class="text-lg font-bold text-center">详细解释</h3>
        <ol
            class="detail flex flex-col gap-1 [& .zdic-example]:text-secondary-500 [& .zdic-example]:text-sm [& .zdic-english]:text-primary-600 [& .zdic-english]:text-xs">
            <li v-for="detail, i in details">
                <p class="mb-2">
                    <strong class="mr-2 text-lg">
                        <span class="font-mono">{{ i + 1 }}.</span>
                        &lt;{{ detail.partOfSpeech }}&gt;
                    </strong>
                    <span class="zdic-english">{{ detail.pinyin }}</span>
                </p>
                <div class="pl-4">
                    <div v-for="sense, j in detail.senses" class="mb-2">
                        <p class="mb-1">
                            <span class="font-mono mr-1 text-sm">({{ j + 1 }})</span>
                            <span v-html="sense.content"></span>
                        </p>
                        <div class="pl-4 indent-4">
                            <p v-for="example in sense.examples" class="zdic-example">
                                <span v-html="example"></span>
                            </p>
                        </div>
                    </div>
                </div>
            </li>
        </ol>
        <h2 v-if="showHeading.phrase" class="text-lg font-bold text-center">补充解释</h2>
        <ol class="flex flex-col gap-1 indent-4">
            <li v-for="item in queryStore.zdicResponse.phrase_explanations" v-html="item"></li>
        </ol>
    </div>
</template>

<style>
@reference "tailwindcss";

.zdic-english {
    @apply text-amber-600 text-sm;
}

.zdic-example {
    @apply text-stone-500 text-sm;
}
</style>
