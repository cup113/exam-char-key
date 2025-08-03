<script lang="ts" setup>
import { ref, onUnmounted } from 'vue'
import { marked } from 'marked'
import { useApiStore } from '@/stores/api'
import { useLocalStorage } from '@vueuse/core'

interface Task {
    id: string
    prompt: string
    content: string
    status: 'pending' | 'running' | 'completed' | 'error'
}

const apiStore = useApiStore()

const tasks = useLocalStorage('EC_tasks', new Array<Task>());
const newPrompt = ref("");

const renderMarkdown = (content: string) => {
    return marked.parse(content)
}

function addTask() {
    const promptExcerpt = newPrompt.value.replace(/\n|\s/g, '').slice(0, 15);
    const taskId = 'task_' + Date.now() + "_" + Math.random().toString(36).substring(2, 5) + "_" + promptExcerpt + "_" + newPrompt.value.length;

    const task: Task = {
        id: taskId,
        prompt: newPrompt.value,
        content: '',
        status: 'pending'
    }

    tasks.value.push(task);
    startTask(task);

    newPrompt.value = '';
}

function updateTask(_task: Task, deltaContent?: string, status?: 'pending' | 'running' | 'completed' | 'error') {
    const task = tasks.value.find(t => t.id === _task.id);
    if (!task) {
        return;
    }

    if (deltaContent) {
        task.content += deltaContent;
    }

    if (status) {
        task.status = status;
    }
}

async function startTask(task: Task) {
    task.status = 'running';

    function get_frontend_handler(task: Task) {
        return {
            updateExtract(contentChunk: string) {
                updateTask(task, contentChunk, undefined);
            },
            updateFlash() { },
            updateSearchOriginal() { },
            updateThinking() { },
            updateUsage() {
                updateTask(task, undefined, 'completed');
            },
            updateZdic() { },
        }
    }
    apiStore.extractModelTest(task.prompt, get_frontend_handler(task), task.id);
}

const removeTask = (taskId: string) => {
    const taskIndex = tasks.value.findIndex(t => t.id === taskId)
    if (taskIndex !== -1) {
        const task = tasks.value[taskIndex]
        if (task.status === 'running') {
            apiStore.abortRequest(task.id);
        }
        tasks.value.splice(taskIndex, 1)
    }
}

const clearTasks = () => {
    const ids = tasks.value.map(task => task.id);
    ids.forEach(id => removeTask(id));
}

onUnmounted(() => {
    tasks.value.forEach(task => {
        apiStore.abortRequest(task.id);
    })
})
</script>

<template>
    <div class="max-w-6xl mx-auto px-4 py-8">
        <h1 class="text-2xl font-bold mb-6">模卷数据提取器</h1>

        <!-- 任务输入区域 -->
        <div class="bg-white rounded-lg shadow-md p-6 mb-6">
            <h2 class="text-xl font-semibold mb-4">添加新任务</h2>
            <div class="space-y-4">
                <div>
                    <textarea v-model="newPrompt"
                        class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
                        rows="3" placeholder="输入模卷内容" required></textarea>
                </div>
                <div class="flex justify-between">
                    <button @click="addTask"
                        class="bg-primary-600 hover:bg-primary-700 text-white px-4 py-2 rounded-md transition-colors"
                        :disabled="!newPrompt.trim()">
                        添加任务
                    </button>
                    <button @click="clearTasks"
                        class="bg-danger-600 hover:bg-danger-700 text-white px-4 py-2 rounded-md transition-colors"
                        :disabled="!tasks.length">
                        清空任务
                    </button>
                </div>
            </div>
        </div>

        <!-- 任务列表 -->
        <div class="grid grid-cols-1 gap-6">
            <div v-for="task in tasks" :key="task.id" class="bg-white rounded-lg shadow-md overflow-hidden">
                <div class="p-4 border-b border-gray-200">
                    <div class="flex justify-between items-center">
                        <h3 class="font-semibold">任务 {{ task.id }}</h3>
                        <button @click="removeTask(task.id)" class="text-danger-500 hover:text-danger-700">
                            删除
                        </button>
                    </div>
                </div>
                <div class="p-4">
                    <div class="h-64 overflow-y-auto border border-gray-200 rounded-md p-2 bg-gray-50">
                        <div class="prose" v-html="renderMarkdown(task.content)"></div>
                    </div>
                    <div class="mt-2 text-sm text-secondary-500">
                        状态: {{ task.status }}
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<style scoped>
.prose :deep(p) {
    margin: 0 0 0.5em 0;
}

.prose :deep(pre) {
    background-color: #f5f5f5;
    padding: 0.5rem;
    border-radius: 0.25rem;
    overflow-x: auto;
}

.prose :deep(code) {
    background-color: #f5f5f5;
    padding: 0.125rem 0.25rem;
    border-radius: 0.125rem;
}
</style>