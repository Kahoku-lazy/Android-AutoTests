# PRD-05 — 测试报告 (Report Generator)

> 关联需求大纲：[`需求大纲.md`](./需求大纲.md) §5.6
> 版本：v6.1 · 日期：2026-07-27

---

## 1. 功能定位

测试报告是执行结果收口。用户在此查看历史执行记录、分析通过率趋势、定位失败原因、下载文件归档。页面由三个区域自上而下排列：统计概览 → 数据图表 → 测试报告列表。

---

## 2. 设计目录

```
frontend/src/modules/report-generator/
├── index.vue                         359 行 · 报告列表页（编排者，ErrorState + RateBar 接入）
├── index.css                          44 行 · scoped CSS（src 引入，rate 相关 6 条规则已迁移到 RateBar）
├── api.js                             72 行 · 数据层（10 端点 + 5 工具函数）
├── routes.js                          26 行 · 路由定义
├── constants.js                      159 行 · L4 达标（图表颜色/样式/列定义/路由/状态映射）
├── composables/                       ⚠️ 尚未创建 — 内联逻辑待提取
├── CaseBreakdown.vue                 431 行 · 用例故障分析子页
├── ReportDetail.vue                  446 行 · 单次报告详情子页（useExpandCollapse + 死代码清理）
├── TaskReport.vue                    323 行 · 任务报告子页
└── components/
    ├── DailyPassFailChart.vue          88 行 · 日通过/失败柱状图
    └── PassRateTrendChart.vue          79 行 · 通过率趋势折线图

共享层新增（本模块使用）：
├── shared/composables/useExpandCollapse.js  通用展开/折叠 Set-toggle
└── shared/components/RateBar.vue            通用通过率进度条
```

**架构特征**：L3 评级（原 L2）。错误态已补全（ErrorState），通过率进度条已组件化（RateBar），子页面展开/折叠已接入 useExpandCollapse 消除 3 处重复。composables/ 本地逻辑层仍待提取。

---

## 3. 核心功能

### 3.1 统计概览

页面顶部区域，包含筛选栏 + 4 张 KPI 卡片。

#### 3.1.1 筛选栏

5 个筛选控件水平排列：日期范围选择器 → Run ID 输入 → 任务名称输入 → 设备输入 → 创建人输入。右侧显示执行统计摘要（"共 N 次执行 · M 次迭代"）。有筛选条件时显示"清空条件"按钮。

#### 3.1.2 KPI 卡片

| 卡片 | 颜色 | 图形 | 数据来源 | 交互 |
|------|:--:|:--:|------|------|
| 总执行次数 | `var(--c-workflow)` 天蓝 | ◆ 菱形 | `summary.total_runs` | — |
| 通过 | `var(--c-device)` 薄荷绿 | ▲ 三角 | `summary.total_pass` | 点击 → 跳转用例通过明细 |
| 失败 | `var(--c-runner)` 桃粉 | ■ 方块 | `summary.total_fail` | 点击 → 跳转用例故障分析（含 Bug 统计子文本） |
| 通过率 | `var(--c-dashboard)` 柠黄 | ● 圆 | `summary.pass_rate`% | 显示迭代次数子文本 |

**组件**：`shared/components/KpiCard.vue`

### 3.2 数据图表

双图表并排展示（仅在有趋势数据时显示）。

#### 3.2.1 工具栏

图表范围切换按钮：30 天 / 90 天，默认展示最近 `CHART_VISIBLE_DAYS` 天。数据不足时显示对应提示。

#### 3.2.2 通过率趋势折线图

单系列折线 + 渐变面积填充。dataZoom 滑块支持缩放和拖拽查看历史数据。

**组件**：`PassRateTrendChart.vue`，props: labels / rate / visibleDays / group

#### 3.2.3 每日通过/失败柱状图

双系列分组柱状图（通过=绿色 / 失败=红色）。dataZoom 滑块支持缩放。

**组件**：`DailyPassFailChart.vue`，props: labels / pass / fail / visibleDays / group

两个图表通过 `echarts.connect('report-trend')` 联动缩放。

### 3.3 测试报告列表

AppTabs 切换三组报告：

| Tab | 内容 | 表格列 |
|------|------|------|
| 全部 | 所有报告 | Run ID(下划线链接) · 设备 · 用例数 · 通过 · 失败 · 通过率(进度条) · 状态(标签) · 创建时间 |
| 已完成 | `status === 'completed'` | 同上 |
| 未完成 | 其他状态 | 同上 |

通过率列渲染为双色进度条（绿色=通过占比，红色=失败占比）+ 百分比文字。颜色规则：≥90% 绿色、60-90% 黄色、<60% 红色。报告为空时显示 EmptyState。

点击 Run ID → 跳转 `/reports/{id}` 详情页。

---

## 4. 子页面

### 4.1 ReportDetail — 报告详情

4 张 KPI 卡片（执行用例/通过/失败/通过率）+ 任务元数据条 + 3 个 Tab（用例明细/失败分析/性能统计）。

### 4.2 CaseBreakdown — 用例故障分析

按用例聚合失败数据。顶部 3 张 KPI 卡片（独立问题数/问题出现次数/涉及用例），下方按用例展开的折叠面板。

### 4.3 TaskReport — 任务报告

4 张 KPI 卡片（总迭代次数/通过/失败/通过率）+ 任务元数据条 + 用例折叠面板。底部 5 个 `perf-stat-item` 性能统计卡片。

---

## 5. 数据流

```
GET /report-generator/runs/ (listRuns)
  ├── runs[]          原始执行记录列表
  ├── summary         统计摘要（total_runs/total_pass/total_fail/pass_rate）
  ├── bugSummary       Bug 聚合（unique_issues/total_occurrences/affected_cases）
  └── trend           趋势数据（labels/pass/fail/rate）

index.vue (内联逻辑)
  ├── hasActiveFilters   筛选激活判定
  ├── filteredRuns       按日期/ID/名称/设备/创建人过滤
  ├── chartRange         图表范围切换（30/90 天）
  └── pagedRuns          分页（usePagination composable）
```

---

## 6. 验收汇总

| 功能编号 | 功能名称 | 验收项 | 通过 | 未验证 |
|:--:|------|:--:|:--:|:--:|
| F-01-01 | 统计概览（KPI 卡片 + 筛选） | 6 | | 6 |
| F-01-02 | 数据图表（趋势 + 每日统计） | 4 | | 4 |
| F-01-03 | 报告列表（3 Tab + 进度条） | 6 | | 6 |
| F-02-01 | 报告详情（用例执行明细） | 4 | | 4 |
| F-02-02 | 用例故障分析 | 3 | | 3 |
| F-02-03 | 趋势图表 | 3 | | 3 |
| F-03-01 | 文件下载 | 4 | | 4 |
| **合计** | | **30** | **0** | **30** |

---

## 附录A：测试优先级

| 优先级 | 覆盖范围 | 验收时机 |
|:--:|------|------|
| P0 | F-01-01~F-02-01（统计+图表+详情） | 每次 MR 前 |
| P1 | F-02-02~F-03-01（故障分析+下载） | 发版前 |

## 附录B：实施状态

| 功能 | 状态 |
|------|:--:|
| 报告列表 + 筛选 + 3 Tab | ✅ |
| KPI 卡片（拍立得 × 4，含 Bug 子文本） | ✅ v6.0 |
| 数据图表（useECharts 接入） | ✅ v6.0 |
| Section 标准化（doc-section + 手绘下划线） | ✅ v6.0 |
| 字体统一（Caveat→Patrick Hand） | ✅ v6.0 |
| 模块色收束（c-dashboard→c-report） | ✅ v6.0 |
| 旧 KPI CSS 死代码清理 | ✅ v6.0 |
| ErrorState 错误处理补全 | ✅ v6.1 |
| RateBar 通过率进度条组件化 | ✅ v6.1 |
| useExpandCollapse 接入（消除 3 处 Set-toggle 重复） | ✅ v6.1 |
| FAIL_CARD_PALETTE 死代码清理 | ✅ v6.1 |
| 在线详情 3 Tab | ✅ |
| CSV/LOG 下载 | ✅ |
| 趋势图表 | ✅ |
| composables/ 逻辑层补全 | 📋 |
| 报告模板管理 | 📋 |
| PDF 导出 | 📋 |

## 附录C：已知问题与改进项

| 编号 | 问题 | 严重度 | 记录日期 |
|:--:|------|:--:|:--:|
| IMP-01 | 缺 composables/，逻辑全内联在 index.vue（L2→L3 待升级） | 🟠 | 2026-07-25 |
| IMP-02 | ReportDetail.vue 446 行超标（已减 14 行，仍需拆子组件） | 🟠 | 2026-07-25 |
| IMP-03 | CaseBreakdown.vue 431 行接近超标 | 🟡 | 2026-07-25 |
| IMP-04 | index.css 为独立文件（scoped src 引入），不同于其他模块的内联 `<style scoped>` | 🟢 | 2026-07-25 |
| IMP-05 | 无错误态 — **已修复 v6.1**：index.vue 添加 ErrorState + error ref | ✅ | 2026-07-27 |
| IMP-06 | 3 处手写 Set-toggle 展开/折叠 — **已修复 v6.1**：接入 useExpandCollapse | ✅ | 2026-07-27 |
| IMP-07 | 内联 rate-bar 进度条 — **已修复 v6.1**：替换为共享 RateBar 组件 | ✅ | 2026-07-27 |
