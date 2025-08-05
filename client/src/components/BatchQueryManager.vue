<script lang="ts" setup>
import { onUnmounted, ref, computed } from 'vue'
import { useApiStore } from '@/stores/api'
import { useLocalStorage } from '@vueuse/core'
import { useQueryStore } from '@/stores/query'
import { useUserStore } from '@/stores/user'
import { useRouter } from 'vue-router'

interface BatchQueryTask {
    id: string
    query: string
    context: string
    answer: string
    status: 'pending' | 'running' | 'completed' | 'error'
}

const apiStore = useApiStore()
const router = useRouter()

const batchQueries = ref("");
const batchQueryTasks = useLocalStorage('EC_batchQueries', new Array<BatchQueryTask>());
const maxConcurrent = 5;

// 表格样式类
const tableClasses = computed(() => ({
    table: 'min-w-full divide-y divide-secondary-200',
    thead: 'bg-secondary-50',
    th: 'px-6 py-3 text-left text-xs font-medium text-secondary-500 uppercase tracking-wider',
    tbody: 'bg-white divide-y divide-secondary-200',
    td: 'px-6 py-4 whitespace-nowrap text-sm',
    queryCell: 'font-medium text-secondary-900',
    contextCell: 'text-secondary-500 max-w-xs truncate',
    answerCell: 'text-primary-600 font-bold max-w-md',
    answerContent: 'prose prose-sm',
    actionCell: 'space-x-2',
    deepConfirmButton: 'text-primary-600 hover:text-primary-900 shadow-sm px-1 rounded-md',
    removeTaskButton: 'text-danger-500 hover:text-danger-700 shadow-sm px-1 rounded-md'
}));

// 状态显示文本
const statusText = computed(() => ({
    pending: '等待中',
    running: '执行中',
    completed: '已完成',
    error: '错误'
}));

// 状态样式类
const statusClass = computed(() => (status: string) => {
    switch (status) {
        case 'pending':
            return 'text-secondary-600';
        case 'running':
            return 'text-warning-600';
        case 'completed':
            return 'text-primary-600';
        case 'error':
            return 'text-danger-600';
        default:
            return '';
    }
});

function executeBatchQueries() {
    const queries = batchQueries.value
        .split('\n')
        .map(q => q.trim())
        .filter(q => q.length > 0);

    // 清空之前的任务
    batchQueryTasks.value = [];

    // 创建任务列表
    queries.forEach((queryLine, index) => {
        // 解析形如"天下云集响应，赢（）粮而景从"的格式
        const regex = /^(.*)[（\(]\s*[）\)](.*)$/;
        const match = queryLine.match(regex);

        let query = "";
        let context = "";

        if (match) {
            const prefix = match[1];
            const suffix = match[2];
            context = prefix + suffix;
            query = prefix.slice(-1);
        } else {
            query = queryLine;
            context = queryLine;
        }

        const taskId = 'batch_' + Date.now() + '_' + index;
        batchQueryTasks.value.push({
            id: taskId,
            query: query,
            context: context,
            answer: '',
            status: 'pending'
        });
    });

    processBatchQueries();
}

async function processBatchQueries() {
    const pendingTasks = batchQueryTasks.value.filter(task => task.status === 'pending');
    if (pendingTasks.length === 0) return;

    const runningTasks = batchQueryTasks.value.filter(task => task.status === 'running');
    const slotsAvailable = maxConcurrent - runningTasks.length;

    const tasksToStart = pendingTasks.slice(0, slotsAvailable);
    tasksToStart.forEach(task => startBatchQueryTask(task));

    // 如果还有任务在等待，继续处理
    if (pendingTasks.length > slotsAvailable) {
        // 等待任意一个任务完成后再继续
        const checkInterval = setInterval(() => {
            const stillRunning = batchQueryTasks.value.filter(t => t.status === 'running').length;
            if (stillRunning < maxConcurrent) {
                clearInterval(checkInterval);
                processBatchQueries();
            }
        }, 100);
    }
}

function updateBatchQueryTask(taskId: string, answerChunk?: string, status?: 'pending' | 'running' | 'completed' | 'error') {
    const task = batchQueryTasks.value.find(t => t.id === taskId);
    if (!task) return;

    if (answerChunk) {
        task.answer += answerChunk;
    }

    if (status) {
        task.status = status;
    }
}

async function startBatchQueryTask(task: BatchQueryTask) {
    task.status = 'running';

    function get_frontend_handler(taskId: string) {
        return {
            updateExtract() { },
            updateFlash(contentChunk: string) {
                updateBatchQueryTask(taskId, contentChunk, undefined);
            },
            updateThinking() { },
            updateUsage() {
                updateBatchQueryTask(taskId, undefined, 'completed');
            },
            updateZdic() { },
        }
    }

    // 使用查询词和上下文执行查询，只进行浅层查询
    apiStore.queryFlash(task.query, task.context, get_frontend_handler(task.id), task.id);
}

const removeBatchQueryTask = (taskId: string) => {
    const taskIndex = batchQueryTasks.value.findIndex(t => t.id === taskId);
    if (taskIndex !== -1) {
        const task = batchQueryTasks.value[taskIndex];
        if (task.status === 'running') {
            apiStore.abortRequest(task.id);
        }
        batchQueryTasks.value.splice(taskIndex, 1);
    }
}

const clearBatchQueryTasks = () => {
    const ids = batchQueryTasks.value.map(task => task.id);
    ids.forEach(id => removeBatchQueryTask(id));
    batchQueryTasks.value = [];
}

function deepConfirm(query: string, context: string) {
    const queryStore = useQueryStore();
    queryStore.querySentence = context;
    queryStore.queryIndex.clear();
    const index = context.indexOf(query)
    for (let i = 0; i < query.length; i++) {
        queryStore.queryIndex.add(index + i);
    }
    const userStore = useUserStore();
    if (userStore.deepThinking === 0) {
        userStore.deepThinking = 1;
    }
    queryStore.query();
    router.push('/query');
}

onUnmounted(() => {
    batchQueryTasks.value.forEach(task => apiStore.abortRequest(task.id));
})
</script>

<template>
    <div class="bg-white rounded-lg shadow-md p-6 mb-6">
        <h2 class="text-xl font-semibold mb-4">批量问答器</h2>
        <div class="space-y-4">
            <div>
                <textarea v-model="batchQueries"
                    class="w-full px-3 py-2 border border-secondary-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
                    rows="5" placeholder="每行输入一个查询，例如：天下云集响应，赢（）粮而景从" required></textarea>
            </div>
            <div class="flex justify-between">
                <button @click="executeBatchQueries"
                    class="bg-secondary-600 hover:bg-secondary-700 text-white px-4 py-2 rounded-md transition-colors"
                    :disabled="!batchQueries.trim()">
                    执行查询
                </button>
                <button @click="clearBatchQueryTasks"
                    class="bg-danger-600 hover:bg-danger-700 text-white px-4 py-2 rounded-md transition-colors"
                    :disabled="!batchQueryTasks.length">
                    清空结果
                </button>
            </div>
        </div>

        <div v-if="batchQueryTasks.length > 0" class="mt-6">
            <h3 class="text-lg font-medium mb-3">查询结果</h3>
            <div class="overflow-x-auto">
                <table :class="tableClasses.table">
                    <thead :class="tableClasses.thead">
                        <tr>
                            <th scope="col" :class="tableClasses.th">
                                查询字</th>
                            <th scope="col" :class="tableClasses.th">
                                上下文</th>
                            <th scope="col" :class="tableClasses.th">
                                答案</th>
                            <th scope="col" :class="tableClasses.th">
                                状态</th>
                            <th scope="col" :class="tableClasses.th">
                                操作</th>
                        </tr>
                    </thead>
                    <tbody :class="tableClasses.tbody">
                        <tr v-for="task in batchQueryTasks" :key="task.id">
                            <td :class="[tableClasses.td, tableClasses.queryCell]">{{ task.query
                            }}</td>
                            <td :class="[tableClasses.td, tableClasses.contextCell]">{{ task.context }}</td>
                            <td :class="[tableClasses.td, tableClasses.answerCell]">
                                <div :class="tableClasses.answerContent">{{ task.answer }}</div>
                            </td>
                            <td :class="[tableClasses.td, statusClass(task.status)]">
                                {{ statusText[task.status as keyof typeof statusText] }}
                            </td>
                            <td :class="[tableClasses.td, tableClasses.actionCell]">
                                <div class="flex gap-2">
                                    <button @click="deepConfirm(task.query, task.context)"
                                        :class="tableClasses.deepConfirmButton">
                                        深度确认
                                    </button>
                                    <button @click="removeBatchQueryTask(task.id)"
                                        :class="tableClasses.removeTaskButton">
                                        删除
                                    </button>
                                </div>
                            </td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>
    </div>
</template>