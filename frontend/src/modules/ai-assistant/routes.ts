import type { RouteRecordRaw } from "vue-router"

const routes: RouteRecordRaw[] = [
  {
    path: "/ai-assistant",
    name: "ai-assistant",
    component: () => import("@/modules/ai-assistant/index.vue"),
    meta: { title: "平台助手" },
  },
  {
    path: "/ai-assistant/evals",
    name: "ai-assistant-evals",
    component: () => import("@/modules/ai-assistant/evals.vue"),
    meta: { title: "评测" },
  },
  {
    path: "/ai-assistant/eval-cases",
    name: "ai-assistant-eval-cases",
    component: () => import("@/modules/ai-assistant/eval-cases.vue"),
    meta: { title: "评测题库" },
  },
  {
    path: "/ai-assistant/:assistantId/chat",
    name: "ai-assistant-chat",
    component: () => import("@/modules/ai-assistant/chat.vue"),
    meta: { title: "助手对话" },
  },
]

export default routes
