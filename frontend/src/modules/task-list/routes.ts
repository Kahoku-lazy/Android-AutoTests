import type { RouteRecordRaw } from "vue-router"

const routes: RouteRecordRaw[] = [
  {
    path: "/tasks",
    name: "task-list",
    component: () => import("@/modules/task-list/index.vue"),
    meta: { title: "任务清单" },
  },
]

export default routes
