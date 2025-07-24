<script lang="ts" setup>
import { useQueryStore } from '@/stores/query';
import { stress_keyword } from '@/stores/utils';
import { computed } from 'vue';
import { FreqResult } from '@/stores/types';

import FrequencyIcon from './icons/FrequencyIcon.vue';

const queryStore = useQueryStore();

const freqInfo = computed(() => {
    return queryStore.freqInfo ?? new FreqResult({
        "word": "",
        "textbook_freq": 0,
        "guwen_freq": 0,
        "query_freq": 0,
        "notes": [],
    });
});
</script>

<template>
    <div class="ec-standard-card">
        <div>
            <FrequencyIcon />
            <strong class="ml-2">词频分析</strong>
        </div>
        <div v-if="freqInfo.word">
            <div>
                <p>总频率指标：<strong class="text-warning-600">{{ freqInfo.get_freq() }}</strong></p>
                <p>其中教科书：{{ freqInfo.textbook_freq }}，古文语料库：{{ freqInfo.guwen_freq }}，用户查询：{{ freqInfo.query_freq }}</p>
            </div>
            <div>
                <div v-for="note in freqInfo.notes.slice(0, 20)">
                    <div class="flex flex-col text-center items-center bg-primary-100 shadow-md py-2 my-2 px-2">
                        <p v-html="stress_keyword(note.context.trim(), note.get_keyword())"
                                class="text-secondary-700">
                        </p>
                        <p class="w-full text-primary-700 font-bold">{{ note.detail }}</p>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>
