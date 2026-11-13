import {defineConfig} from 'vitest/config';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';
export default defineConfig({plugins:[react(),tailwindcss()],build:{rollupOptions:{output:{manualChunks:{charts:['recharts'],framework:['react','react-dom','react-router-dom']}}}},test:{environment:'jsdom',setupFiles:['./src/test/setup.ts']}});
