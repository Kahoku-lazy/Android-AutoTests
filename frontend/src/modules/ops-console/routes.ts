import type { RouteRecordRaw } from "vue-router"

const routes: RouteRecordRaw[] = [
  {
    path: "/ops/users",
    name: "ops-users",
    component: () => import("@/modules/ops-console/index.vue"),
    meta: { title: "用户管理", requiresOperator: true },
  },
  {
    path: "/ops/agents",
    name: "ops-agents",
    component: () => import("@/modules/ops-console/agents.vue"),
    meta: { title: "Agent配置", requiresOperator: true },
  },
  {
    path: "/ops/model-configs",
    name: "ops-model-configs",
    component: () => import("@/modules/ops-console/model-configs.vue"),
    meta: { title: "模型配置", requiresOperator: true },
  },
]

export default routes
