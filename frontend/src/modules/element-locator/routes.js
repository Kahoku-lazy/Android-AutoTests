export default [
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
    meta: { title: '元素管理' },
  },
]
