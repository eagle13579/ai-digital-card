import tailwindcss from '@tailwindcss/vite';
import react from '@vitejs/plugin-react';
import {defineConfig} from 'vite';

export default defineConfig(() => {
  return {
    base: '/',
    plugins: [react(), tailwindcss()],
    build: {
      outDir: 'dist',
    },
    server: {
      proxy: {
        '/api': {
          target: 'http://localhost:8002',
          changeOrigin: true,
        },
      },
    },
  };
});
