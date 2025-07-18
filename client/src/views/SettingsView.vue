<script lang="ts" setup>
import { useSettingsStore } from '@/stores/settings';
import { computed } from 'vue';

const settingsStore = useSettingsStore();

const usageDisplay = computed(() => {
    const promptTokensK = settingsStore.usageInfo.prompt_tokens / 1000;
    const promptPricePerK = settingsStore.usageInfo.prompt_price / 1e7 / (settingsStore.usageInfo.prompt_tokens / 1000) || 0;
    const completionTokensK = settingsStore.usageInfo.completion_tokens / 1000;
    const completionPricePerK = settingsStore.usageInfo.completion_price / 1e7 / (settingsStore.usageInfo.completion_tokens / 1000) || 0;
    const totalCost = (settingsStore.usageInfo.completion_price + settingsStore.usageInfo.prompt_price) / 1e7;

    return [
        { item: "输入 Token × 单价", value: `${promptTokensK.toFixed(2)}k * ${promptPricePerK.toFixed(4)}/k` },
        { item: "输出 Token × 单价", value: `${completionTokensK.toFixed(2)}k * ${completionPricePerK.toFixed(4)}/k` },
        { item: "历史消费成本 (RMB)", value: `${totalCost.toFixed(4)}` },
    ]
})
</script>

<template>
    <main class="p-4 flex flex-col items-center">
        <section class="w-xs lg:w-md">
            <h2 class="font-bold text-xl">AI 使用情况</h2>
            <div class="grid grid-cols-1 border-collapse">
                <div v-for="usage in usageDisplay" :key="usage.item" class="flex justify-between p-2 border-b">
                    <span>{{ usage.item }}</span>
                    <span class="font-mono font-bold text-primary-800">{{ usage.value }}</span>
                </div>
            </div>
        </section>
    </main>
</template>
