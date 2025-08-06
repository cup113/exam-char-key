<script setup lang="ts">
import QuickAnswer from '@/components/QuickAnswer.vue';
import ZdicExplanation from '@/components/ZdicExplanation.vue';
import DeepAnswer from '@/components/DeepAnswer.vue';
import FreqDisplay from '@/components/FreqDisplay.vue';
import AddText from '@/components/AddText.vue';
import TapSearch from '@/components/TapSearch.vue';
import { useUserStore } from '@/stores/user';
import { useQueryStore } from '@/stores/query';
import { useRouter } from 'vue-router';

const userStore = useUserStore();
const queryStore = useQueryStore();
const router = useRouter();
localStorage.setItem('EC_visited', 'true');

function goToBatch() {
  router.push('/batch');
}
</script>

<template>
  <main class="flex flex-col items-center gap-4">
    <div class="flex flex-col md:flex-row gap-4 items-center">
      <AddText></AddText>
      <div class="relative">
        <button @click="goToBatch"
          class="rounded-lg text-sm cursor-pointer flex gap-2 bg-secondary-600 text-white px-4 py-2 hover:bg-secondary-700">
          批量搜索
        </button>
      </div>
    </div>
    <TapSearch></TapSearch>
    <section class="flex flex-col md:flex-row gap-2 py-4" v-show="queryStore.lastQuery.word">
      <div class="flex flex-col gap-2">
        <QuickAnswer></QuickAnswer>
        <DeepAnswer v-show="userStore.deepThinking"></DeepAnswer>
        <FreqDisplay></FreqDisplay>
      </div>
      <ZdicExplanation></ZdicExplanation>
    </section>
  </main>
</template>