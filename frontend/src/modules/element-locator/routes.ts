import type { RouteRecordRaw } from "vue-router"

const routes: RouteRecordRaw[] = [
  {
    path: '/elements',
    redirect: '/elements/android',
  },
  {
    path: '/elements/android',
    name: 'element-locator-android',
    component: () => import('@/modules/element-locator/index.vue'),
    meta: { title: 'Android元素管理' },
  },
  {
    path: '/elements/web',
    name: 'element-locator-web',
    component: () => import('@/modules/element-locator/index.vue'),
    meta: { title: 'Web端元素' },
  },
  {
    path: '/elements/api',
    name: 'element-locator-api',
    component: () => import('@/modules/element-locator/index.vue'),
    meta: { title: 'API接口' },
  },
  {
    path: '/element-mgr',
    name: 'ElementManager',
    component: () => import('@/modules/element-locator/components/ElementManager.vue'),
    meta: { title: 'Android元素管理' },
  },
]
export default routes
