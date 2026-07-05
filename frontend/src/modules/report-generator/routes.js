export default [
  {
    path: '/reports',
    name: 'report-generator',
    component: () => import('@/modules/report-generator/index.vue'),
  },
]
