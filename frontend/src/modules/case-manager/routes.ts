import type { RouteRecordRaw } from 'vue-router'

const legacyCasePaths = [
  '/cases/ui',
  '/cases/web',
  '/cases/storage',
  '/cases/api',
  '/cases/new',
  '/cases/web/new',
  '/cases/api/new',
  '/cases/storage/new',
]

const routes: RouteRecordRaw[] = [
  {
    path: '/cases',
    name: 'case-manager-projects',
    component: () => import('@/modules/case-manager/ProjectList.vue'),
    meta: { title: '用例管理' },
  },
  {
    path: '/cases/projects/:projectId',
    name: 'case-manager-workspace',
    component: () => import('@/modules/case-manager/ProjectWorkspace.vue'),
    meta: { title: '项目工作台' },
  },
  {
    path: '/cases/projects/:projectId/files/:fileId',
    name: 'case-manager-file-sheet',
    component: () => import('@/modules/case-manager/CaseFileSheet.vue'),
    meta: { title: '编辑用例表' },
  },
  {
    path: '/cases/projects/:projectId/cases/:caseId',
    redirect: (to) => `/cases/projects/${to.params.projectId}`,
  },
  // Legacy redirects
  ...legacyCasePaths.map((path) => ({
    path,
    redirect: '/cases',
  })),
  {
    path: '/cases/:id/edit',
    redirect: '/cases',
  },
  {
    path: '/cases/web/:id/edit',
    redirect: '/cases',
  },
  {
    path: '/cases/api/:id/edit',
    redirect: '/cases',
  },
  {
    path: '/cases/storage/:id/edit',
    redirect: '/cases',
  },
]

export default routes
