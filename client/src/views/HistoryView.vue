<script setup lang="ts">
import { ref } from 'vue';
import type { HistoryRecord } from '@/stores/types';
import { useQueryStore } from '@/stores/query';

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

const select_all = () => {
  if (selectedRecords.value.length === queryStore.history.length) {
    selectedRecords.value.splice(0, selectedRecords.value.length);
    return;
  }
  selectedRecords.value.splice(0, selectedRecords.value.length, ...queryStore.history);
};

const select_old = () => {
  const newestIndex = Math.min.apply(undefined,
    selectedRecords.value.map(record => queryStore.history.findIndex(r => r.id === record.id))
  );
  selectedRecords.value.splice(0, selectedRecords.value.length, ...queryStore.history.slice(newestIndex));
}

const select_new = () => {
  const oldestIndex = Math.max.apply(undefined,
    selectedRecords.value.map(record => queryStore.history.findIndex(r => r.id === record.id))
      .filter(index => index !== -1)
  );
  selectedRecords.value.splice(0, selectedRecords.value.length, ...queryStore.history.slice(0, oldestIndex + 1));
}

// 定义按钮配置数组，使用 className 且只保留颜色差异部分
const buttons = [
  { text: '导出选中记录', click: export_selected, className: 'bg-blue-500 hover:bg-blue-600' },
  { text: '删除选中记录', click: delete_selected, className: 'bg-red-500 hover:bg-red-600' },
  { text: '全选', click: select_all, className: 'bg-green-500 hover:bg-green-600' },
  { text: '选中旧记录', click: select_old, className: 'bg-gray-500 hover:bg-gray-600' },
  { text: '选中新记录', click: select_new, className: 'bg-gray-500 hover:bg-gray-600' },
];
</script>

<template>
  <main class="p-4">
    <div class="history-header mb-4 flex gap-2 items-center">
      <button v-for="(button, index) in buttons" :key="index" @click="button.click"
        class="text-white py-1 px-2 rounded-xl cursor-pointer disabled:cursor-no-drop" :class="button.className"
        :disabled="button.text !== '全选' && selectedRecords.length === 0">
        {{ button.text }}
      </button>
    </div>
    <div>
      <div v-for="record in queryStore.history" :key="record.id"
        class="flex flex-col p-3 bg-white rounded-lg shadow-sm hover:bg-gray-50">
        <div class="flex items-center">
          <input type="checkbox" v-model="selectedRecords" :value="record"
            class="form-checkbox h-5 w-5 mr-2 text-blue-500" />
          <div class="record-content flex-1">
            <div class="front-text text-gray-700" v-html="record.front"></div>
          </div>
          <input v-model="record.userModifiedBack" :placeholder="record.back" class="px-2 py-1 w-48" />
        </div>
      </div>
    </div>
  </main>
</template>
