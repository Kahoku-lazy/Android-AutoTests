export default [
  {
    path: '/workflow',
    name: 'workflow-workbench',
    component: () => import('@/modules/workflow/index.vue'),
    meta: { title: '工作流工作台' },
  },
]
