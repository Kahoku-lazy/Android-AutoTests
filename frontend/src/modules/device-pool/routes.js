export default [
  {
    path: '/devices',
    name: 'device-pool',
    component: () => import('@/modules/device-pool/index.vue'),
    meta: { title: '设备管理' },
  },
]
