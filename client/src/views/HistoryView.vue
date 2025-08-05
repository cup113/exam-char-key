<script setup lang="ts">
import { ref, computed } from 'vue';
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
const showExportMenu = ref(false);
const exportButtonRef = ref<InstanceType<typeof ToolbarButton> | null>(null);

// 数据处理逻辑
const historyData = computed(() => {
  return historyStore.history;
});

const exportOptions = [
  { format: 'json' as const, label: 'JSON 格式 (.json)' },
  { format: 'word' as const, label: 'Word 文档 (.docx)' },
  { format: 'apkg' as const, label: 'Anki 牌组 (.apkg)' }
];

const toolbarButtons = [
  {
    text: '删除选中',
    action: delete_selected,
    icon: DeleteIcon,
    className: 'bg-danger-600 hover:bg-danger-700',
    condition: () => selectedRecords.value.length > 0
  },
  {
    text: '全部选中',
    action: select_all,
    icon: CheckAllIcon,
    className: 'bg-primary-600 hover:bg-primary-700',
    condition: () => true
  },
  {
    text: '选择旧项',
    action: select_old,
    icon: SelectBackIcon,
    className: 'bg-secondary-600 hover:bg-secondary-700',
    condition: () => selectedRecords.value.length > 0
  },
  {
    text: '选择新项',
    action: select_new,
    icon: SelectForwardIcon,
    className: 'bg-primary-600 hover:bg-primary-700',
    condition: () => selectedRecords.value.length > 0
  },
];

// 业务逻辑方法
function export_selected(format: 'json' | 'word' | 'apkg') {
  historyStore.exportHistory(selectedRecords.value, format);
  showExportMenu.value = false;
}

function toggleExportMenu() {
  if (selectedRecords.value.length === 0) return;
  showExportMenu.value = !showExportMenu.value;
}

function delete_selected() {
  if (selectedRecords.value.length === 0) {
    return;
  }
  if (!confirm(`确定要删除选中的 ${selectedRecords.value.length} 条记录吗？`)) {
    return;
  }
  historyStore.deleteHistory(selectedRecords.value);
  selectedRecords.value.splice(0, selectedRecords.value.length);
}

function select_all() {
  if (selectedRecords.value.length === historyData.value.length) {
    selectedRecords.value.splice(0, selectedRecords.value.length);
    return;
  }
  selectedRecords.value.splice(0, selectedRecords.value.length, ...historyData.value);
}

function select_old() {
  const newestIndex = Math.min.apply(undefined,
    selectedRecords.value.map(record => historyData.value.findIndex(r => r.id === record.id))
  );
  selectedRecords.value.splice(0, selectedRecords.value.length, ...historyData.value.slice(newestIndex));
}

function select_new() {
  const oldestIndex = Math.max.apply(undefined,
    selectedRecords.value.map(record => historyData.value.findIndex(r => r.id === record.id))
      .filter(index => index !== -1)
  );
  selectedRecords.value.splice(0, selectedRecords.value.length, ...historyData.value.slice(0, oldestIndex + 1));
}

function isRecordSelected(record: HistoryRecord) {
  return selectedRecords.value.some(selected => selected.id === record.id);
}

function toggleRecordSelection(record: HistoryRecord) {
  const index = selectedRecords.value.findIndex(selected => selected.id === record.id);
  if (index > -1) {
    selectedRecords.value.splice(index, 1);
  } else {
    selectedRecords.value.push(record);
  }
}

function handleDocumentClick(e: MouseEvent) {
  const el = e.target;
  if (!(el instanceof HTMLElement) || el === null) {
    showExportMenu.value = false;
  } else if (exportButtonRef.value && !exportButtonRef.value.$el.contains(el) && !el.closest('.export-menu')) {
    showExportMenu.value = false;
  }
}

document.addEventListener('click', handleDocumentClick);
</script>

<template>
  <main class="py-4 px-4 md:px-6 lg:px-8">
    <toolbar-root class="bg-white flex flex-col md:flex-row md:flex-wrap justify-center p-2 shadow-md rounded-md">
      <div class="relative w-full md:w-auto">
        <toolbar-button ref="exportButtonRef" @click="toggleExportMenu"
          class="bg-primary-600 hover:bg-primary-700 text-white py-2 px-4 cursor-pointer disabled:cursor-not-allowed flex items-center w-full justify-center"
          :disabled="selectedRecords.length === 0">
          <ExportIcon class="inline-block mr-2" />
          <span>导出选中</span>
        </toolbar-button>

        <div v-if="showExportMenu" class="export-menu absolute z-10 mt-1 w-48 bg-white rounded-md shadow-lg py-1">
          <button v-for="option in exportOptions" :key="option.format"
            @click="() => export_selected(option.format)"
            class="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100">
            {{ option.label }}
          </button>
        </div>
      </div>

      <toolbar-button v-for="button in toolbarButtons" :key="button.text" @click="button.action"
        :class="button.className" :disabled="!button.condition()"
        class="text-white py-2 px-4 cursor-pointer disabled:cursor-not-allowed flex items-center justify-center">
        <Component :is="button.icon" class="inline-block mr-2" />
        <span>{{ button.text }}</span>
      </toolbar-button>
    </toolbar-root>

    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3">
      <div v-for="record in historyData" :key="record.id" class="flex p-3 rounded-lg gap-1 hover:bg-gray-50">
        <div class="flex items-center w-full">
          <input type="checkbox" :checked="isRecordSelected(record)" @change="() => toggleRecordSelection(record)"
            class="form-checkbox h-5 w-5 mr-2 text-blue-500" />
          <div class="flex-grow">
            <div class="record-content flex-1 px-2 py-1">
              <div class="front-text text-gray-700" v-html="record.front"></div>
            </div>
            <input v-model="record.back" :placeholder="record.back"
              class="px-2 py-1 w-full border-b text-primary-800" />
          </div>
        </div>
      </div>
    </div>
  </main>
</template>
