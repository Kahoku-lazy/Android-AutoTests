export default [
  {
    path: "/cases",
    name: "case-manager",
    component: () => import("@/modules/case-manager/index.vue"),
    meta: { title: '用例管理' },
  },
  // UI Automation (existing, backward compatible)
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
  // Storage / Business Function (NEW)
  {
    path: "/cases/storage/new",
    name: "storage-case-new",
    component: () => import("@/modules/case-manager/components/storage/StorageCaseEditor.vue"),
    meta: { title: '新建存储业务用例' },
  },
  {
    path: "/cases/storage/:id/edit",
    name: "storage-case-edit",
    component: () => import("@/modules/case-manager/components/storage/StorageCaseEditor.vue"),
    meta: { title: '编辑存储业务用例' },
  },
  // API Interface
  {
    path: "/cases/api/new",
    name: "api-case-new",
    component: () => import("@/modules/case-manager/components/api/ApiCaseEditor.vue"),
    meta: { title: '新建 API 接口用例' },
  },
  {
    path: "/cases/api/:id/edit",
    name: "api-case-edit",
    component: () => import("@/modules/case-manager/components/api/ApiCaseEditor.vue"),
    meta: { title: '编辑 API 接口用例' },
  },
  // Web Automation (NEW)
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
];
