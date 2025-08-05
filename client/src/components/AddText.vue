<script lang="ts" setup>
import { DialogRoot, DialogClose, DialogContent, DialogOverlay, DialogPortal, DialogTitle, DialogTrigger } from 'reka-ui';
import DocumentAddIcon from './icons/DocumentAddIcon.vue';
import { useQueryStore } from '@/stores/query';
import { ref, watch } from 'vue';

const queryStore = useQueryStore();

const inputText = ref(queryStore.activeText);

watch(() => queryStore.activeText, () => {
    inputText.value = queryStore.activeText;
})
</script>

<template>
    <DialogRoot>
        <DialogTrigger as-child>
            <button
                class="rounded-lg text-lg cursor-pointer flex gap-2 bg-primary-600 text-white px-4 py-2 hover:bg-primary-700 mx-auto">
                <Component :is="DocumentAddIcon" class="w-6 h-6" />
                <span>添加/修改文本内容</span>
            </button>
        </DialogTrigger>

        <DialogPortal>
            <DialogOverlay class="fixed inset-0 bg-black/20" />
            <DialogContent
                class="fixed top-1/2 left-1/2 w-full max-w-md p-6 bg-white rounded-xl transform -translate-x-1/2 -translate-y-1/2 flex flex-col items-center gap-4">
                <DialogTitle class="text-xl font-semibold">添加文本</DialogTitle>
                <textarea name="text" rows="5" class="block w-full min-h-20 bg-secondary-200 p-2"
                    placeholder="请输入文言文文本……" v-model="inputText"></textarea>

                <div class="flex justify-around w-full">
                    <DialogClose>
                        <button class="text-white bg-primary-600 px-4 py-2 rounded-md hover:bg-primary-700">确定</button>
                    </DialogClose>
                    <DialogClose>
                        <button
                            class="text-white bg-secondary-400 px-4 py-2 rounded-md hover:bg-secondary-500">取消</button>
                    </DialogClose>
                </div>
            </DialogContent>
        </DialogPortal>
    </DialogRoot>
</template>
