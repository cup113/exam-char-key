<script setup lang="ts">
import { useQueryStore } from '@/stores/query';
import PassageAnnotation from '@/components/PassageAnnotation.vue';
import { ref, watch } from 'vue';

const queryStore = useQueryStore();
const queryIndex = ref(new Set<number>());

watch(() => queryStore.querySentence, (newSentence, oldSentence) => {
  if (newSentence !== oldSentence) {
    queryIndex.value.clear();
    if (newSentence.length <= 2 && newSentence.length >= 1) {
      queryIndex.value.add(0);
      if (newSentence.length === 2) {
        queryIndex.value.add(1);
      }
    }
  }
})

function toggleIndex(index: number) {
  if (queryIndex.value.has(index)) {
    queryIndex.value.delete(index);
  } else {
    queryIndex.value.add(index);
  }
  queryStore.queryWord = Array.from(queryIndex.value).sort().map(i => queryStore.querySentence[i]).join();
}
</script>

<template>
  <main>
    <section class="flex flex-col gap-2">
      <div class="text-center">
        <input type="text" class="rounded-lg border border-gray-500 text-center p-1 w-96"
          v-model="queryStore.querySentence" placeholder="请输入要翻译词语的上下文">
      </div>
      <div class="flex justify-center items-center gap-4">
        <div class="flex">
          <div v-for="word, i in queryStore.querySentence" class="cursor-pointer rounded-md hover:bg-gray-100 px-1 py-0"
            :class="{ 'bg-green-100': queryIndex.has(i), 'hover:bg-green-200': queryIndex.has(i) }"
            @click="toggleIndex(i)">{{ word }}</div>
        </div>
        <button @click="queryStore.query()"
          class="bg-blue-500 hover:bg-blue-600 active:bg-blue-700 text-white p-1 rounded-lg px-2">搜索</button>
      </div>
    </section>
    <section class="flex items-start justify-center gap-2">
      <div class="flex flex-col gap-4">
        <div class="w-96 min-h-24 px-4 py-2 shadow-lg flex flex-col gap-2">
          <h2 class="text-2xl font-bold text-center">AI 快速回答</h2>
          <p class="text-center text-xl font-bold bg-green-200 mx-auto px-4 rounded-xl" v-show="queryStore.instantStructured.answer">
            {{ queryStore.instantStructured.answer }}
            <span class="text-lg font-mono" v-show="!isNaN(queryStore.instantStructured.conf)"> ({{
              queryStore.instantStructured.conf }})</span>
          </p>
          <p class="text-gray-500 text-sm indent-4" v-show="queryStore.instantStructured.think">{{
            queryStore.instantStructured.think }}</p>
          <p class="indent-4" v-show="queryStore.instantStructured.explain">
            {{ queryStore.instantStructured.explain }}
          </p>
        </div>
        <div class="w-96 min-h-24 px-4 py-2 shadow-lg flex flex-col gap-2">
          <h2 class="text-2xl font-bold text-center">汉典基本解释</h2>
          <ol class="indent-4">
            <li v-for="item, i in queryStore.zdicResponse.basic_explanations">
              {{ i + 1 }}. {{ item }}
            </li>
          </ol>
          <h2 v-if="queryStore.zdicResponse.detailed_explanations.length" class="text-2xl font-bold text-center">汉典详细解释
          </h2>
          <ol class="detail flex flex-col gap-1 indent-4">
            <li v-for="item in queryStore.zdicResponse.detailed_explanations" v-html="item"></li>
          </ol>
        </div>
      </div>
      <section class="flex flex-col gap-4 w-48 md:w-60 lg:w-96">
        <div class="min-h-24 px-4 py-2 shadow-lg flex flex-col gap-2">
          <h2 class="text-2xl font-bold text-center">AI 深度回答</h2>
          <div class="text-center text-xl font-bold bg-green-200 mx-auto px-4 rounded-xl">
            <p v-for="answer in queryStore.thoughtStructured.answers">
              <span>{{ answer.answer }}</span>
              <span class="font-mono text-lg" v-show="answer.conf && !isNaN(answer.conf)"> ({{ answer.conf }})</span>
            </p>
          </div>
          <p class="text-gray-500 text-sm indent-4" v-show="queryStore.thoughtStructured.analysis">{{
            queryStore.thoughtStructured.analysis }}</p>
          <div class="indent-4">
            <div v-for="candidate in queryStore.thoughtStructured.candidates">
              <strong>{{ candidate }}</strong> / {{ queryStore.thoughtStructured.filter[candidate] }}
            </div>
          </div>
        </div>
        <section class="w-full flex flex-col">
          <PassageAnnotation v-for="(_, index) in queryStore.textAnnotations" :key="index" :index="index" />
        </section>
      </section>
    </section>
  </main>
</template>

<style>
.detail li:nth-child(1) {
  display: none;
}

.detail .cino {
  color: green;
  font-weight: bolder;
  font-size: 0.875rem;
}

.detail .encs {
  color: green;
  font-size: 0.75rem;
  font-family: Georgia, 'Times New Roman', Times, serif;
}

.detail .diczx1,
.detail .diczx2,
.detail .smcs {
  color: rgb(87, 87, 87);
  font-size: 0.875rem;
}
</style>
