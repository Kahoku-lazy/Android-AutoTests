import type { RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  {
    path: '/workflow',
    name: 'workflow-prototypes',
    component: () => import('@/modules/workflow/PrototypeList.vue'),
    meta: { title: '页面流' },
  },
  {
    path: '/workflow/prototypes/:prototypeId',
    name: 'workflow-workbench',
    component: () => import('@/modules/workflow/index.vue'),
    meta: { title: '原型工作台' },
  },
]

export default routes
