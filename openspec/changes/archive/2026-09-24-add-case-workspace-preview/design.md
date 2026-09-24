## Context

用例管理工作台（`/cases/projects/:projectId`）目前是单栏：整页只有 `ProjectTree.vue`，点文件跳 `/files/:fileId` 到 `CaseFileSheet.vue`（10 列 Excel 纸，可编辑）。元素定位工作台已按同一套「左树 + 右只读预览」落地并归档（`relayout-locator-workspace` → `preview-only-locator-pane` → `trim-locator-preview-columns` → `paginate-locator-preview` → `dedupe-locator-preview-cta`），本单是把同一版式与预览契约搬到用例侧。

可用资产：`api.ts` 的 `getFileSheet(fileId)`（返回 `{file, rows}`）、`types.ts` 的 `CaseDefinition`（含 `id / title / test_type / business_type / updated_at`）与 `TEST_TYPE_OPTIONS / BUSINESS_TYPE_OPTIONS`、共享 `usePagination`、共享 `AppTable`。

注意：`case-manager-projects` 能力在 `openspec/specs/` 下**没有主 spec**（只有 `2026-09-12-refactor-case-manager-projects` 归档单里的副本），属既有漂移，本单不顺手修，另立一单补齐。

## Goals / Non-Goals

**Goals:**

- 用例工作台补齐与元素定位一致的「左树 + 右只读预览」版式
- 右栏预览固定五列、只读、可分页、单一编辑入口
- 零后端改动、零写请求

**Non-Goals:**

- 不改 `ProjectTree.vue` 的树皮肤与拖拽 / 右键行为（本单只加右侧预览）
- 不改 `CaseFileSheet.vue` 的十列与编辑行为
- 不补 `case-manager-projects` 主 spec

## Decisions

**D1 新建 `CasePagePreview.vue`，不复用 `CaseFileSheet.vue`**
后者携带行内编辑、类型标签下拉、脏标记与路由离开守卫（`onBeforeRouteLeave`）等全部写路径；用 props 关掉它们会得到一个双模组件。预览件只调 `getFileSheet` 读数据，不导入任何写函数（`createDefinition` / `updateDefinition` / `deleteDefinition`）。

**D2 预览用共享 `AppTable` + 模块强调色**
五列是扁列表，走共享表纸（`accent="var(--c-case)"`），与元素定位预览同族；不为预览另造 Excel 网格皮肤。

**D3 分页走共享 `usePagination`**
每页固定 10 行、无行数选择器，与全站口径一致；页码在数据源变小时由 composable 自动夹取。

**D4 预览件按选中文件加 `:key`**
换文件即重置到第 1 页，避免页码跨文件残留。

**D5 窄屏沿用既有两页流程**
与元素定位同口径：`<1280px` 只渲染树，点文件跳 `/files/:fileId`。理由同前——`doc-page--fixed` 下唯一滚动在 `.doc-body`。

**D6 时间列取 `updated_at`**
`CaseDefinition` 同时有 `created_at` 与 `updated_at`；预览用于核对「最近改过哪些用例」，取更新时间更贴合。列头写「时间」，与详情页该列表头保持一致。

## 模块防火墙自检

- 跨 App import：无（纯前端）
- 写库 / ORM：无；预览件不导入写函数，右栏零写请求
- 前端 HTTP 出口：不变（只经 `modules/case-manager/api.ts` 的 `getFileSheet`）
- 引擎边界 / 通信通道：不涉及

## Risks / Trade-offs

- [预览五列不含步骤与预期，判断用例内容仍需进详情页] → 这是需求方指定的列集；缩略信息用于定位与筛选，正文在详情页
- [两模块工作台的树皮肤目前不同（元素定位紧凑行、用例仍是全宽描边行）] → 本次不改用例树皮肤，避免超出需求；左栏收窄到 320px 后「通栏巨框」问题自然消失，登记为后续可选对齐项
- [用例数超过接口单次上限时预览只能翻到取回的部分] → 复用详情页同款口径，超出时如实提示
