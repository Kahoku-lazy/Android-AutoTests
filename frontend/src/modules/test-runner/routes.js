export default [
  {
    path: '/runner',
    name: 'test-runner',
    component: () => import('@/modules/test-runner/index.vue'),
  },
  {
    path: '/runner/task/:taskId',
    name: 'task-detail',
    component: () => import('@/modules/test-runner/components/TaskDetail.vue'),
  },
]
