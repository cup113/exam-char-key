<script setup lang="ts">
import { RouterLink, RouterView } from 'vue-router';
import { NavigationMenuRoot, NavigationMenuItem, NavigationMenuList } from 'reka-ui';

const links = [
  { name: '查询', to: '/' },
  { name: '历史记录', to: '/history' },
]
</script>

<template>
  <header class="flex items-center justify-center gap-4 py-4">
    <img alt="Vue logo" class="logo" src="/favicon.ico" width="32" height="32" />
    <div>
      <h1 class="text-xl font-semibold"><RouterLink to="/">Exam Char Key</RouterLink></h1>
    </div>
    <NavigationMenuRoot>
      <NavigationMenuList class="flex">
        <NavigationMenuItem v-for="link in links" :key="link.to" class="text-blue-800 rounded-lg hover:bg-blue-50 px-2 py-1 font-bold">
          <RouterLink :to="link.to">{{ link.name }}</RouterLink>
        </NavigationMenuItem>
      </NavigationMenuList>
    </NavigationMenuRoot>
  </header>

  <RouterView />
</template>
