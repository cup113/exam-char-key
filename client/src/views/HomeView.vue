<script setup lang="ts">
import { useQueryStore } from '@/stores/query';
import PassageAnnotation from '@/components/PassageAnnotation.vue';
import { computed, ref } from 'vue';

const queryStore = useQueryStore();
const word = ref(queryStore.queryWord);

const iframeSrc = computed(() => {
  return `https://zdic.net/hans/${queryStore.queryWord}`;
})
</script>

<template>
  <main>
    <section class="flex justify-center items-center gap-2 text-center">
      <input type="text" class="rounded-lg border border-gray-500 text-center p-1 w-60" v-model="queryStore.querySentence">
      <input type="text" class="rounded-lg border border-gray-500 text-center p-1 w-16" v-model="word">
      <button @click="queryStore.query(word)" class="bg-blue-500 text-white p-1 rounded-lg">Search</button>
    </section>
    <section class="flex items-start justify-center">
      <section class="w-96 flex flex-col">
        <PassageAnnotation v-for="(_, index) in queryStore.textAnnotations" :key="index" :index="index" />
      </section>
      <section>
        <iframe :src="iframeSrc" frameborder="0" width="500" height="500"></iframe>
        <div>{{ queryStore.aiInstantResponse }}</div>
      </section>
    </section>
  </main>
</template>
