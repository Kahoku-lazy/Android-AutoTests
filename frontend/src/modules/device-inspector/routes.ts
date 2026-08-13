import type { RouteRecordRaw } from "vue-router"

const routes: RouteRecordRaw[] = [
  {
    path: '/inspector',
    name: 'device-inspector',
    component: () => import('@/modules/device-inspector/index.vue'),
    meta: { title: '设备检查器' },
  },
]
export default routes
