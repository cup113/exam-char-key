<script setup lang="ts">
import { computed, ref } from 'vue';
import { useQueryStore } from '@/stores/query';
import { Editor, EditorContent, BubbleMenu } from '@tiptap/vue-3';
import { useLocalStorage } from '@vueuse/core';
import { format_front } from '@/stores/utils';
import StarterKit from '@tiptap/starter-kit';

const text = useLocalStorage('EC_text', '');
const queryStore = useQueryStore();
const editor = new Editor({
  extensions: [
    StarterKit,
  ],
  content: text.value,
  onUpdate() {
    text.value = editor.getHTML();
  }
});
const contextStart = ref<number | null>(null);
const contextEnd = ref<number | null>(null);
const showMenu = ref(false);
const menuPosition = ref({ x: 0, y: 0 });
const finalAnswer = ref('');
const queryDisplay = computed(() => {
  if (contextStart.value === null || contextEnd.value === null) {
    return '';
  }
  return format_front(queryStore.querySentence, queryStore.queryIndex);
})

const setContext = () => {
  if (editor) {
    const { from, to } = editor.state.selection;
    contextStart.value = from;
    contextEnd.value = to;
    showMenu.value = false;
    queryStore.querySentence = editor.view.state.doc.textBetween(contextStart.value, contextEnd.value);
  }
};

const runQuery = () => {
  if (contextStart.value !== null) {
    const { from, to } = editor.state.selection;
    queryStore.queryWord = editor.view.state.doc.textBetween(from, to);

    queryStore.queryIndex.clear();
    for (let i = from; i < to; i++) {
      queryStore.queryIndex.add(i - contextStart.value);
    }
    editor.chain().focus().setBold().run();
    queryStore.query();
  }
  showMenu.value = false;
};
</script>

<template>
  <section class="flex flex-col items-center gap-2">
    <div class="rounded-lg border px-2 py-1 border-gray-500 min-w-96 max-w-[48rem]">
      <div>
        <BubbleMenu :tippy-options="{ duration: 100 }" :editor="editor"
          class="shadow-md rounded-md px-2 py-1 bg-white flex gap-2">
          <button @click="setContext" class="hover:bg-blue-50 rounded-md px-1">上下文</button>
          <button :disabled="contextStart === null || contextEnd === null" @click="runQuery"
            class="hover:bg-blue-50 rounded-md px-1 disabled:text-gray-500 disabled:cursor-no-drop">查询</button>
        </BubbleMenu>
      </div>
      <EditorContent :editor="editor" />
    </div>
    <div class="text-sm text-gray-500">已用量：{{ (queryStore.usage / 1e7).toFixed(4) }}</div>
    <div>查询内容：<span v-html="queryDisplay || '[请输入]'"></span></div>
    <div v-if="showMenu" class="absolute" :style="{ left: `${menuPosition.x}px`, top: `${menuPosition.y}px` }">
      <button class="bg-blue-500 hover:bg-blue-600 active:bg-blue-700 text-white p-1 rounded-lg px-2 mr-2"
        @click="setContext">上下文</button>
      <button class="bg-green-500 hover:bg-green-600 active:bg-green-700 text-white p-1 rounded-lg px-2"
        :disabled="contextStart === null || contextEnd === null" @click="runQuery">
        查询
      </button>
    </div>
    <div class="flex justify-center items-center gap-2" v-show="!queryStore.currentRecorded">
      <span>最终答案是：</span>
      <input type="text" v-model="finalAnswer" class="rounded-lg border border-gray-500 text-center w-48">
      <button class="bg-green-700 text-white rounded-lg px-2 py-1"
        @click="queryStore.adopt_answer(finalAnswer)">采纳</button>
    </div>
  </section>
</template>

<style>
.ProseMirror-focused {
  outline: none;
}
</style>
