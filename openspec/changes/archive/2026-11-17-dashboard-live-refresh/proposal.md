## Why

仪表盘页头有一个手动「刷新」按钮，用户得自己点；章节头同时挂着英文 eyebrow 与描述行，同一层级出现三种文字；页脚的「最近更新 / 系统状态」放在滚动容器里，滚到下面时这两条信息就跑掉了。三处都是“信息在，但位置不对”。

## What Changes

- **章节头瘦身**：「平台运营 / AI 用量 / 测试资产 / 趋势与动态」保留模块色方标与中文标题，删除英文 eyebrow（Platform Ops 等）与描述行。
- **自动刷新**：删除页头「刷新」按钮；改为每 5 秒静默拉取一次，数据指纹没变就什么都不做（也不动「最近更新」），变了才更新。
- **页脚固定**：「最近更新 / 系统状态」移出内容滚动容器，固定在页面底部。

## 关联文档

- 无 PRD 编号；对齐既有规格 `dashboard-chapter-boards`（本次修改其章节头要求）与 `frontend-l3-container`（滚动归属）。

## Capabilities

### New Capabilities

- `dashboard-live-refresh`: 仪表盘 5 秒静默轮询（仅数据变化才刷新）与固定页脚。

### Modified Capabilities

- `dashboard-chapter-boards`: 章节头不再要求英文 eyebrow 与描述行，改由模块色方标 + 中文标题表达层级。

## Impact

- 前端：`modules/dashboard/index.vue`、`DashboardView.style.css`、`composables/useDashboardStats.ts`、`composables/useDashboardAutoRefresh.ts`、`tests/dashboard/p1/dashboardAutoRefresh.spec.ts`。
- 后端 / 接口：无改动（仍只读既有统计与活动接口）。
