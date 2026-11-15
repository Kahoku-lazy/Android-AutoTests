---
name: vue
description: >-
  Use when writing or reviewing Vue 3 code in this repo — .vue components, `use*` composables, shared helpers, Vitest specs, or TypeScript patterns.
  Covers props/emits (including Vue 3.5 prop destructuring), defineModel, slots, composable structure and cleanup, reactivity gotchas, vue-tsc edge cases,
  and route meta typing for the repo's static router. Project-first: frontend/AGENTS.md and doodle-craft win over this skill.
  Deliberately skips Nuxt, VueUse, unplugin-vue-router and custom directives — none of them are dependencies here.
license: MIT
---

# Vue 3 写法速查（本仓库）

通用 Vue 3 内核写法参考，已按本仓库裁剪。

**优先级**：`frontend/AGENTS.md`（文件组织 / 500 行 / API 层）→ `doodle-craft`（组件皮肤与令牌）→ 本技能（Vue 内核细节）→ 需要「文档原文 / 版本依据」时用 `vue-docs`。

**版本口径**：`frontend` 实装 **Vue 3.5.44**，`package.json` 声明 `^3.4.0`、lock 锁 3.5.39。
所以 3.5 才稳定的写法（props 解构）本机可用，但**不要假设项目能回滚到 3.4**；某 API 从哪版开始，交 `vue-docs` 判。

## 何时用 / 何时不用

**用**：写 `.vue` 组件、`use*` 组合式函数、`shared/helpers` 纯函数、`.spec.ts` 测试、Vue 相关 TS 类型。

**不用**：

- 组件皮肤、布局、令牌 → `doodle-craft`
- 页面改版方案 / 原型 → `frontend-change-plan`
- 「官方文档怎么说 / 这个 API 3.4 有没有」→ `vue-docs`
- Element Plus 组件 API（el-table / el-dialog / el-form）→ Element Plus 文档，本技能不覆盖

## 速查表（按任务取文件）

| 正在改… | 读 |
| --- | --- |
| `components/*.vue`、props/emits/slots | [references/components.md](references/components.md) |
| `composables/useX.ts` | [references/composables.md](references/composables.md) |
| `shared/helpers/*.ts` | [references/helpers.md](references/helpers.md) |
| `*.spec.ts`、`frontend/tests/` | [references/testing.md](references/testing.md) |
| TS 泛型、`vue-tsc` 报错 | [references/typescript.md](references/typescript.md) |
| `routes.ts`、`route.meta`、守卫 | [references/router.md](references/router.md) |
| `ref` / `reactive` / `watch` / `computed` | [references/reactivity.md](references/reactivity.md) |
| `provide` / `inject` | [references/provide-inject.md](references/provide-inject.md) |
| 边角问题、hydration、竞态 | [references/gotchas.md](references/gotchas.md) |

**不要一次全读**，按当前任务只取一两个。

## 与本仓库的锚点

- 共享件：`AppTable`、`AppCard`、`SketchCard`、`KpiCard`、`DoodleBtn`、`FilterTabs`、`WorkbenchHeader/Crumbs`、三态件（`SkeletonCard`/`ErrorState`/`EmptyState`）。新组件先找它们，别自造第二套。
- HTTP 唯一出口：`shared/api-client.ts`；错误统一走 `formatApiError`，组件里不直接 `axios`。
- 跨组件事件：已有 `mitt`；不要另造事件总线，也不要靠 `$emit` 跨层透传。
- 本仓库**没有**：VueUse、Nuxt、`unplugin-vue-router`、自定义指令、`defineModel` 使用先例（要引入先在方案里说明）。

## 快速起点（仓库风格）

```vue
<script setup lang="ts">
const props = withDefaults(defineProps<{ title: string; count?: number }>(), {
  count: 0,
})

const emit = defineEmits<{
  select: [id: number]
  refresh: []
}>()
</script>

<template>
  <button type="button" @click="emit('select', props.count)">
    {{ title }}
  </button>
</template>
```

- props 解构（Vue 3.5+）在仓库里已有 22 处，两种写法都可以；**同一文件内保持一致**。
- `defineEmits` 用元组签名（仓库 27 处），比函数重载更贴近现有代码。
- 组件超过 500 行先拆样式层，再拆逻辑层（`frontend/AGENTS.md`）。

## 本技能不覆盖

Nuxt / SSR 框架层、Element Plus 组件用法、设计令牌与布局、文档检索——各自由对应技能负责。
