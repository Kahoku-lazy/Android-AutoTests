import type { RouteRecordRaw } from "vue-router"

const routes: RouteRecordRaw[] = [
  {
    path: "/knowledge-assistant",
    name: "knowledge-assistant",
    component: () => import("@/modules/knowledge-assistant/index.vue"),
    meta: { title: "知识库助手" },
  },
]

export default routes
