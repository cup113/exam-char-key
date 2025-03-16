<script setup lang="ts">
import { RouterLink, RouterView } from 'vue-router';
import { NavigationMenuRoot, NavigationMenuItem, NavigationMenuList } from 'reka-ui';

</script>

<template>
  <header class="flex items-center justify-center gap-4 p-2 border-b border-b-green-800 mb-8">
    <img alt="Vue logo" class="logo" src="@/assets/logo.svg" width="32" height="32" />
    <div>
      <h1 class="text-xl font-semibold">Exam Char Key</h1>
    </div>
    <NavigationMenuRoot>
      <NavigationMenuList>
        <NavigationMenuItem>
          <RouterLink to="/">Home</RouterLink>
        </NavigationMenuItem>
      </NavigationMenuList>
    </NavigationMenuRoot>
  </header>

  <RouterView />
</template>
