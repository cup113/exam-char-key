<script setup lang="ts">
import { RouterLink, RouterView } from 'vue-router';
import NavigationMenu from './components/NavigationMenu.vue';
</script>

<template>
  <div class="bg-secondary-200 min-h-screen">
  <header class="flex items-center justify-center gap-4 py-4">
    <img alt="Vue logo" class="logo" src="/favicon.ico" width="32" height="32" />
    <div>
      <h1 class="text-xl font-semibold text-primary-800"><RouterLink to="/">Exam Char Key</RouterLink></h1>
    </div>
  </header>

  <RouterView />
  <NavigationMenu />
  </div>
</template>
