# SPEC — 测试报告模块重构

> 基于 SPEC-模块重构规范.md，针对 report-generator 模块的逐阶段执行计划。
> 版本：v1.0 · 日期：2026-07-25

---

## 当前状态快照

```
frontend/src/modules/report-generator/
├── index.vue                         350 行 · 页面编排者
├── index.css                          52 行 · ⚠️ 独立 CSS 文件（其他模块全用 scoped）
├── api.js                             72 行 · 数据层（10 端点）
├── routes.js                          26 行
├── constants.js                      159 行 · L4 达标
├── composables/                       ❌ 缺失 — 逻辑全内联在 index.vue
├── CaseBreakdown.vue                 431 行 · 用例故障分析子页
├── ReportDetail.vue                  460 行 · 单次报告详情子页
├── TaskReport.vue                    323 行 · 任务报告子页
└── components/
    ├── DailyPassFailChart.vue          88 行 · 日通过/失败柱状图
    └── PassRateTrendChart.vue          79 行 · 通过率趋势折线图
```

**架构评级**：L2 — 有 api.js/routes.js/constants.js，但缺 composables/。逻辑层处于 0 状态。

**已完成的改进**（前期重构）：

| 改进 | 状态 |
|------|:--:|
| KPI 卡片替换为 shared KpiCard × 4 | ✅ |
| 图表接入 useECharts composable × 2 | ✅ |
| catch(_){} 全部替换 | ✅ |
| 背景点阵纸纹 + 全局全宽 | ✅（全局生效） |

**关键问题**：

| 问题 | 严重度 | 说明 |
|------|:--:|------|
| **缺 composables/** | 🔴 | 唯一没有逻辑层的模块（digital-human 除外）。index.vue 350 行脚本全内联 |
| **独立 index.css** | 🟡 | 唯一有独立 CSS 文件的模块，应迁移到各 .vue 的 scoped |
| **旧 KPI CSS 未清理** | 🟡 | index.css + CaseBreakdown + ReportDetail + TaskReport 中仍有手写 `.kpi-card`/`.kpi-dot`/`.kpi-value` 样式（已死代码） |
| **字体不一致** | 🟡 | 用 `Caveat` 而非 `Patrick Hand`（DESIGN_SYSTEM.md §1.5 标准） |
| **section 标题用 emoji** | 🟢 | `📊 统计概览` 而非 `doc-section__title` + `doc-tag` 标准格式 |
| **ReportDetail 460 行** | 🟠 | 超标，子页无 composable |
| **CaseBreakdown 431 行** | 🟡 | 接近超标，需抽 composable |

---

## 阶段 1：基础设施统一 — 已完成 ✅

背景点阵 + 全宽已在全局生效。

---

## 阶段 2：清理死代码 — 旧 KPI CSS

### 问题

index.css 第 12-17 行仍有手写 KPI 卡片样式，ReportDetail / CaseBreakdown / TaskReport 的 scoped CSS 中也有同份拷贝：

```css
/* ❌ 死代码 — KpiCard 组件已接管渲染 */
.kpi-card { ... }
.kpi-dot { width:10px;height:10px;transform:rotate(45deg); ... }
.kpi-value { font-family:'Caveat',cursive;font-size:30px; ... }
.kpi-label { font-size:10px;font-weight:700;opacity:0.4; ... }
.kpi-card::after { content:'~'; ... }
```

### 操作

1. 删除 index.css 中的 `.kpi-card` / `.kpi-dot` / `.kpi-value` / `.kpi-label` / `.kpi-card::after` 规则块
2. 删除 ReportDetail.vue / CaseBreakdown.vue / TaskReport.vue 中同样的规则
3. `.kpi-row` 保留（网格布局由各模块自行控制）

---

## 阶段 3：字体统一 + section 标题标准化

### 3.1 字体

```
Caveat → Patrick Hand
```

影响范围：index.css `.section-title`、`.kpi-value`、`.kpi-label`、`.kpi-card::after`。`kpi-*` 相关样式随阶段 2 一并删除，只需修 `.section-title`。

### 3.2 section 标题

```
❌ 当前：
<span class="section-title">📊 统计概览</span>

✅ 目标（对齐仪表盘/设备管理/执行引擎）：
<div class="doc-section__header">
  <h3 class="doc-section__title">统计概览 <span class="doc-tag">Overview</span></h3>
  <span class="doc-section__label">测试执行统计与趋势总览</span>
</div>
```

两个 `.info-card` 改为两个 `<section class="doc-section">`：

```
.info-card（统计概览）→ <section class="doc-section report-stats">
.info-card（数据图表）→ <section class="doc-section report-charts">
```

CSS 迁移：`.info-card` 的背景/边框/阴影 → scoped `.doc-section`；手绘下划线 → 复用 `.doc-section__title::after`（从 dashboard 复制 SVG）。

---

## 阶段 4：提取 composables — 补全逻辑层

### 4.1 useReportData.js（~120 行，从 index.vue 抽）

```javascript
export function useReportData() {
  const runs = ref([])
  const summary = ref(null)
  const bugSummary = ref(null)
  const trend = ref(null)
  const loading = ref(false)

  async function fetchReports(params) { ... }
  function clearFilters() { ... }

  const hasActiveFilters = computed(() => ...)
  const filteredRuns = computed(() => ...)
  const lastUpdated = computed(() => ...)

  return { runs, summary, bugSummary, trend, loading,
           fetchReports, clearFilters, hasActiveFilters,
           filteredRuns, lastUpdated }
}
```

index.vue 的 `<script>` 从 ~200 行缩减到 ~100 行。

### 4.2 useReportCharts.js（~40 行，从 index.vue 抽）

图表范围切换（30天/90天）逻辑 + chartRange ref + setChartRange 函数。

---

## 阶段 5：CSS 文件合并 — 消除独立 index.css

### 问题

`index.css` 是全局注入样式，影响整个模块的 4 个 `.vue` 文件。不符合 Vue scoped CSS 约定。

### 操作

1. 将 index.css 中仍在使用且非全局的规则迁移到 `index.vue` 的 `<style scoped>`
2. 将图表/表格相关规则迁移到对应组件的 scoped CSS
3. 删除 `index.css`

---

## 阶段 6：模块颜色收束

| 当前 | 应该 | 位置 |
|------|------|------|
| `.info-card` 边框 `var(--ink)` | `var(--c-report)` `#7C6F83` | index.vue scoped |
| `.btn-sm:hover` `var(--c-dashboard)` 黄色 | `var(--c-report)` 灰紫 | index.vue scoped |
| 图表范围按钮 `.page-size-btn.active` 通用色 | 保持通用（图表工具栏不属于模块色范围） | — |

---

## 阶段 7：子页面瘦身

### 7.1 ReportDetail.vue (460 行)

拆分：`components/ReportDetailHeader.vue`（元数据条 ~80 行）+ `components/ReportCaseDetails.vue`（用例折叠面板 ~120 行）

### 7.2 CaseBreakdown.vue (431 行)

拆分：逻辑抽 `composables/useCaseBreakdown.js`（API 调用 + 数据聚合 ~80 行）

### 7.3 TaskReport.vue (323 行)

行数合理（阈值内），不需拆。

---

## 阶段 8：PRD 更新

参照 PRD-00 格式更新 PRD-05-测试报告.md。

---

## 执行顺序

```
1. 清理死代码（旧 KPI CSS）         →  0.5h  ─ 消除误导
2. 字体统一 + section 标题标准化     →  1h    ─ 视觉一致
3. CSS 合并（index.css → scoped）    →  1h    ─ 架构一致
4. 提取 composables（逻辑层补全）    →  2h    ─ L2→L3
5. 模块颜色收束                     →  0.5h  ─ CSS 替换
6. 子页面瘦身                       →  3h    ─ 460/431→350
7. PRD 更新                         →  1h
                                    ─────
                                     9h
```

## 验证

```bash
# 每阶段后
npx vite build --mode development

# 完成后
ls modules/report-generator/composables/  # 应存在
grep "Caveat" modules/report-generator/ --include="*.vue" --include="*.css" -r  # 应为空
grep "kpi-dot\|kpi-card\b" modules/report-generator/ --include="*.css" -r  # 应为空
wc -l modules/report-generator/index.css  # 应不存在
```
