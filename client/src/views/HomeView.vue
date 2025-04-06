<script setup lang="ts">
import { useQueryStore, type HistoryRecord } from '@/stores/query';
import PassageAnnotation from '@/components/PassageAnnotation.vue';
import { ref } from 'vue';

const queryStore = useQueryStore();

const selectedRecords = ref<HistoryRecord[]>([]);
const export_selected = () => {
  queryStore.export_history(selectedRecords.value);
};
const delete_selected = () => {
  if (!confirm(`确定要删除选中的${selectedRecords.value.length}条记录吗？`)) {
    return;
  }
  queryStore.delete_history(selectedRecords.value);
};
</script>

<template>
  <main>
    <section class="flex flex-col gap-2">
      <div class="text-center flex justify-center items-center gap-2">
        <input type="text" class="rounded-lg border border-gray-500 text-center p-1 w-96"
          v-model="queryStore.querySentence" placeholder="请输入要翻译词语的上下文">
        <span class="text-sm">已用量：{{ (queryStore.usage / 1e7).toFixed(4) }}</span>
      </div>
      <div class="flex justify-center items-center gap-4">
        <div class="flex">
          <div v-for="word, i in queryStore.querySentence" class="cursor-pointer rounded-md hover:bg-gray-100 px-1 py-0"
            :class="{ 'bg-green-100': queryStore.queryIndex.has(i), 'hover:bg-green-200': queryStore.queryIndex.has(i) }"
            @click="queryStore.toggle_index(i)">{{ word }}</div>
        </div>
        <button @click="queryStore.query()"
          class="bg-blue-500 hover:bg-blue-600 active:bg-blue-700 text-white p-1 rounded-lg px-2">搜索</button>
      </div>
    </section>
    <section class="flex items-start justify-center gap-2">
      <div class="flex flex-col gap-4">
        <div class="w-96 min-h-24 px-4 py-2 shadow-lg flex flex-col gap-2">
          <h2 class="text-2xl font-bold text-center">AI 快速回答</h2>
          <p class="text-center text-xl font-bold bg-green-200 mx-auto pl-4 rounded-xl"
            v-show="queryStore.instantStructured.answer">
            {{ queryStore.instantStructured.answer }}
            <span class="text-lg font-mono" v-show="!isNaN(queryStore.instantStructured.conf)"> ({{
              queryStore.instantStructured.conf }})</span>
            <button @click="queryStore.adopt_answer(queryStore.instantStructured.answer)"
              v-if="!queryStore.currentRecorded"
              class="bg-green-500 hover:bg-green-600 text-white font-bold py-1 px-2 rounded-xl ml-2">
              采用
            </button>
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
              <button @click="queryStore.adopt_answer(answer.answer)" v-if="!queryStore.currentRecorded"
                class="bg-green-500 hover:bg-green-600 text-white font-bold py-1 px-2 rounded-xl ml-2">
                采用
              </button>
            </p>
          </div>
          <p class="text-gray-500 text-sm indent-4" v-show="queryStore.thoughtStructured.think">{{
            queryStore.thoughtStructured.think }}</p>
          <div class="indent-4">
            <div v-for="candidate in queryStore.thoughtStructured.candidates">
              <strong>{{ candidate.answer }}</strong> / {{ candidate.explanation }}
            </div>
          </div>
        </div>
        <section class="w-full flex flex-col">
          <PassageAnnotation v-for="(_, index) in queryStore.textAnnotations" :key="index" :index="index" />
        </section>
        <section class="history-section p-4 bg-white rounded-lg shadow-md">
          <div class="history-header mb-4 flex justify-between items-center">
            <button @click="export_selected"
              class="bg-blue-500 hover:bg-blue-600 text-white font-bold py-1 px-2 rounded-xl">
              导出选中记录
            </button>
            <button @click="delete_selected"
              class="bg-red-500 hover:bg-red-600 text-white font-bold py-1 px-2 rounded-xl">
              删除选中记录
            </button>
          </div>
          <div>
            <div v-for="record in queryStore.history" :key="record.id"
              class="flex flex-col p-3 bg-white rounded-lg shadow-sm hover:bg-gray-50">
              <div class="flex items-center">
                <input type="checkbox" v-model="selectedRecords" :value="record"
                  class="form-checkbox h-4 w-4 mr-2 text-blue-500" />
                <div class="record-content flex-1">
                  <div class="front-text text-gray-700" v-html="record.front"></div>
                </div>
              </div>
              <div>
                <input v-model="record.userModifiedBack" :placeholder="record.back" class="px-2 py-1 w-full" />
              </div>
            </div>
          </div>
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
