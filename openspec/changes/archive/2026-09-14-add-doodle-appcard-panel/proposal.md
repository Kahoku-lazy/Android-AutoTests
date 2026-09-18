## Why

仪表盘趋势图等「内容分块」仍是 Element Plus 实线圆角 `el-card` / 旧 AppCard（实线 + 彩色顶条），与 hand-drawn doodle 参考页 `#page-typography` 的 `.panel` 钉板（虚线近直角、马克笔硬阴影、居中图钉、微倾）不一致。后续所有可复用数据块都应走同一壳，故升级共享 `AppCard`，并把仪表盘裸 `el-card` 收进去。

## What Changes

- 升级 `AppCard` 默认外观为钉板壳：虚线描边、近直角、硬偏移色阴影、可选居中图钉、微倾；去掉 4px 彩色顶条
- 同排多卡 accent **cycle**（复用 `sketchToneAt` / `sketchTiltAt`）
- 仪表盘趋势 4 张裸 `el-card` → `AppCard`
- 报告等已用 AppCard 的图表/表自动换皮
- **ECharts 画布内配色独立设计，允许硬编码**（不纳入本变更壳样式约束）
- 同步 `frontend/AGENTS.md` 与 doodle-craft 组件规格

## Capabilities

### New Capabilities

- `frontend-doodle-appcard-panel`：共享 AppCard 钉板壳、cycle accent、仪表盘趋势消费契约；ECharts 色板硬编码例外

### Modified Capabilities

- `frontend-l3-content-block`：数据块视觉对齐钉板；角色判据（分区 vs AppCard）不变

## Impact

- `frontend/src/shared/components/AppCard.vue`、`workbench-theme.css`、`style.css` 顶条规则
- `frontend/src/modules/dashboard/index.vue` + `DashboardView.style.css`
- 文档：`frontend/AGENTS.md`、doodle-craft `components.md`
- 不改：SketchCard、KpiCard、`.doc-section`、ECharts option 配色
