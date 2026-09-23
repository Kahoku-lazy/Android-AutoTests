## Why

仪表盘「趋势与动态」里的最近活动区随条目多少伸缩，条目少时区块塌成一条标题，条目略多时又挤不出稳定的十条阅读面；同时接口最多只吐 10 条且当前实现几乎只聚合智能体更新，用户无法从主屏进入更早记录。需要固定十条可视槽位，并提供「查看历史」入口。

## What Changes

- 最近活动列表区 **预留恰好十条信息的可视高度**（不足十条时保留空白槽，超过十条时主屏只展示最新十条并在区内滚动）
- 标题行增加 **「查看历史」按键**，打开本页弹层列出更早活动，不新增路由、不改侧栏
- `GET /api/dashboard/activities/` 增加只读分页查询参数（默认仍为首页十条）；历史弹层走同一端点拉取后续页
- 活动聚合补齐当前平台真实数据源（助手任务卡 + 智能体更新），不再假装存在已删除的 `TestRunRecord`
- 不新增仪表盘自有表、不引入写操作

## 关联文档

- PRD-需求总纲（仪表盘：活动时间线）。无独立 PRD-01 子文档。

## Capabilities

### New Capabilities

- `dashboard-activity-timeline`：仪表盘最近活动十条可视槽、历史按键与分页只读查询的可观察行为

### Modified Capabilities

- （无）`dashboard-chapter-boards` 四章节结构与只读聚合语义不变；本变更只增强「趋势与动态」内活动面。

## Impact

- 后端：`apps/dashboard/views.py`（`DashboardActivitiesAPIView`）、`apps/dashboard/urls.py`（契约不变路径）、相关 graybox 单测
- 前端：`frontend/src/modules/dashboard/components/ActivityTimeline.vue`、`api.ts`、`composables/useDashboardStats.ts`、`DashboardView.style.css` / `index.vue`（仅必要接线）、`frontend/tests/dashboard/p1/ActivityTimeline.spec.ts`
- 文档：接口说明与实现对齐（分页参数、数据源）；不改 KPI / 趋势图契约
