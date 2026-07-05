export default [
  {
    path: '/dashboard',
    name: 'dashboard',
    component: () => import('@/modules/dashboard/index.vue'),
    meta: { title: '总览', icon: 'dashboard' },
  },
]
