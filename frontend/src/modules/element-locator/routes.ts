import type { RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  {
    path: '/elements',
    name: 'element-locator-projects',
    component: () => import('@/modules/element-locator/ProjectList.vue'),
    meta: { title: '元素定位' },
  },
  {
    path: '/elements/projects/:code',
    name: 'element-locator-workspace',
    component: () => import('@/modules/element-locator/ProjectWorkspace.vue'),
    meta: { title: '元素项目' },
  },
  {
    path: '/elements/projects/:code/files/:fileId',
    name: 'element-locator-file',
    component: () => import('@/modules/element-locator/LocatorFileView.vue'),
    meta: { title: '元素详情' },
  },
  {
    path: '/elements/android',
    redirect: '/elements/projects/android',
  },
  {
    path: '/elements/web',
    redirect: '/elements/projects/web',
  },
  {
    path: '/elements/api',
    redirect: '/elements/projects/api',
  },
  {
    path: '/element-mgr',
    redirect: '/elements/projects/android',
  },
]

export default routes
