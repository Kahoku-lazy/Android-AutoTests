## Context

仪表盘 `index.vue` 的 `.ch-ai` 章节头当前有 5 枚 chip：累计 Token、任务、费用、角色·累计、角色·今日。下方 5 张 `StatsAppCard` 已展示任务数量、累计 Token、缓存命中率、平均每任务 Token、DeepSeek 费用（今日在 `desc`、累计在主数值）。每张卡经 `StatsCard` 固定传入 `enter-label="进入"`，全部 `path="/ai-assistant"`。

`KpiCard` entry：`enterLabel` 为空则不渲染按钮；`clickable` 显式为 true 时整卡仍可点。`StatsCard` 已 `:clickable="!!path"`。

## Goals / Non-Goals

**Goals:**

- 去掉 AI 章节头与 KPI 重复的三枚 chip
- AI 区 KPI 卡不再显示「进入」，整卡跳转保留
- 其它章节 chip / 进入按钮不变

**Non-Goals:**

- 不改 stats API 与字段映射
- 不改 `KpiCard` 默认 `enterLabel: '进入'`
- 不去掉角色 chip，不改趋势图与活动流
- 不在本变更中改平台运营 / 测试资产的「进入」

## Decisions

1. **只动 AI 章节，不全局关「进入」。** 运营区「进入」仍是模块入口信号；AI 区五卡同路径，按钮冗余。实现：`StatsCard` 增加可选 prop（如 `showEnter`，默认 `true`），AI 五卡传 `false` / 空 `enterLabel`。禁止改 `KpiCard` 默认值以免波及其它 entry 用法。

2. **整卡仍可点。** 用户点选的是按钮与 chip，不是取消导航。`path` 仍为 `/ai-assistant`，`clickable` 仍跟 `path`。

3. **章节头只留角色 chip。** Token/任务/费用与 KPI 主数值重复；角色拆解只在 chip 上出现，必须保留。空 `chip-row` 时仍渲染角色 chip；若无角色数据则沿用现有 `roleBreakdown` 展示逻辑，不另造空态。

4. **规格增量写在既有 capability。** `dashboard-chapter-boards` 管章节头 chip；`dashboard-ai-usage` 管用量卡外观。不新增 capability。

## Risks / Trade-offs

- [P2] 用户点选了 AI 网格中 4 张卡的「进入」（未含第一张「任务数量」）。按同一冗余原因五张全部去掉「进入」，避免一卡有按钮四卡没有。
- [P2] `StatsCard` 单测目前断言有 `path` 时存在 `.kpi-card__enter`。默认 prop 为 true 则既有用例仍过；需补 `showEnter=false` 用例。

## Migration Plan

无数据迁移。前端合并后即时生效。

## Open Questions

无。角色 chip 无数据时的现有行为保持不变。
