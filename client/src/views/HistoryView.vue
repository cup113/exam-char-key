<script setup lang="ts">
import { ref } from 'vue';
import { ToolbarRoot, ToolbarButton } from 'reka-ui';
import type { HistoryRecord } from '@/stores/types';
import { useHistoryStore } from '@/stores/history';
import ExportIcon from '@/components/icons/ExportIcon.vue';
import DeleteIcon from '@/components/icons/DeleteIcon.vue';
import CheckAllIcon from '@/components/icons/CheckAllIcon.vue';
import SelectBackIcon from '@/components/icons/SelectBackIcon.vue';
import SelectForwardIcon from '@/components/icons/SelectForwardIcon.vue';

const historyStore = useHistoryStore();
const selectedRecords = ref<HistoryRecord[]>([]);

const export_selected = () => {
  historyStore.exportHistory(selectedRecords.value);
};

const delete_selected = () => {
  if (selectedRecords.value.length === 0) {
    return;
  }
  if (!confirm(`确定要删除选中的 ${selectedRecords.value.length} 条记录吗？`)) {
    return;
  }
  historyStore.deleteHistory(selectedRecords.value);
  selectedRecords.value.splice(0, selectedRecords.value.length);
};

const select_all = () => {
  if (selectedRecords.value.length === historyStore.history.length) {
    selectedRecords.value.splice(0, selectedRecords.value.length);
    return;
  }
  selectedRecords.value.splice(0, selectedRecords.value.length, ...historyStore.history);
};

const select_old = () => {
  const newestIndex = Math.min.apply(undefined,
    selectedRecords.value.map(record => historyStore.history.findIndex(r => r.id === record.id))
  );
  selectedRecords.value.splice(0, selectedRecords.value.length, ...historyStore.history.slice(newestIndex));
}

const select_new = () => {
  const oldestIndex = Math.max.apply(undefined,
    selectedRecords.value.map(record => historyStore.history.findIndex(r => r.id === record.id))
      .filter(index => index !== -1)
  );
  selectedRecords.value.splice(0, selectedRecords.value.length, ...historyStore.history.slice(0, oldestIndex + 1));
}

const buttons = [
  { text: '导出选中', click: export_selected, icon: ExportIcon, className: 'bg-primary-600 hover:bg-primary-700' },
  { text: '删除选中', click: delete_selected, icon: DeleteIcon, className: 'bg-danger-600 hover:bg-danger-700' },
  { text: '全部选中', click: select_all, icon: CheckAllIcon, className: 'bg-primary-600 hover:bg-primary-700' },
  { text: '选择旧项', click: select_old, icon: SelectBackIcon, className: 'bg-secondary-600 hover:bg-secondary-700' },
  { text: '选择新项', click: select_new, icon: SelectForwardIcon, className: 'bg-primary-600 hover:bg-primary-700' },
];
</script>

<template>
  <main class="py-4 px-4 md:px-6 lg:px-8">
    <toolbar-root class="bg-white flex flex-col md:flex-row md:flex-wrap justify-center p-2 shadow-md rounded-md">
      <toolbar-button v-for="button in buttons" :key="button.text" @click="button.click" :class="button.className"
        :disabled="button.text !== '全部选中' && selectedRecords.length === 0"
        class="text-white py-2 px-4 cursor-pointer disabled:cursor-not-allowed">
        <Component :is="button.icon" class="inline-block mr-2" />
        <span>{{ button.text }}</span>
      </toolbar-button>
    </toolbar-root>
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3">
      <div v-for="record in historyStore.history" :key="record.id"
        class="flex p-3 rounded-lg gap-1 hover:bg-gray-50">
        <div class="flex items-center w-full">
          <input type="checkbox" v-model="selectedRecords" :value="record"
            class="form-checkbox h-5 w-5 mr-2 text-blue-500" />
          <div class="flex-grow">
            <div class="record-content flex-1 px-2 py-1">
              <div class="front-text text-gray-700" v-html="record.front"></div>
            </div>
            <input v-model="record.back" :placeholder="record.back" class="px-2 py-1 w-full border-b text-primary-800" />
          </div>
        </div>
      </div>
    </div>
  </main>
</template>
