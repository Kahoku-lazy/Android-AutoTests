import type { RouteRecordRaw } from "vue-router"

const routes: RouteRecordRaw[] = [
  {
    path: '/elements',
    name: 'element-locator',
    component: () => import('@/modules/element-locator/index.vue'),
    meta: { title: '元素定位' },
  },
  {
    path: '/element-mgr',
    name: 'ElementManager',
    component: () => import('@/modules/element-locator/components/ElementManager.vue'),
    meta: { title: 'Android元素管理' },
  },
]
export default routes
