import type { RouteRecordRaw } from "vue-router"

const routes: RouteRecordRaw[] = [
  {
    path: "/tasks",
    name: "task-list",
    component: () => import("@/modules/task-list/index.vue"),
    meta: { title: "任务清单" },
  },
  {
    path: "/tasks/:id",
    name: "task-detail",
    component: () => import("@/modules/task-list/TaskDetailPage.vue"),
    meta: { title: "任务详情" },
  },
]

export default routes
