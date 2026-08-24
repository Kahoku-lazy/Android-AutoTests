import type { RouteRecordRaw } from "vue-router"

const routes: RouteRecordRaw[] = [
  {
    path: "/cases",
    redirect: "/cases/ui",
  },
  {
    path: "/cases/ui",
    name: "case-manager-ui",
    component: () => import("@/modules/case-manager/index.vue"),
    meta: { title: 'Android UI 自动化用例' },
  },
  {
    path: "/cases/web",
    name: "case-manager-web",
    component: () => import("@/modules/case-manager/index.vue"),
    meta: { title: 'Web 自动化测试用例' },
  },
  {
    path: "/cases/storage",
    name: "case-manager-storage",
    component: () => import("@/modules/case-manager/index.vue"),
    meta: { title: '业务功能用例' },
  },
  {
    path: "/cases/api",
    name: "case-manager-api",
    component: () => import("@/modules/case-manager/index.vue"),
    meta: { title: 'API 接口用例' },
  },
  // UI Automation
  {
    path: "/cases/new",
    name: "case-new",
    component: () => import("@/modules/case-manager/CaseEditor.vue"),
    meta: { title: '新建 UI 自动化用例' },
  },
  {
    path: "/cases/:id/edit",
    name: "case-edit",
    component: () => import("@/modules/case-manager/CaseEditor.vue"),
    meta: { title: '编辑 UI 自动化用例' },
  },
  // Web Automation
  {
    path: "/cases/web/new",
    name: "web-case-new",
    component: () => import("@/modules/case-manager/components/web/WebCaseEditor.vue"),
    meta: { title: '新建 Web 自动化用例' },
  },
  {
    path: "/cases/web/:id/edit",
    name: "web-case-edit",
    component: () => import("@/modules/case-manager/components/web/WebCaseEditor.vue"),
    meta: { title: '编辑 Web 自动化用例' },
  },
  // API
  {
    path: "/cases/api/new",
    name: "api-case-new",
    component: () => import("@/modules/case-manager/components/api/ApiCaseEditor.vue"),
    meta: { title: '新建 API 用例' },
  },
  {
    path: "/cases/api/:id/edit",
    name: "api-case-edit",
    component: () => import("@/modules/case-manager/components/api/ApiCaseEditor.vue"),
    meta: { title: '编辑 API 用例' },
  },
  // Storage
  {
    path: "/cases/storage/new",
    name: "storage-case-new",
    component: () => import("@/modules/case-manager/components/storage/StorageCaseEditor.vue"),
    meta: { title: '新建功能用例' },
  },
  {
    path: "/cases/storage/:id/edit",
    name: "storage-case-edit",
    component: () => import("@/modules/case-manager/components/storage/StorageCaseEditor.vue"),
    meta: { title: '编辑功能用例' },
  },
];
export default routes
