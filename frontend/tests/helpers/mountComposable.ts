import { defineComponent, h, KeepAlive, nextTick, ref, type Component } from 'vue'
import { mount, type VueWrapper } from '@vue/test-utils'
import { createMemoryHistory, createRouter, type Router, type RouteRecordRaw } from 'vue-router'

const defaultRoutes: RouteRecordRaw[] = [
  { path: '/', component: { template: '<div />' } },
  { path: '/login', component: { template: '<div />' } },
  { path: '/dashboard', component: { template: '<div />' } },
]

export interface MountComposableOptions {
  router?: Router
  routes?: RouteRecordRaw[]
  initialPath?: string
  initialQuery?: Record<string, string>
  /**
   * 把探针组件放进 `<KeepAlive>` 里挂载。
   *
   * 打开后可通过返回的 `deactivate()` / `activate()` 模拟路由切走与切回——
   * 这正是 `App.vue` 的真实结构：切页只触发 `onDeactivated`，不触发 `onUnmounted`。
   */
  keepAlive?: boolean
}

export interface MountComposableResult<T> {
  result: T
  wrapper: VueWrapper
  router: Router
  /** 仅 `keepAlive: true` 时有意义：把探针组件切出视图（触发 `onDeactivated`） */
  deactivate?: () => Promise<void>
  /** 仅 `keepAlive: true` 时有意义：把探针组件切回视图（触发 `onActivated`） */
  activate?: () => Promise<void>
}

/** 挂载一个空组件以触发 onMounted，并拿到 setup 里 composable 的返回值 */
export async function mountComposable<T>(
  factory: () => T,
  options: MountComposableOptions = {},
): Promise<MountComposableResult<T>> {
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
    name: 'ComposableProbe',
    setup() {
      result = factory()
      return () => h('div')
    },
  }) as Component

  if (!options.keepAlive) {
    const wrapper = mount(Comp, {
      global: { plugins: [router] },
    })
    return { result, wrapper, router }
  }

  const Placeholder = defineComponent({
    name: 'ComposableProbePlaceholder',
    setup: () => () => h('span'),
  })
  const visible = ref(true)
  const Host = defineComponent({
    name: 'ComposableProbeHost',
    setup: () => () =>
      h(KeepAlive, null, {
        default: () => (visible.value ? h(Comp, { key: 'probe' }) : h(Placeholder, { key: 'other' })),
      }),
  })

  const wrapper = mount(Host, {
    global: { plugins: [router] },
  })

  return {
    result,
    wrapper,
    router,
    deactivate: async () => {
      visible.value = false
      await nextTick()
    },
    activate: async () => {
      visible.value = true
      await nextTick()
    },
  }
}

export function clearAuthStorage() {
  localStorage.clear()
  sessionStorage.clear()
}
