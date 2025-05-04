<script setup lang="ts">
import SearchBar from '@/components/SearchBar.vue';
import QuickAnswer from '@/components/QuickAnswer.vue';
import ZdicExplanation from '@/components/ZdicExplanation.vue';
import DeepAnswer from '@/components/DeepAnswer.vue';
import PassageAnnotation from '@/components/PassageAnnotation.vue';
import { useQueryStore } from '@/stores/query';

const queryStore = useQueryStore();
</script>

<template>
  <main class="flex flex-col gap-4">
    <SearchBar />
    <div class="flex justify-center items-start gap-2">
      <section class="flex flex-col gap-2">
        <div class="flex flex-col justify-center items-center gap-4 w-96">
          <QuickAnswer />
          <DeepAnswer />
        </div>
      </section>
      <section class="flex flex-col items-start justify-center gap-2 w-72 md:w-96">
        <section class="w-full flex flex-col gap-4">
          <ZdicExplanation />
          <PassageAnnotation v-for="(_, index) in queryStore.textAnnotations" :key="index" :index="index" />
        </section>
      </section>
    </div>
  </main>
</template>
