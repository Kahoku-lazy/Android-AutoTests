import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'
import AutoImport from 'unplugin-auto-import/vite'
import Components from 'unplugin-vue-components/vite'
import { ElementPlusResolver } from 'unplugin-vue-components/resolvers'

export default defineConfig({
  plugins: [
    vue(),
    // Element Plus 按需引入：AutoImport 负责 ElMessage / ElMessageBox 等 API
    AutoImport({
      resolvers: [ElementPlusResolver()],
      dts: 'src/auto-imports.d.ts',
    }),
    // Components 负责 <el-xxx> 组件自动注册
    Components({
      resolvers: [ElementPlusResolver()],
      dts: 'src/components.d.ts',
    }),
  ],
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src'),
    },
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
