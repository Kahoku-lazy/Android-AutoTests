import type { RouteRecordRaw } from "vue-router"

const routes: RouteRecordRaw[] = [
  {
    path: "/ai-assistant",
    name: "ai-assistant",
    component: () => import("@/modules/ai-assistant/index.vue"),
    meta: { title: "平台助手" },
  },
  {
    path: "/ai-assistant/:assistantId/chat",
    name: "ai-assistant-chat",
    component: () => import("@/modules/ai-assistant/chat.vue"),
    meta: { title: "助手对话" },
  },
]

export default routes
