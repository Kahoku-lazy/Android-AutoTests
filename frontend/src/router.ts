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

// ── Auth guard — all pages require login except /login itself ──
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
