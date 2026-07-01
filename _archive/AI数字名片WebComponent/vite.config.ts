import { defineConfig } from 'vite';

export default defineConfig({
  build: {
    lib: {
      entry: 'src/ai-digital-card.ts',
      name: 'AiDigitalCard',
      formats: ['umd', 'es'],
      fileName: (format) => `ai-digital-card.${format === 'es' ? 'js' : 'umd.cjs'}`,
    },
    rollupOptions: {
      // Externalize peer dependencies — lit is bundled in for self-contained usage
      external: [],
      output: {
        globals: {},
        // Ensure the global variable is accessible
        exports: 'named',
      },
    },
    target: 'es2020',
    outDir: 'dist',
    sourcemap: true,
    minify: 'esbuild',
  },
});
