import type { RouteRecordRaw } from "vue-router"

const routes: RouteRecordRaw[] = [
  {
    path: "/bugs",
    name: "bug-manager",
    component: () => import("@/modules/bug-manager/index.vue"),
    meta: { title: "BUG单管理" },
  },
]

export default routes
