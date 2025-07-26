<script lang="ts" setup>
import { onMounted } from 'vue';
import { useUserStore } from '@/stores/user';
import { add_sep } from '@/stores/utils';

import MyPagination from './MyPagination.vue';

const userStore = useUserStore();
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

function handlePageChange(page: number) {
    userStore.fetchBalanceDetails(page);
}
</script>

<template>
    <div class="ec-standard-card">
        <div class="justify-center">余额明细</div>

        <div v-if="userStore.bdLoading" class="text-center py-4">
            加载中...
        </div>

        <div v-else>
            <div v-if="userStore.balanceDetails.length === 0" class="text-center py-4 text-secondary-500">
                暂无余额明细记录
            </div>

            <div v-else>
                <div class="space-y-3">
                    <div v-for="detail in userStore.balanceDetails" :key="detail.id"
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

                <MyPagination
                  :current-page="userStore.bdCurrentPage"
                  :total-pages="userStore.bdTotalPages"
                  @page-changed="handlePageChange" />
            </div>
        </div>
    </div>
</template>