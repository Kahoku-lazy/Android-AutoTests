export default [
  {
    path: '/cases',
    name: 'case-manager',
    component: () => import('@/modules/case-manager/index.vue'),
  },
  {
    path: '/cases/new',
    name: 'case-new',
    component: () => import('@/modules/case-manager/CaseEditor.vue'),
  },
  {
    path: '/cases/:id/edit',
    name: 'case-edit',
    component: () => import('@/modules/case-manager/CaseEditor.vue'),
  },
]
