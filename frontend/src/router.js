import { createRouter, createWebHistory } from 'vue-router'
import dbRoutes  from '@/modules/dashboard/routes.js'
import elRoutes   from '@/modules/element-locator/routes.js'
import dpRoutes   from '@/modules/device-pool/routes.js'
import cmRoutes   from '@/modules/case-manager/routes.js'
import trRoutes   from '@/modules/test-runner/routes.js'
import rgRoutes   from '@/modules/report-generator/routes.js'
// element-manager 已合并到 element-locator (routes.js 中 /element-mgr 路由)
import aiRoutes   from '@/modules/ai-assistant/routes.js'
import wfRoutes   from '@/modules/workflow/routes.js'

const routes = [
  { path: '/login', name: 'login',
    component: () => import('@/views/LoginView.vue') },
  ...dbRoutes, ...elRoutes, ...dpRoutes, ...cmRoutes, ...trRoutes, ...rgRoutes, ...aiRoutes, ...wfRoutes,
  { path: '/', redirect: '/dashboard' },
  { path: '/:pathMatch(.*)*', redirect: '/dashboard' },
]

const router = createRouter({ history: createWebHistory(), routes })

// ── Auth guard — all pages require login except /login itself ──
router.beforeEach((to) => {
  const token = localStorage.getItem('access_token')
  // 登录路由下禁用 body 背景动画（性能优化：避免空转）
  if (to.path === '/login') {
    document.body?.classList.add('no-bg-anim')
  } else {
    document.body?.classList.remove('no-bg-anim')
  }
  if (!token && to.path !== '/login') {
    return '/login'
  }
  if (token && to.path === '/login') {
    return '/dashboard'
  }
})

export default router
