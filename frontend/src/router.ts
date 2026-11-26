import { createRouter, createWebHistory } from "vue-router"
import { getToken } from "@/shared/auth/token-storage"
import { resetAuthUser, useAuthUser } from "@/shared/composables/useAuthUser"
import dbRoutes from "@/modules/dashboard/routes"
import dpRoutes from "@/modules/device-pool/routes"
import cmRoutes from "@/modules/case-manager/routes"

import aiRoutes from "@/modules/ai-assistant/routes"
import slRoutes from "@/modules/serial-log/routes"
import ksRoutes from "@/modules/knowledge-search/routes"
import taskRoutes from "@/modules/task-list/routes"
import bugRoutes from "@/modules/bug-manager/routes"
import reportRoutes from "@/modules/report-generator/routes"
import opsRoutes from "@/modules/ops-console/routes"

const routes = [
  { path: "/login", name: "login", component: () => import("@/views/LoginView.vue") },
  ...dbRoutes,
  ...dpRoutes,
  ...cmRoutes,
  ...aiRoutes,
  ...taskRoutes,
  ...slRoutes,
  ...ksRoutes,
  ...bugRoutes,
  ...reportRoutes,
  ...opsRoutes,
  { path: "/", redirect: "/dashboard" },
  {
    path: "/:pathMatch(.*)*",
    name: "NotFound",
    component: () => import("@/views/NotFound.vue"),
    meta: { title: "404 - 页面未找到" },
  },
]

const router = createRouter({ history: createWebHistory(), routes })

router.afterEach((to) => {
  const base = "Android-AutoTests"
  document.title = to.meta?.title ? `${to.meta.title} — ${base}` : base
})

router.beforeEach(async (to) => {
  const token = getToken()

  if (!token) {
    resetAuthUser()
    if (to.path !== "/login") return "/login"
    return
  }
  if (to.path === "/login") return "/dashboard"

  if (to.meta?.requiresOperator) {
    const { ensure, isOperator } = useAuthUser()
    await ensure()
    if (!isOperator.value) return "/dashboard"
  }
})

export default router
