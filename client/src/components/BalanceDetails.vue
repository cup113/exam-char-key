<script lang="ts" setup>
import { ref, onMounted } from 'vue';
import { useApiStore } from '@/stores/api';
import { add_sep } from '@/stores/utils';

interface BalanceDetail {
    id: string;
    created: string;
    delta: number;
    remaining: number;
    reason: string;
}

const apiStore = useApiStore();

const balanceDetails = ref<BalanceDetail[]>([]);
const currentPage = ref(1);
const totalPages = ref(1);
const loading = ref(false);

async function fetchBalanceDetails(page: number = 1) {
    loading.value = true;
    try {
        const response = await apiStore.getBalanceDetails(page);
        balanceDetails.value = response.items;
        totalPages.value = response.totalPages;
        currentPage.value = page;
    } catch (error) {
        console.error('Failed to fetch balance details:', error);
    } finally {
        loading.value = false;
    }
}

function formatDate(dateString: string) {
    const date = new Date(dateString);
    return date.toLocaleString('zh-CN');
}

function getDeltaClass(delta: number) {
    return delta > 0 ? 'text-green-600' : 'text-red-600';
}

function getDeltaText(delta: number) {
    return delta > 0 ? `+${add_sep(delta)}` : `-${add_sep(-delta)}`;
}

onMounted(() => {
    fetchBalanceDetails();
});
</script>

<template>
    <div class="ec-standard-card">
        <div class="justify-center">余额明细</div>

        <div v-if="loading" class="text-center py-4">
            加载中...
        </div>

        <div v-else>
            <div v-if="balanceDetails.length === 0" class="text-center py-4 text-secondary-500">
                暂无余额明细记录
            </div>

            <div v-else>
                <div class="space-y-3">
                    <div v-for="detail in balanceDetails" :key="detail.id"
                        class="border-b border-secondary-200 pb-3 last:border-0 last:pb-0">
                        <div class="flex justify-between items-center">
                            <div>
                                <div class="font-medium">{{ detail.reason }}</div>
                                <div class="text-sm text-secondary-500">{{ formatDate(detail.created) }}</div>
                            </div>
                            <div class="text-right">
                                <div class="font-medium" :class="getDeltaClass(detail.delta)">
                                    {{ getDeltaText(detail.delta) }}
                                </div>
                                <div class="text-sm text-secondary-500">余额: {{ add_sep(detail.remaining) }}</div>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="flex justify-between items-center mt-4">
                    <button @click="fetchBalanceDetails(currentPage - 1)" :disabled="currentPage <= 1"
                        class="px-3 py-1 rounded bg-gray-200 disabled:opacity-50">
                        上一页
                    </button>

                    <span class="text-sm">
                        第 {{ currentPage }} 页，共 {{ totalPages }} 页
                    </span>

                    <button @click="fetchBalanceDetails(currentPage + 1)" :disabled="currentPage >= totalPages"
                        class="px-3 py-1 rounded bg-gray-200 disabled:opacity-50">
                        下一页
                    </button>
                </div>
            </div>
        </div>
    </div>
</template>