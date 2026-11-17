import type { RouteRecordRaw } from "vue-router"

const routes: RouteRecordRaw[] = [
  {
    path: "/cases",
    name: "case-manager-projects",
    component: () => import("@/modules/case-manager/ProjectList.vue"),
    meta: { title: "用例管理" },
  },
  {
    path: "/cases/projects/:projectId",
    name: "case-manager-sheet",
    component: () => import("@/modules/case-manager/ProjectSheet.vue"),
    meta: { title: "项目用例表" },
  },
  {
    path: "/cases/projects/:projectId/files/:fileId",
    redirect: (to) => `/cases/projects/${to.params.projectId}`,
  },
]

export default routes
