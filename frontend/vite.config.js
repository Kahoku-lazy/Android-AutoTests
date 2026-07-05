import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'
import AutoImport from 'unplugin-auto-import/vite'
import Components from 'unplugin-vue-components/vite'
import { ElementPlusResolver } from 'unplugin-vue-components/resolvers'

// ── 性能优化插件：构建时剔除 animal-island-vue 自带的
//    Noto Sans SC 中文子集字体（3 个文件共 3.4MB）。
//    运行时由 style.css 中的 @font-face local() 覆盖兜底
//    为系统字体（Microsoft YaHei / PingFang SC），不发起网络请求。
function stripChineseFonts() {
  return {
    name: 'strip-chinese-fonts',
    apply: 'build',
    generateBundle(_opts, bundle) {
      // bundle 是 { [fileName]: OutputAsset | OutputChunk }
      for (const fileName of Object.keys(bundle)) {
        if (/noto-sans-sc-chinese-simplified-.*\.woff2$/.test(fileName)) {
          delete bundle[fileName]
        }
      }
    },
  }
}

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
    // 剔除中文字体（3.4MB → 0）
    stripChineseFonts(),
  ],
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src'),
    },
  },
  server: {
    port: 5173,
    proxy: {
      '/api': 'http://localhost:8765',
      '/ws': {
        target: 'ws://localhost:8765',
        ws: true,
      },
      '/agentscope': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/agentscope/, ''),
      },
      '/agentscope-stream': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/agentscope-stream/, ''),
      },
    },
  },
  build: {
    rollupOptions: {
      output: {
        // ── vendor 分包：让浏览器并行下载，登录页不被全量库拖累 ──
        manualChunks: {
          'element-plus': ['element-plus'],
          'animal-island': ['animal-island-vue'],
          'vendor': ['vue', 'vue-router', 'pinia', 'axios', 'animejs'],
        },
      },
    },
    // 中文字体文件较大，调高警告阈值避免噪音
    chunkSizeWarningLimit: 1500,
  },
})
