## Context

- 实测分布（`v-loading` 12 处 / `el-skeleton` 6 处 / 模块私有 `__loading` 容器 4 处 / `SkeletonCard` 1 处 / `WbLoader` 1 处），明细见 `proposal.md`。
- 假空态机制：`case-manager/ProjectWorkspace.vue:15-27` 与 `element-locator/ProjectWorkspace.vue:20-30` 解构 composable 时**未取 `loading`**，而两个 composable 的返回值中都有 `loading`（`useProjectTree.ts:177` / `useLocatorTree.ts:248`）；子树 `components/ProjectTree.vue:408-409` 与 `LocatorTree.vue` 各自有 `<EmptyState v-if="!treeData.length">`，加载期 `tree` 为 `[]` → 空态抢先渲染。
- `SkeletonCard`（`shared/components/patterns/SkeletonCard.vue`）目前只有单一布局：4 条固定高度占位条（60/24/12/24px），面向 KPI 卡；直接用于整页列表会呈"一张卡的形状"，因此本变更为其增加 `variant` 以覆盖列表场景。
- `el-skeleton` 在变更 4 之后底色已随 `--el-fill-color` 落到暖灰，故本变更的目标是**写法统一**而非修色。
- 动机见 `proposal.md`。

## Goals / Non-Goals

**Goals**

- 两个项目工作台在加载期渲染骨架而非空态
- 区块/列表级骨架统一到 `SkeletonCard`，删除模块私有 `__loading` 容器
- 错误态统一到 `ErrorState`（消除唯一 `el-alert` 用法）
- 分层口径写进 spec，避免"哪种加载用哪种写法"再次漂移

**Non-Goals**

- 不改 12 处 `v-loading`（原地遮罩分层，语义正确）
- 不把 `WbLoader`（品牌 loader + 文案）收敛为骨架，本期登记为例外
- 不改 `AppTable` 内部的 `v-loading` 实现
- 不动各页面的取数逻辑与 composable

## Decisions

**D1 扩展 `SkeletonCard` 的 `variant`，而不是新建 `SkeletonList` 组件**
理由：骨架的唯一实现应只有一个共享件；`variant` 是同一角色的布局档，符合"复制不发明"。默认值取 `card`，保证 `dashboard/StatsCard.vue` 现状不变。
备选：新建 `SkeletonList.vue` —— 否决，会留下两个骨架共享件。
备选：保留 `el-skeleton` 只统一外层容器 —— 否决，"同一角色两套原子"正是本变更要消除的漂移。

**D2 加载期在页面层用 `v-if` 切换骨架，而不是给子组件传 `loading`**
理由：两个树的空态由子组件自己拥有（`ProjectTree` / `LocatorTree` 各有一处 `EmptyState`），传参需要同时改两个子组件并与空态条件耦合；在页面层用 `v-if="loading"` / `v-else` 隔离挂载更简单、改动面更小，且加载期不挂载树也避免了无谓的树渲染。
备选：给子树加 `loading` prop —— 否决（改动面更大、两个子组件各需改空态判定）。

**D3 `el-alert` 直接换成共享 `ErrorState`**
理由：同模块已有 4 处 `ErrorState` + `@retry` 的正确范式；`ErrorState` 自带重试入口，而 `el-alert` 需要额外配一个按钮。本项在变更 4 已把 `el-alert` 配色拉回主题，此处解决的是**角色重复**。

**D4 `variant="list"` 的占位取统一高度 + 令牌间距**
理由：列表骨架追求"节奏一致"，不追求还原内容形状；高度取固定值（几何量），间距取 `--app-space-*`。

## Risks / Trade-offs

- [6 处首屏骨架观感从 EP 灰条变为共享骨架，视觉有变化] → 骨架本就是临时态，且统一到主题色更符合目标；tasks 含浏览器断言与逐页确认
- [加载期不挂载树组件，若取数极快可能出现"骨架一闪"] → 与现状（空态一闪）相比是改进；不引入人为延迟（拒绝为了好看加 setTimeout）
- [扩展 `SkeletonCard` 可能影响 `dashboard/StatsCard` 现有观感] → 默认 `variant` 保持 `card` 且原 4 条布局不变；tasks 含对该处的回归断言

## Migration Plan

1. 先扩展 `SkeletonCard`（默认档不变），再逐页替换，最后补两个工作台的骨架与 `el-alert` 替换
2. 回滚策略：纯前端渲染改动，回滚即 `git revert`；无数据、接口与路由迁移

## Open Questions

（无）