<script lang="ts" setup>
import { useQueryStore } from '@/stores/query';
import { computed } from 'vue';
import { stress_keyword } from '@/stores/utils';
import type { Note } from '@/stores/types';

const props = defineProps<{
    note: Note,
}>();

const queryStore = useQueryStore();

const processedKeyword = computed(() => {
    return stress_keyword(props.note.context, queryStore.lastQuery.word);
});

const processedContext = computed(() => {
    return stress_keyword(props.note.context, queryStore.lastQuery.word);
});

const processedAnswer = computed(() => {
    return stress_keyword(props.note.answer, queryStore.lastQuery.word);
});

</script>

<template>
    <div class="rounded-lg shadow px-4 py-2">
        <div class="indent-4" v-html="processedContext"></div>
        <div>【<span class="text-warning-700" v-html="processedKeyword"></span>】<span v-html="processedAnswer"></span></div>
    </div>
</template>
