import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'
import AutoImport from 'unplugin-auto-import/vite'
import Components from 'unplugin-vue-components/vite'
import { ElementPlusResolver } from 'unplugin-vue-components/resolvers'

const isTest = !!process.env.VITEST

export default defineConfig({
  plugins: [
    vue(),
    // 单测用 stub 替换 el-*，避免 Element Plus 按需 CSS 拖垮 Vitest
    ...(!isTest
      ? [
          AutoImport({
            resolvers: [ElementPlusResolver()],
            dts: 'src/auto-imports.d.ts',
          }),
          Components({
            resolvers: [ElementPlusResolver()],
            dts: 'src/components.d.ts',
          }),
        ]
      : []),
  ],
  resolve: {
    alias: {
      // ESM-safe：package.json "type":"module" 下无 __dirname
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  test: {
    // Vitest UI 按 project 分栏：P0 / P1（P2 故意无用例）
    projects: [
      {
        extends: true,
        test: {
          name: 'P0',
          include: ['tests/**/p0/**/*.{test,spec}.{js,ts}'],
          environment: 'jsdom',
          css: false,
        },
      },
      {
        extends: true,
        test: {
          name: 'P1',
          include: ['tests/**/p1/**/*.{test,spec}.{js,ts}'],
          environment: 'jsdom',
          css: false,
        },
      },
    ],
  },
  server: {
    host: '0.0.0.0',
    port: 5173,
    proxy: {
      '/api': `http://localhost:${process.env.SERVER_PORT || 8766}`,
      '/ws': {
        target: `ws://localhost:${process.env.SERVER_PORT || 8766}`,
        ws: true,
      },
    },
  },
  build: {
    rollupOptions: {
      output: {
        // ── vendor 分包：让浏览器并行下载，登录页不被全量库拖累 ──
        manualChunks: {
          'element-plus': ['element-plus'],
          'vendor': ['vue', 'vue-router', 'pinia', 'axios', 'animejs'],
          'vue-flow': [
            '@vue-flow/core',
            '@vue-flow/background',
            '@vue-flow/controls',
            '@vue-flow/minimap',
          ],
          blockly: ['blockly'],
        },
      },
    },
    // 中文字体文件较大，调高警告阈值避免噪音
    chunkSizeWarningLimit: 1500,
  },
})
