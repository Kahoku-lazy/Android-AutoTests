import type { RouteRecordRaw } from "vue-router"

const routes: RouteRecordRaw[] = [
  {
    path: "/knowledge-search",
    name: "knowledge-search",
    component: () => import("@/modules/knowledge-search/index.vue"),
    meta: { title: "知识库" },
  },
]

export default routes
