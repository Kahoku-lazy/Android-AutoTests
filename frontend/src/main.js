import { createApp } from 'vue'
import { createPinia } from 'pinia'
import 'element-plus/dist/index.css'
import 'animal-island-vue/style'
import App from './App.vue'
import router from './router'
import './style.css'
import './shared/styles/workbench-theme.css'
import './shared/styles/motion.css'

// 注：Element Plus 组件由 unplugin-vue-components 按需引入
// 注：ElMessage / ElMessageBox 等 API 由 unplugin-auto-import 按需引入

const app = createApp(App)
app.use(createPinia())
app.use(router)
app.mount('#app')
