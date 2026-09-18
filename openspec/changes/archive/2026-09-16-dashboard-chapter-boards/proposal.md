## Why

仪表盘 KPI 卡已是 doodle 钉板风，但六个 `.doc-section` 同权扁平堆叠：无章节容器、灰字摘要像调试输出、用例与元素同构却拆成两段。布局层级与 Hand-Drawn Doodle 主题不搭，扫描成本高。

## What Changes

- 将仪表盘信息架构收束为 **4 个章节钉板**：平台运营、AI 用量、测试资产、趋势与动态
- 章节头改为：彩色方标 + 英文 eyebrow + marker 标题；摘要改为 chip，去掉多行裸灰字
- 测试用例与元素定位合并为「测试资产」一章双栏
- 仅改仪表盘前端布局/样式；不改 API、不改 StatsCard / AppCard 契约

## 关联文档

- 原型：`dev_docs/项目笔记/平台前端主题参考模版/dashboard-chapter-board-proto.html`
- 主题参考：`dev_docs/项目笔记/平台前端主题参考模版/hand-drawn-doodle-sidebar.html`
- UI 约束：`frontend/AGENTS.md` L3 分区 vs AppCard 判据；doodle-craft layout/components

## Capabilities

### New Capabilities

- `dashboard-chapter-boards`：仪表盘四章节钉板信息架构与章节头/chip/双栏资产区的可观察行为

### Modified Capabilities

- （无）L3「分区用 `.doc-section`、数据块用 AppCard」判据不变；本变更只增强仪表盘分区视觉与分组

## Impact

- `frontend/src/modules/dashboard/index.vue`
- `frontend/src/modules/dashboard/DashboardView.style.css`
- 可能微调 `DashboardView.logic.ts`（仅展示辅助，无新接口）
- 相关前端单测（若有布局断言）
- 不改：`apps/`、仪表盘 API、共享 StatsCard / AppCard 实现
