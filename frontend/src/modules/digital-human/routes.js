const routes = [
  {
    path: '/digital-human',
    name: 'digital-human',
    component: () => import('@/modules/digital-human/index.vue'),
    meta: { title: '平台数字人' },
  },
]

export default routes
