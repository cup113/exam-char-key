<script setup lang="ts">
import { useQueryStore } from '@/stores/query';
import PassageAnnotation from '@/components/PassageAnnotation.vue';
import { computed, ref } from 'vue';
import { ProgressRoot, ProgressIndicator } from 'reka-ui';

const queryStore = useQueryStore();
const word = ref(queryStore.queryWord);

const iframeSrc = computed(() => {
  return `https://zdic.net/hans/${queryStore.queryWord}`;
});

const confidence = computed(() => {
  const val = parseInt(queryStore.instantStructured.confidence);
  return isNaN(val) ? 0 : (val * 10);
});
</script>

<template>
  <main>
    <section class="flex justify-center items-center gap-2 text-center my-8">
      <input type="text" class="rounded-lg border border-gray-500 text-center p-1 w-60"
        v-model="queryStore.querySentence">
      <input type="text" class="rounded-lg border border-gray-500 text-center p-1 w-16" v-model="word">
      <button @click="queryStore.query(word)" class="bg-blue-500 text-white p-1 rounded-lg">Search</button>
    </section>
    <section class="flex items-start justify-center gap-2">
      <div class="flex flex-col gap-4">
        <pre
          class="w-96 min-h-24 px-4 py-2 shadow-lg text-center text-wrap break-words">{{ queryStore.aiInstantResponse }}</pre>
        <iframe :src="iframeSrc" frameborder="0" width="384" height="600"></iframe>
      </div>
      <section class="flex flex-col gap-4 w-48 md:w-60 lg:w-96">
        <pre class="w-full min-h-60 px-4 py-2 shadow-lg text-wrap break-words">{{ queryStore.aiThoughtResponse }}</pre>
        <section class="w-full flex flex-col">
          <PassageAnnotation v-for="(_, index) in queryStore.textAnnotations" :key="index" :index="index" />
        </section>
      </section>
    </section>
  </main>
</template>
