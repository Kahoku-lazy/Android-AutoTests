## Context

`LocatorPagePreview.vue` 目前用 `rows.slice(0, 6)` 截首屏。`usePageElements` 已经内建共享分页（`usePagination`，每页固定 10 行、边界自动夹取 `currentPage`），并暴露 `currentPage / totalPages / pagedItems / goPage`——上一单没用它们，是因为当时右栏定位为「概览位只给首屏」。现在右栏要能浏览全部元素，直接改用这套既有状态即可，不需要新状态机。

## Goals / Non-Goals

**Goals:**

- 右栏可浏览该页全部元素：每页 10 行 + 「第 X / Y 页 · 共 N 条」+ 上一页 / 下一页（边界禁用）
- 与详情页共用同一套分页口径（同一 composable、同一文案），不新造分页

**Non-Goals:**

- 不改每页行数、不加行数选择器（全站口径：固定 10 行，无选择器）
- 不把右栏页码带到详情页（进详情页从第 1 页开始）
- 不引入编辑能力，不改三列口径

## Decisions

**D1 复用 `usePageElements` 的分页状态，不自算页码**
`usePageElements` → `usePagination` 已经实现「数据源变小自动夹取 `currentPage`」「文案与按钮口径」；预览只消费 `pagedItems / currentPage / totalPages / goPage`。页面自算 `totalPages` 或自写 `goPage` 属既有规范明令禁止。

**D2 去掉截断表达，页脚同时承担页码与入口**
页脚左侧为分页（文案 + 上一页 / 下一页），右侧为「进入页面编辑」。不再出现「还有 N 条未显示」这类截断文案——因为已经没有看不到的元素。

**D3 预览件按选中页面加 `:key`**
工作台右栏在两个页面之间切换时复用同一组件实例，`currentPage` 会跨页面残留（新页面恰好更短时尤其困惑）。给预览件加 `:key="selectedFile.id"`，换页面即重置到第 1 页。

**D4 表格固定高度 + 表体内部滚动**
预览每页 10 行会高于右栏可用高度，`AppTable` 以 `height="100%"` 在表体内部纵向滚动、表头固定（既有 `AppTable` 能力，与详情页同款）。

## 模块防火墙自检

- 跨 App import：无
- 写库 / ORM：无；右栏仍零写请求（只读接口未变）
- 前端 HTTP 出口：不变（`pages/{id}/items/` 仍一次取回上限 500 条，本地分页）
- 引擎边界 / 通信通道：不涉及

## Risks / Trade-offs

- [右栏现在能浏览全部元素，与详情页功能重叠] → 重叠仅在「读」，写入口仍唯一；这是需求方的明确选择
- [一次取回上限 500 条，超出时右栏只能翻到取回的部分] → 复用既有 `truncated` 口径，超出时按详情页同样方式如实提示（不假装是全部）
