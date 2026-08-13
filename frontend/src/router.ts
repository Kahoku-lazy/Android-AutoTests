import { createRouter, createWebHistory } from 'vue-router'
import { getToken, getActiveUsername } from '@/shared/auth/token-storage'
import dbRoutes  from '@/modules/dashboard/routes'
import elRoutes   from '@/modules/element-locator/routes'
import diRoutes   from '@/modules/device-inspector/routes'
import dpRoutes   from '@/modules/device-pool/routes'
import cmRoutes   from '@/modules/case-manager/routes'
import trRoutes   from '@/modules/test-runner/routes'
import rgRoutes   from '@/modules/report-generator/routes'
// element-manager 已合并到 element-locator (routes.js 中 /element-mgr 路由)
import aiRoutes   from '@/modules/ai-assistant/routes'
import wfRoutes   from '@/modules/workflow/routes'
import dhRoutes   from '@/modules/digital-human/routes'

const routes = [
  { path: '/login', name: 'login',
    component: () => import('@/views/LoginView.vue') },
  ...dbRoutes, ...diRoutes, ...elRoutes, ...dpRoutes, ...cmRoutes, ...trRoutes, ...rgRoutes, ...aiRoutes, ...wfRoutes, ...dhRoutes,
  { path: '/', redirect: '/dashboard' },
  { path: '/:pathMatch(.*)*', name: 'NotFound', component: () => import('@/views/NotFound.vue'), meta: { title: '404 - 页面未找到' } },
]

const router = createRouter({ history: createWebHistory(), routes })

// ── Update document.title after each navigation ──
router.afterEach((to) => {
  const base = 'Android-AutoTests'
  document.title = to.meta?.title ? `${to.meta.title} — ${base}` : base
})

// ── Auth guard — all pages require login except /login itself ──
router.beforeEach((to) => {
  const token = getToken()
  // 登录路由下禁用 body 背景动画（性能优化：避免空转）
  if (to.path === '/login') {
    document.body?.classList.add('no-bg-anim')
  } else {
    document.body?.classList.remove('no-bg-anim')
  }
  if (!token && to.path !== '/login') {
    return '/login'
  }
  if (token && to.path === '/login' && !to.query.add) {
    return '/dashboard'
  }
})

export default router
