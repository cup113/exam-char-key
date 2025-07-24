<script setup lang="ts">
import QuickAnswer from '@/components/QuickAnswer.vue';
import ZdicExplanation from '@/components/ZdicExplanation.vue';
import DeepAnswer from '@/components/DeepAnswer.vue';
import FreqDisplay from '@/components/FreqDisplay.vue';
import AddText from '@/components/AddText.vue';
import TapSearch from '@/components/TapSearch.vue';
import { useQueryStore } from '@/stores/query';

const queryStore = useQueryStore();
</script>

<template>
  <main class="flex flex-col items-center gap-4 pb-40">
    <AddText></AddText>
    <TapSearch></TapSearch>
    <section class="flex flex-col md:flex-row gap-2 py-4">
      <div class="flex flex-col gap-2">
        <QuickAnswer></QuickAnswer>
        <DeepAnswer></DeepAnswer>
        <FreqDisplay></FreqDisplay>
      </div>
      <ZdicExplanation></ZdicExplanation>
    </section>
  </main>
</template>
