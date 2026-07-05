export default [
  {
    path: '/elements',
    name: 'element-locator',
    component: () => import('@/modules/element-locator/index.vue'),
  },
  {
    path: '/element-mgr',
    name: 'ElementManager',
    component: () => import('@/modules/element-locator/components/ElementManager.vue'),
  },
]
