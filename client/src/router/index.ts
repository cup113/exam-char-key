import { createRouter, createWebHashHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue';
import HistoryView from '@/views/HistoryView.vue';

const router = createRouter({
  history: createWebHashHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: HomeView,
    },
    {
      path: '/history',
      name: 'history',
      component: HistoryView,
    }
  ],
})

export default router
