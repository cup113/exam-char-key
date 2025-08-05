<script lang="ts" setup>
import { NavigationMenuRoot, NavigationMenuItem, NavigationMenuList } from 'reka-ui';
import SearchIcon from './icons/SearchIcon.vue';
import HistoryIcon from './icons/HistoryIcon.vue';
import SettingsIcon from './icons/SettingsIcon.vue';
import AboutIcon from './icons/AboutIcon.vue';

const links = [
  { name: '搜索', to: '/query', icon: SearchIcon },
  { name: '历史', to: '/history', icon: HistoryIcon },
  { name: '设置', to: '/settings', icon: SettingsIcon },
  { name: '关于', to: '/about', icon: AboutIcon },
]
</script>

<template>
    <NavigationMenuRoot class="fixed bottom-0 w-full p-2 bg-primary-200 md:right-4 md:bottom-4 md:w-auto md:rounded-xl">
        <NavigationMenuList class="flex md:flex-col items-center justify-center gap-4">
            <NavigationMenuItem v-for="link in links" :key="link.to"
                class="rounded-lg text-secondary-700 hover:text-warning-700 px-2 py-1 font-bold">
                <RouterLink :to="link.to" class="rounded-xl flex items-center flex-col" :class="{'text-primary-700': $route.path.startsWith(link.to)}">
                    <Component :is="link.icon" class="w-10 h-10"></Component>
                    <div>{{ link.name }}</div>
                </RouterLink>
            </NavigationMenuItem>
        </NavigationMenuList>
    </NavigationMenuRoot>
</template>
