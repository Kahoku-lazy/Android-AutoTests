## Context

- 行数构成（拆分前）：`<script setup>` 1–200、`<template>` 202–380、`<style scoped>` 382–624；样式块 243 行中约 1/3 是 `:deep()` 规则（`.sap-table-body :deep(.el-table__body)` 等），承担表格最小宽、冻结列、拖拽滚动光标、复选框可点等。
- 同模块先例：`ScreenshotView.vue` 用 `<style scoped src="./ScreenshotView.css">`；其它模块用 `*.style.css` + 同样写法（`DevicePoolView.style.css` 等）。本变更照同模块命名（`ScreenshotView.css` 无 `.style` 中缀）。
- 关键不确定性：`:deep()` 在**外部** scoped 样式表里是否仍被作用域转换（`ScreenshotView.css` 里没有 `:deep()`，因此本模块没有直接先例）。若未转换，表格的高度锁定与滚动条皮肤会失效——必须真机核对。

## Goals / Non-Goals

**Goals:**

- 组件回到 500 行红线内，且样式规则逐字不变（可 diff 验证）
- `:deep()` 规则在外部 scoped 样式表里仍然生效（真机证据）

**Non-Goals:**

- 不拆逻辑层 / 不抽子组件
- 不重命名或合并选择器、不调整规则顺序
- 不引入 CSS 变量或令牌改动

## Decisions

**D1 抽成外部 `.css` 而不是拆成子组件**
理由：规范明确「先拆样式层，再拆逻辑层」；样式层拆分对运行时零影响（同选择器、同顺序、同作用域），而抽子组件要重新定义 props/事件与 `store` 依赖，属下一次动作。

**D2 文件名为 `StructureAnalysisPanel.css`（不用 `.style.css`）**
理由：同模块既有 `ScreenshotView.css`；模块内命名一致优先于跨模块命名。

**D3 用 `<style scoped src=...>` 而不是 `main.ts` 全局导入**
理由：该样式含 `.sap-*` 组件私有类与 `:deep()`，必须保持 scoped；`main.ts` 导入会丢作用域（`tokens.css` 那种全局令牌文件才走 `main.ts`）。

## 模块防火墙自检

- 跨 App import：零新增；不涉及后端、端点、令牌与共享层
- 前端不直连数据库 / 无写库：不涉及
- HTTP 出口：不变
- 迁移：零

## Risks / Trade-offs

- [`:deep()` 在外部 scoped 样式表里未按预期转换] → 真机核对两条由 deep 规则产生的计算样式：`.el-table__body` 的 `min-width` 应为列宽合计 **986px**、`.el-scrollbar__wrap` 的 `cursor` 应为 **grab**；并检查编译后的样式表规则是否带 `[data-v-*]` 作用域；不通过则回退为「保留 style 块、另拆 `<script>`」
- [样式顺序变化导致覆盖关系改变] → 拆分是整块迁移，单文件内相对顺序不变；真机对表格纸皮肤与冻结列做视觉核对
- [构建期不识别 `src` 外部样式] → `vite build` 与 `lint:styles` 双门禁；`lint:styles` 会扫描 `.css` 文件与 `.vue` 的样式块，能覆盖拆出的文件

## Migration Plan

1. 抽出样式块 → 校验行数与规则数
2. 真机核对 deep 规则与渲染（表格最小宽 / 滚动容器光标 / 复选框可点 / 冻结列底色）
3. 门禁：`lint:styles` + `vite build` + `vitest tests/device-inspector`
4. 回滚：`git revert` 两文件；无数据迁移

## Open Questions

（无）
