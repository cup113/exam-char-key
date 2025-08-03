<script lang="ts" setup>
import ModelExtractorManager from '@/components/ModelExtractorManager.vue'
import BatchQueryManager from '@/components/BatchQueryManager.vue'
</script>

<template>
    <div class="max-w-6xl mx-auto px-4 py-8">
        <h1 class="text-2xl font-bold mb-6">模卷数据提取器</h1>
        <ModelExtractorManager />
        <BatchQueryManager />
    </div>
</template>
