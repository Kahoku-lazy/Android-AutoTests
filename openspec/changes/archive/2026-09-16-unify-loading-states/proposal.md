## Why

全站首屏加载有 5 种写法（`v-loading` 12 处、`el-skeleton` 6 处、模块私有 `__loading` 容器 4 处、共享 `SkeletonCard` 仅 1 处、品牌 `WbLoader` 1 处），同一角色读起来不像一套语言。更严重的是**两个页面完全没有加载态**：`case-manager/ProjectWorkspace.vue` 与 `element-locator/ProjectWorkspace.vue` 的 composable（`useProjectTree` / `useLocatorTree`）都暴露了 `loading`，但页面没有解构使用，加载期间 `tree` 为空 → 子树的 `<EmptyState v-if="!treeData.length">` 抢先渲染"暂无目录或文件"，把**加载中显示成空态**。另有一处用 `el-alert` 顶替错误态。

## What Changes

- **修假空态**：两个 ProjectWorkspace 解构 `loading`，加载期间渲染共享 `SkeletonCard`，加载完成后才挂载树组件（避免 `EmptyState` 抢跑）
- **错误态调用点统一**：`element-locator/components/PageElementsWorkbench.vue` 的 `el-alert` 换成共享 `ErrorState`（带重试），与同模块其余 4 处一致
- **区块级骨架统一到共享件**：为 `SkeletonCard` 增加 `variant="list"`（N 条等高占位），替换 6 处裸 `el-skeleton` 并删除 4 处模块私有 `__loading` 容器及其死 CSS
- **登记分层口径**：区块/首屏骨架 → `SkeletonCard`；原地操作遮罩 → `v-loading`；表格 → `AppTable :loading`；需要品牌文案的整页等待 → `WbLoader`（登记为例外）
- **BREAKING**：无

## 关联文档

- `dev_docs/DEV_TEST/前端UI风格一致性分析-2026-09.md` §3.5 与 §八·批次 B
- `dev_docs/DEV_TEST/前端UI一致性整改计划.md` 阶段 2 · `unify-loading-states`
- 既有共享件：`shared/components/patterns/{SkeletonCard,EmptyState,ErrorState}.vue`

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `frontend-l3-content-block`：新增要求「三态渲染有唯一实现」

## Impact

- 新增/扩展：`frontend/src/shared/components/patterns/SkeletonCard.vue`（`variant="list"`）
- 修假空态：`modules/case-manager/ProjectWorkspace.vue`、`modules/element-locator/ProjectWorkspace.vue`
- 骨架替换：`modules/case-manager/ProjectList.vue`、`modules/element-locator/ProjectList.vue`、`modules/element-locator/LocatorFileView.vue`、`modules/element-locator/components/LocatorFilePanel.vue`、`modules/element-locator/components/PageElementsWorkbench.vue`、`modules/workflow/PrototypeList.vue`
- 错误态：`modules/element-locator/components/PageElementsWorkbench.vue`
- 观感变化：6 处首屏骨架由 EP 默认灰条改为共享暖色骨架；两个项目工作台由"假空态"改为骨架
- 不影响：12 处 `v-loading`（原地遮罩分层，本次不改）、`WbLoader`、接口与数据

## 登记为后续变更的输入（本变更不做）

- `ai-assistant/index.vue` 的 `WbLoader` 是否收敛为 `SkeletonCard` → 待品牌 loader 口径确认，暂登记为例外
- `AppTable` 内部 `v-loading` 与表格骨架的取舍 → 变更 9