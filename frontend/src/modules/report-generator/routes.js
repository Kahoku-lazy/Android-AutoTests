export default [
  {
    path: '/reports',
    name: 'report-generator',
    component: () => import('@/modules/report-generator/index.vue'),
  },
  {
    path: '/reports/task/:taskId',
    name: 'task-report',
    component: () => import('@/modules/report-generator/TaskReport.vue'),
  },
  {
    path: '/reports/:runId',
    name: 'report-detail',
    component: () => import('@/modules/report-generator/ReportDetail.vue'),
  },
]
