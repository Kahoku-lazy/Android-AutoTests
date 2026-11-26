import { createApp } from "vue"
import { createIcons } from "lucide"
import { lucideIconSubset } from "./shared/icons/lucide-registry"
import App from "./App.vue"
import router from "./router"

import "element-plus/dist/index.css"
import "./shared/styles/tokens.css"
import "./style.css"
import "./modules/ai-assistant/tokens.css"
import "./modules/case-manager/tokens.css"
import "./shared/styles/workbench-theme.css"
import "./shared/styles/motion.css"

import "./shared/styles/sketched-kit.css"

declare global {
  interface Window {
    lucide?: { createIcons: () => void }
  }
}

window.lucide = { createIcons: () => createIcons({ icons: lucideIconSubset }) }

const app = createApp(App)
app.use(router)
app.mount("#app")

if (import.meta.env.DEV) {
  void import("./shared/dev/scroll-guard").then(({ installScrollGuard }) =>
    installScrollGuard({ router }),
  )
}
