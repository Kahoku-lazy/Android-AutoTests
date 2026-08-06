import type { RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  {
    path: '/dashboard',
    name: 'dashboard',
    component: () => import('@/modules/dashboard/index.vue'),
    meta: { title: '总览', icon: 'dashboard' },
  },
]

export default routes
