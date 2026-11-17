## Why

BUG 管理页只有 4 张 KPI 卡和一张表格：能知道「有多少」，看不出「分布长什么样」——待处理是不是集中在某一类任务、已解决占比多少，都要靠肉眼数表格。测试报告页已经有成体系的统计图表，BUG 页目前是唯一的「有数据但没有图形表达」的页面。

## What Changes

- 在「BUG 概览」下方新增「BUG 分布」区块：
  - 左侧环形图 = 处理状态（待处理 / 已解决 / 已忽略），圆心显示 BUG 总数；
  - 右侧条形图 = 任务类型（UI 自动化 / 用例编写）。
- 数据全部取自列表接口已返回的 `summary`，不新增接口、不在前端重算业务口径。

## 关联文档

- 复用测试报告页的图表底座（`useECharts`）与 Doodle 主题卡片/区块样式；不新增第二套视觉。

## Capabilities

### New Capabilities

- 无

### Modified Capabilities

- `bug-ticket-management`: 新增「BUG 分布图表」要求，明确图表数据源与两种维度。

## Impact

- 前端：`modules/bug-manager/{index.vue,components/BugDistributionChart.vue,helpers/bugDistribution.ts}` 与一条单测。
- 后端 / 接口：无改动。
