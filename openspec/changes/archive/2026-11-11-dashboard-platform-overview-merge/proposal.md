## Why

仪表盘当前是四个同权章节板：「平台运营」的五张运行指标卡与「测试资产」的用例项目卡，本质都是「平台里现在有多少东西」的计数快照，却各占一个与「AI 用量」同级的章节壳。两处拆开既多一段章节头，又让「平台现状」这层信息要在页面上扫两遍才能拼齐。

## What Changes

- 「平台运营」+「测试资产」合并为一个章节，标题改为 **「平台概览」**。
- 合并后仍按顺序展示在线设备、活跃智能体、运行中任务、任务数量、工作流五张 KPI 入口卡。
- 下方保留 **「测试用例」** 子标题（`Cases` tag），用例项目入口卡仍在该子区；用例数 chip 移到「平台概览」章节头右侧。
- 仪表盘章节数由四变三，顺序为：平台概览、AI 用量、趋势与动态。
- 数据口径、统计接口、卡片组件（KpiCard 入口卡）与整卡跳转行为全部不变。

## 关联文档

- 需求来源：需求方直接决策的仪表盘信息架构调整（合并两章、命名「平台概览」、保留「测试用例」小标题）。
- 受影响主 spec：`dashboard-chapter-boards`（章节钉板）、`dashboard-case-project-cards`（用例项目卡）。
- 前序变更参考：`2026-10-21-dashboard-remove-chapter-chips`（章节头 chip 规则）。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- `dashboard-chapter-boards`: 四章节 → 三章节；「平台运营」与「测试资产」合并为「平台概览」；用例数 chip 的归属改到新章节头。
- `dashboard-case-project-cards`: 测试用例子区的父章节由「测试资产」改为「平台概览」，子区标题为「测试用例」。

## Impact

- 前端：`frontend/src/modules/dashboard/index.vue`（章节结构）、`frontend/src/modules/dashboard/DashboardView.style.css`（章节色标与子区样式）。
- 后端 / 接口：无改动；`cases.total` 与 `cases.breakdown` 口径不变。
- 测试：`tests/dashboard/**` 为统计接口测试，不涉及章节 UI 文案，无需改动。
