# Vue Router：本项目用法

本仓库用**静态路由表**（`src/router.ts` + 各模块 `routes.ts`），没有 `unplugin-vue-router`，也没有文件路由。因此这里只讲三件事：`route.meta` 类型、params 收窄、守卫类型。

## route.meta 类型

`routes.ts` 里每个路由都带 `meta.title`，把它补进 `RouteMeta` 就有补全：

```ts
// src/router/types.ts
import "vue-router"

declare module "vue-router" {
  interface RouteMeta {
    title?: string
    requiresAuth?: boolean
  }
}
```

```ts
const route = useRoute()
route.meta.title // string | undefined
```

不扩展 `RouteMeta` 时，`route.meta.xxx` 是 `any`，拼错字段名不会报错——这是最常见的丢类型方式。

## params 收窄

静态路由的 `params` 一定是 `string | string[]`，组件里不要直接当 `number` 用：

```ts
// 本仓库的现有写法：先转再算
const projectId = computed(() => Number(route.params.projectId))
```

```ts
// 可能命中 catch-all 时先判数组
const raw = route.params.id
const id = Array.isArray(raw) ? raw[0] : raw
```

- 路由变化要重新取数时用 `watch(() => route.params.id, ...)`，不要只在 `onMounted` 里读一次。
- `router.push` 用 name + params 比手拼字符串安全：

```ts
router.push({ name: "case-manager-workspace", params: { projectId } })
```

## 守卫

```ts
import type { NavigationGuardWithThis } from "vue-router"

const authGuard: NavigationGuardWithThis<undefined> = (to) => {
  if (to.meta.requiresAuth && !isLoggedIn()) {
    return { name: "login", query: { redirect: to.fullPath } }
  }
}
```

- 本仓库目前只有一个全局 `beforeEach`；新增守卫先确认是否真的需要全局，能放在页面里就别放路由层。
- 守卫里不要做重活（请求、解析大文件），会卡住整次导航。

## 常用类型

```ts
import type {
  RouteLocationNormalized,       // 解析后的路由（守卫入参）
  RouteLocationNormalizedLoaded, // useRoute() 的返回
  RouteLocationRaw,              // router.push 的入参
  RouteRecordRaw,                // 路由表定义
} from "vue-router"
```

## 常见错误

```ts
// ❌ 依赖 name 字符串手写，改名后静默 404
router.push(`/cases/projects/${id}`)

// ✅ 具名路由，改 path 不影响调用方
router.push({ name: "case-manager-workspace", params: { projectId: id } })

// ❌ 把 params 当 number
route.params.projectId + 1

// ✅ 显式转换
Number(route.params.projectId) + 1
```

## 相关

- 懒加载路由的 `component: () => import(...)` 与 Vite 分包在 `guide/scaling-up/routing`；本仓库的路由表都在模块 `routes.ts`。
- 页面级返回/面包屑：`WorkbenchCrumbs`（子页导航规范见 `frontend-doodle-subpage-nav`）。
