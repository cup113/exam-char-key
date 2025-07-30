import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueDevTools from 'vite-plugin-vue-devtools'
import tailwindcss from '@tailwindcss/vite';
import { VitePWA } from 'vite-plugin-pwa';

const vitePWA = VitePWA({
  registerType: 'autoUpdate',
  devOptions: {
    enabled: true
  },
  workbox: {
    runtimeCaching: [
      {
        urlPattern: ({ request }) => request.destination === 'script',
        handler: 'StaleWhileRevalidate',
        options: {
          cacheName: 'scripts',
          expiration: {
            maxEntries: 20,
            maxAgeSeconds: 7 * 24 * 60 * 60,
          }
        }
      }
    ],
  },
  manifest: {
    name: 'Exam Char Key',
    short_name: 'CharKey',
    description: '古代汉字解释与AI辅助学习平台',
    theme_color: '#4F46E5',
    icons: [
      {
        src: 'public/favicon-192x192.png',
        sizes: '192x192',
        type: 'image/png'
      },
      {
        src: 'public/favicon-512x512.png',
        sizes: '512x512',
        type: 'image/png'
      }
    ]
  }
});

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    vue(),
    vueDevTools(),
    tailwindcss(),
    vitePWA,
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    },
  },
  server: {
    proxy: {
      '/api': 'http://localhost:4122',
    }
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          vue: ['vue', 'vue-router', 'pinia', '@vueuse/core'],
          ui: ['reka-ui'],
        }
      }
    }
  }
})