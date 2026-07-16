export default [
  {
    path: '/runner',
    name: 'test-runner',
    component: () => import('@/modules/test-runner/index.vue'),
    meta: { title: '执行引擎' },
  },
  {
    path: '/runner/task/:taskId',
    name: 'task-detail',
    component: () => import('@/modules/test-runner/components/TaskDetail.vue'),
    meta: { title: '任务详情' },
  },
]
