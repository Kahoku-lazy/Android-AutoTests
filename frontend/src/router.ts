/**
 * 前端路由：汇总各模块页面，并挡住未登录访问。
 *
 * 业务：
 * - 未登录只能停留在登录页，打开其它页面会回到登录
 * - 已经登录再打开登录页，进入工作台
 * - 根路径进入工作台；找不到的地址显示 404
 */
import { createRouter, createWebHistory } from "vue-router"
import { getToken } from "@/shared/auth/token-storage"
import dbRoutes from "@/modules/dashboard/routes"
import dpRoutes from "@/modules/device-pool/routes"
import cmRoutes from "@/modules/case-manager/routes"
import rgRoutes from "@/modules/report-generator/routes"
import aiRoutes from "@/modules/ai-assistant/routes"
import tlRoutes from "@/modules/task-list/routes"
import wfRoutes from "@/modules/workflow/routes"
import slRoutes from "@/modules/serial-log/routes"
import ksRoutes from "@/modules/knowledge-assistant/routes"
import bugRoutes from "@/modules/bug-manager/routes"

const routes = [
  { path: "/login", name: "login", component: () => import("@/views/LoginView.vue") },
  ...dbRoutes,
  ...dpRoutes,
  ...cmRoutes,
  ...rgRoutes,
  ...aiRoutes,
  ...tlRoutes,
  ...wfRoutes,
  ...slRoutes,
  ...ksRoutes,
  ...bugRoutes,
  { path: "/", redirect: "/dashboard" },
  {
    path: "/:pathMatch(.*)*",
    name: "NotFound",
    component: () => import("@/views/NotFound.vue"),
    meta: { title: "404 - 页面未找到" },
  },
]

const router = createRouter({ history: createWebHistory(), routes })

// ── Update document.title after each navigation ──
router.afterEach((to) => {
  const base = "Android-AutoTests"
  document.title = to.meta?.title ? `${to.meta.title} — ${base}` : base
})

// ── 未登录回登录页；已登录再进登录页则去工作台 ──
router.beforeEach((to) => {
  const token = getToken()

  if (!token && to.path !== "/login") {
    return "/login"
  }
  if (token && to.path === "/login") {
    return "/dashboard"
  }
})

export default router
