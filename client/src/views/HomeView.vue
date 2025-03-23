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
</script>

<template>
  <main>
    <section class="flex justify-center items-center gap-2 text-center my-8">
      <input type="text" class="rounded-lg border border-gray-500 text-center p-1 w-60"
        v-model="queryStore.querySentence">
      <input type="text" class="rounded-lg border border-gray-500 text-center p-1 w-16" v-model="word">
      <button @click="queryStore.query(word)"
        class="bg-blue-500 hover:bg-blue-600 active:bg-blue-700 text-white p-1 rounded-lg px-2">Search</button>
    </section>
    <section class="flex items-start justify-center gap-2">
      <div class="flex flex-col gap-4">
        <div class="w-96 min-h-24 px-4 py-2 shadow-lg flex flex-col gap-2">
          <p class="text-gray-500 text-sm indent-4" v-show="queryStore.instantStructured.think">{{
            queryStore.instantStructured.think }}</p>
          <p class="text-center text-xl font-bold" v-show="queryStore.instantStructured.answer">
            {{ queryStore.instantStructured.answer }}
            <span class="text-lg font-mono" v-show="!isNaN(queryStore.instantStructured.conf)"> ({{
              queryStore.instantStructured.conf }})</span>
          </p>
          <p class="indent-4" v-show="queryStore.instantStructured.explain">
            {{ queryStore.instantStructured.explain }}
          </p>
        </div>
        <div class="w-96 min-h-24 px-4 py-2 shadow-lg flex flex-col gap-2">
          <h2 v-if="queryStore.zdicResponse.basic_explanations.length" class="text-2xl font-bold">基本解释</h2>
          <ol class="indent-4">
            <li v-for="item, i in queryStore.zdicResponse.basic_explanations">
              {{ i + 1 }}. {{ item }}
            </li>
          </ol>
        </div>
      </div>
      <section class="flex flex-col gap-4 w-48 md:w-60 lg:w-96">
        <div class="min-h-24 px-4 py-2 shadow-lg flex flex-col gap-2">
          <p class="text-gray-500 text-sm indent-4" v-show="queryStore.thoughtStructured.analysis">{{
            queryStore.thoughtStructured.analysis }}</p>
          <div class="indent-4">
            <div v-for="candidate in queryStore.thoughtStructured.candidates">
              <strong>{{ candidate }}</strong> / {{ queryStore.thoughtStructured.filter[candidate] }}
            </div>
          </div>
          <div class="text-center text-xl font-bold">
            <p v-for="answer in queryStore.thoughtStructured.answers">
              <span>{{ answer.answer }}</span>
              <span class="font-mono text-lg" v-show="answer.conf && !isNaN(answer.conf)"> ({{ answer.conf }})</span>
            </p>
          </div>
        </div>
        <section class="w-full flex flex-col">
          <PassageAnnotation v-for="(_, index) in queryStore.textAnnotations" :key="index" :index="index" />
        </section>
      </section>
    </section>
  </main>
</template>
