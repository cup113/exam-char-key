import { createRouter, createWebHashHistory } from 'vue-router'
import QueryView from '../views/QueryView.vue';
import HistoryView from '@/views/HistoryView.vue';
import SettingsView from '@/views/SettingsView.vue';

const router = createRouter({
  history: createWebHashHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      redirect: '/query',
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
