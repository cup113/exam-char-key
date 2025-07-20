<script lang="ts" setup>
import { useQueryStore } from '@/stores/query';
import { computed } from 'vue';
import { stress_keyword } from '@/stores/utils';

const props = defineProps<{
    index: number,
}>();

const queryStore = useQueryStore();

const passage = computed(() => {
    return queryStore.textAnnotations[props.index];
});

const processedKeyword = computed(() => {
    return stress_keyword(passage.value.get_keyword(), queryStore.displayWord);
});

const processedContext = computed(() => {
    return stress_keyword(passage.value.context, queryStore.displayWord)
});

const processedDetail = computed(() => {
    return stress_keyword(passage.value.core_detail, queryStore.displayWord)
});

</script>

<template>
    <div class="rounded-lg shadow px-4 py-2">
        <div class="font-bold text-center">{{ passage.name_passage }}</div>
        <div class="indent-4" v-html="processedContext"></div>
        <div>【<span class="text-primary-700" v-html="processedKeyword"></span>】<span v-html="processedDetail"></span></div>
    </div>
</template>
