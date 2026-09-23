## Why

`StructureAnalysisPanel.vue` 已达 **624 行**，超过 `frontend/AGENTS.md` 硬性规范 6 的 500 行红线（「超过 500 行请务必拆分，**先拆样式层**，再拆逻辑层」）。该组件的样式块占 243 行（382–624），其中大量是表格容器、冻结列、拖拽滚动的 `:deep()` 规则。

## What Changes

- 把 `<style scoped>` 整块**逐字**抽到 `components/StructureAnalysisPanel.css`，`.vue` 改为 `<style scoped src="./StructureAnalysisPanel.css"></style>` —— 与同模块 `ScreenshotView.vue` 的既有做法一致
- 组件由 **624 行 → 381 行**，回到红线以内
- **BREAKING**：无（只移动样式声明的位置，选择器与值一字未改）

## 明确移出本变更范围

- 不拆逻辑层（`<script setup>` 200 行、`<template>` 179 行，均未超限，规则要求「先样式后逻辑」）
- 不抽子组件（会改动 props / 事件契约，属更大动作）
- 不改任何选择器、值、令牌引用

## 关联文档

- 需求编号：`PRD-03-设备检查器`（纯结构整理，无需求变更）
- 依据：`frontend/AGENTS.md` 硬性规范 6；同模块先例 `ScreenshotView.vue` + `ScreenshotView.css`

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

（无 —— 无 spec 级行为变化，`.openspec.yaml` 置 `skip_specs: true`）

## Impact

- 新增 `frontend/src/modules/device-inspector/components/StructureAnalysisPanel.css`（241 行）
- `frontend/src/modules/device-inspector/components/StructureAnalysisPanel.vue`（624 → 381 行）
- 后端 / 端点 / 依赖 / 迁移：零改动；观感与行为零变化