/// <reference types="vitest/config" />
import react from '@vitejs/plugin-react';
import { defineConfig } from 'vite';

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
  build: {
    // Code splitting configuration
    rollupOptions: {
      output: {
        manualChunks: {
          // Split vendor code into separate chunks
          'react-vendor': ['react', 'react-dom'],
          'axios-vendor': ['axios'],
        },
      },
    },
    // Enable source maps for production debugging
    sourcemap: true,
    // Chunk size warning limit (500kb)
    chunkSizeWarningLimit: 500,
  },
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: './src/setupTests.ts',
    exclude: ['**/e2e/**', '**/node_modules/**'],
    coverage: {
      reporter: ['text', 'html', 'json'],
      exclude: ['node_modules/', 'src/setupTests.ts', '**/*.test.ts', '**/*.test.tsx', '**/e2e/**'],
    },
  },
});
