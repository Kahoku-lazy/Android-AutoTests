import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { createIcons } from 'lucide'
import { lucideIconSubset } from './shared/icons/lucide-registry'
import App from './App.vue'
import router from './router'
// Element Plus 全量样式：30 个文件是显式 import { ElMessageBox } from 'element-plus'，
// 走不到 resolver 的按需样式注入（实测会丢 .el-message-box），所以样式统一由这一份全量提供；
// vite.config 里 ElementPlusResolver 已设 importStyle:false，按需组件样式不再重复下发。
import 'element-plus/dist/index.css'
import './shared/styles/tokens.css'
import './style.css'
import './modules/ai-assistant/tokens.css'
import './modules/case-manager/tokens.css'
import './modules/device-inspector/tokens.css'
import './modules/element-locator/tokens.css'
import './modules/workflow/tokens.css'
import './shared/styles/workbench-theme.css'
import './shared/styles/motion.css'

// 注：Element Plus 组件由 unplugin-vue-components 按需引入（样式见上方全量 import）
// 注：ElMessage / ElMessageBox 等 API 由 unplugin-auto-import 按需引入

declare global {
  interface Window {
    /** lucide 图标入口：由 main.ts 注入，组件用 data-lucide + createIcons 渲染（见 AppSidebar / WorkbenchHeader） */
    lucide?: { createIcons: () => void }
  }
}

// lucide 图标：走本地依赖 + 图标子集（原为 index.html 的 unpkg CDN —— 版本不锁、离线环境静默失效）
window.lucide = { createIcons: () => createIcons({ icons: lucideIconSubset }) }

const app = createApp(App)
app.use(createPinia())
app.use(router)
app.mount('#app')

// 仅开发环境：L0 滚动自检（页面根被裁切且无法滚动时告警），生产构建不含此模块
if (import.meta.env.DEV) {
  void import('./shared/dev/scroll-guard').then(({ installScrollGuard }) => installScrollGuard({ router }))
}
