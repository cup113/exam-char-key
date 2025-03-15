<script lang="ts" setup>
import { useQueryStore } from '@/stores/query';
import { computed } from 'vue';

const props = defineProps<{
    index: number,
}>();

const queryStore = useQueryStore();

const passage = computed(() => {
    return queryStore.textAnnotations[props.index];
});

function replace_all(str: string, find: string, replace: string) {
    return str.replace(new RegExp(find, 'g'), replace);
}

const processedKeyword = computed(() => {
    return replace_all(passage.value.get_keyword(), queryStore.queryWord, `<strong>${queryStore.queryWord}</strong>`);
});

const processedContext = computed(() => {
    return replace_all(passage.value.context, queryStore.queryWord, `<strong>${queryStore.queryWord}</strong>`);
});

const processedDetail = computed(() => {
    return replace_all(passage.value.core_detail, queryStore.queryWord, `<strong>${queryStore.queryWord}</strong>`);
});

</script>

<template>
    <div class="rounded-lg shadow px-4 py-2">
        <div class="font-bold text-center">{{ passage.name_passage }}</div>
        <div class="indent-4" v-html="processedContext"></div>
        <div>【<span class="text-green-800" v-html="processedKeyword"></span>】 <span v-html="processedDetail"></span></div>
    </div>
</template>
