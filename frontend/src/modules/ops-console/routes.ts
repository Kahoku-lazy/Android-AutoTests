import type { RouteRecordRaw } from "vue-router"

const routes: RouteRecordRaw[] = [
  {
    path: "/ops/users",
    name: "ops-users",
    component: () => import("@/modules/ops-console/index.vue"),
    meta: { title: "用户管理", requiresOperator: true },
  },
]

export default routes
