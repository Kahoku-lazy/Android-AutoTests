export default [
  {
    path: "/cases",
    name: "case-manager",
    component: () => import("@/modules/case-manager/index.vue"),
    meta: { title: '用例管理' },
  },
  {
    path: "/cases/new",
    name: "case-new",
    component: () => import("@/modules/case-manager/CaseEditor.vue"),
    meta: { title: '新建用例' },
  },
  {
    path: "/cases/:id/edit",
    name: "case-edit",
    component: () => import("@/modules/case-manager/CaseEditor.vue"),
    meta: { title: '编辑用例' },
  },
];
