import type { RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  {
    path: '/devices',
    name: 'device-pool',
    component: () => import('@/modules/device-pool/index.vue'),
    meta: { title: '设备管理' },
  },
]

export default routes
