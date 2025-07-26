import { createRouter, createWebHashHistory } from 'vue-router'
import IntroView from '@/views/IntroView.vue';
import QueryView from '../views/QueryView.vue';
import HistoryView from '@/views/HistoryView.vue';
import SettingsView from '@/views/SettingsView.vue';

const router = createRouter({
  history: createWebHashHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: IntroView,
    },
    {
      path: '/query',
      name: 'query',
      component: QueryView,
    },
    {
      path: '/history',
      name: 'history',
      component: HistoryView,
    },
    {
      path: '/settings',
      name: 'settings',
      component: SettingsView,
    },
  ],
})

export default router
