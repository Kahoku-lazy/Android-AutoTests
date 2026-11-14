import type { RouteRecordRaw } from "vue-router"

const routes: RouteRecordRaw[] = [
  {
    path: "/agent-reports",
    name: "agent-reports",
    component: () => import("@/modules/agent-reports/index.vue"),
    meta: { title: "执行报告" },
  },
]

export default routes
