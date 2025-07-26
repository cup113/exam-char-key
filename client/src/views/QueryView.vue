<script setup lang="ts">
import QuickAnswer from '@/components/QuickAnswer.vue';
import ZdicExplanation from '@/components/ZdicExplanation.vue';
import DeepAnswer from '@/components/DeepAnswer.vue';
import FreqDisplay from '@/components/FreqDisplay.vue';
import AddText from '@/components/AddText.vue';
import TapSearch from '@/components/TapSearch.vue';
import { useUserStore } from '@/stores/user';
import { useQueryStore } from '@/stores/query';

const userStore = useUserStore();
const queryStore = useQueryStore();
localStorage.setItem('EC_visited', 'true');
</script>

<template>
  <main class="flex flex-col items-center gap-4">
    <AddText></AddText>
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