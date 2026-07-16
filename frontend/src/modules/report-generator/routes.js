export default [
  {
    path: '/reports',
    name: 'report-generator',
    component: () => import('@/modules/report-generator/index.vue'),
    meta: { title: '测试报告' },
  },
  {
    path: '/reports/cases/:resultType',
    name: 'case-breakdown',
    component: () => import('@/modules/report-generator/CaseBreakdown.vue'),
    meta: { title: '用例细分' },
  },
  {
    path: '/reports/task/:taskId',
    name: 'task-report',
    component: () => import('@/modules/report-generator/TaskReport.vue'),
    meta: { title: '任务报告' },
  },
  {
    path: '/reports/:runId',
    name: 'report-detail',
    component: () => import('@/modules/report-generator/ReportDetail.vue'),
    meta: { title: '报告详情' },
  },
]
