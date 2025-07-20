<script setup lang="ts">
import QuickAnswer from '@/components/QuickAnswer.vue';
import ZdicExplanation from '@/components/ZdicExplanation.vue';
import DeepAnswer from '@/components/DeepAnswer.vue';
import PassageAnnotation from '@/components/PassageAnnotation.vue';
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
        <div class="w-xs lg:w-md">
          <PassageAnnotation v-for="(annotation, index) in queryStore.textAnnotations" :annotation="annotation"
            :key="index" :index="index">
          </PassageAnnotation>
        </div>
      </div>
      <ZdicExplanation></ZdicExplanation>
    </section>
  </main>
</template>
