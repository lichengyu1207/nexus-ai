import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { fileURLToPath, URL } from 'node:url'

export default defineConfig(({ mode }) => {
  const isDev = mode === 'development'
  
  return {
    plugins: [react()],
    resolve: {
      alias: {
        '@': fileURLToPath(new URL('./src', import.meta.url)),
      },
    },
    server: {
      port: 5173,
      proxy: {
        '/api': {
          target: 'http://localhost:8000',
          changeOrigin: true,
        },
      },
    },
    build: {
      target: 'es2015',
      minify: isDev ? false : 'terser',
      terserOptions: isDev ? undefined : {
        compress: {
          drop_console: true,
          drop_debugger: true,
          pure_funcs: ['console.log', 'console.info', 'console.debug'],
        },
      },
      rollupOptions: {
        output: {
          manualChunks: (id) => {
            if (id.includes('node_modules')) {
              if (id.includes('react/') || id.includes('react-dom/') || id.includes('scheduler')) {
                return 'react-vendor';
              }
              if (id.includes('react-router-dom')) {
                return 'router';
              }
              if (id.includes('@headlessui') || id.includes('@heroicons') || id.includes('lucide-react')) {
                return 'ui-lib';
              }
              if (id.includes('framer-motion')) {
                return 'animation';
              }
              if (id.includes('recharts')) {
                return 'charts';
              }
              if (id.includes('axios') || id.includes('@tanstack/react-query')) {
                return 'data';
              }
              if (id.includes('react-markdown') || id.includes('remark') || id.includes('rehype')) {
                return 'markdown';
              }
              if (id.includes('i18next') || id.includes('react-i18next')) {
                return 'i18n';
              }
              if (id.includes('jspdf') || id.includes('html2canvas')) {
                return 'pdf';
              }
              return 'vendor';
            }
          },
        },
      },
      chunkSizeWarningLimit: 500,
      reportCompressedSize: !isDev,
      sourcemap: isDev ? 'inline' : false,
      cssCodeSplit: true,
      modulePreload: {
        polyfill: true,
      },
    },
    optimizeDeps: {
      include: [
        'react',
        'react-dom',
        'react-router-dom',
        'axios',
        '@tanstack/react-query',
        'react-markdown',
        'framer-motion',
      ],
      exclude: ['@iconify/react'],
    },
  }
})
