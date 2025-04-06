<script setup lang="ts">
import { ref } from 'vue';
import { useQueryStore, type HistoryRecord } from '@/stores/query';

const queryStore = useQueryStore();
const selectedRecords = ref<HistoryRecord[]>([]);

const export_selected = () => {
  queryStore.export_history(selectedRecords.value);
};

const delete_selected = () => {
  if (selectedRecords.value.length === 0) {
    return;
  }
  if (!confirm(`确定要删除选中的 ${selectedRecords.value.length} 条记录吗？`)) {
    return;
  }
  queryStore.delete_history(selectedRecords.value);
  selectedRecords.value.splice(0, selectedRecords.value.length);
};
</script>

<template>
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
</template>
