<script setup lang="ts">
import { RouterLink, RouterView } from 'vue-router'
</script>

<template>
  <header class="flex items-center justify-center gap-2">
    <img alt="Vue logo" class="logo" src="@/assets/logo.svg" width="32" height="32" />
    <div>
      <h1 class="text-xl font-semibold">Exam Char Key</h1>
    </div>
    <nav>
      <RouterLink to="/">Home</RouterLink>
      <RouterLink to="/about">About</RouterLink>
    </nav>
  </header>

  <RouterView />
</template>
