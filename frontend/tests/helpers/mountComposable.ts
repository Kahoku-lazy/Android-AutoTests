import { defineComponent, h, type Component } from 'vue'
import { mount, type VueWrapper } from '@vue/test-utils'
import { createMemoryHistory, createRouter, type Router, type RouteRecordRaw } from 'vue-router'

const defaultRoutes: RouteRecordRaw[] = [
  { path: '/', component: { template: '<div />' } },
  { path: '/login', component: { template: '<div />' } },
  { path: '/dashboard', component: { template: '<div />' } },
]

/** 挂载一个空组件以触发 onMounted，并拿到 setup 里 composable 的返回值 */
export async function mountComposable<T>(
  factory: () => T,
  options: {
    router?: Router
    routes?: RouteRecordRaw[]
    initialPath?: string
    initialQuery?: Record<string, string>
  } = {},
): Promise<{ result: T; wrapper: VueWrapper; router: Router }> {
  const router =
    options.router ??
    createRouter({
      history: createMemoryHistory(),
      routes: options.routes ?? defaultRoutes,
    })

  await router.push({
    path: options.initialPath ?? '/',
    query: options.initialQuery,
  })
  await router.isReady()

  let result!: T
  const Comp = defineComponent({
    setup() {
      result = factory()
      return () => h('div')
    },
  }) as Component

  const wrapper = mount(Comp, {
    global: { plugins: [router] },
  })

  return { result, wrapper, router }
}

export function clearAuthStorage() {
  localStorage.clear()
  sessionStorage.clear()
}
