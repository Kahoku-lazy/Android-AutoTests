## Context

- `TaskReport.vue` 共 356 行，`<style scoped>` 仅 11 行（压缩式），模板引用约 40 个类，其中约 25 个在本文件与全仓均无定义。动机见 `proposal.md`。
- 失效机制：Vue 的 `<style scoped>` 会给选择器追加 `[data-v-<hash>]`，因此兄弟组件里的同名规则**作用不到本组件**：
  - `ReportDetail.vue` 的 `.progress-bar/.p-pass/.p-fail/.rate-cell`（scoped）
  - `CaseBreakdown.vue` 的 `.case-header/.step-list/.case-list`（scoped）
  - `KpiCard.vue` 的 `.kpi-card`（scoped，模板却直接写 `class="kpi-card perf-stat-item"`）
  - `views/NotFound.vue` 的 `.not-found`（scoped）
- 本文件已定义但模板未使用的样式：`.task-meta-card` / `.meta-item` / `.meta-label` / `.meta-value` —— 模板写的是 `.task-meta-bar` / `.task-meta-item`，属类名不匹配。
- 既有可用范式（同模块内已存在）：`index.vue:338` `<RateBar :rate=... :show-fail=... />`；`index.vue:213-218` 与 `ReportDetail.vue:197-202` 用 `<KpiCard>` 渲染指标行；`index.vue:356` 用 `<EmptyState icon text hint />`。
- 共享件契约（已核实）：`RateBar` props `rate`（Number，必填）/ `showFail`（默认 true）/ `showLabel`（默认 true），自带 95 / 80 阈值配色；`KpiCard` props `value/label/color/shape/variant`；`EmptyState` props `icon/text(必填)/hint`。
- 判据要求：`frontend-l2-page-region`「No L2 declaration without a consumer」（页面不得保留无 CSS 规则消费的标记类）、「L2 page roots reuse the shared page skeleton」、「Every L2 page root provides the workbench theme scope」；`frontend-l4-data-surface`「Cards and grids reuse shared parts」。

## Goals / Non-Goals

**Goals**

- 本页所有模板类都有本作用域的 CSS 规则消费，页面不再出现无样式裸块
- 性能指标行复用共享 `KpiCard`，通过率复用共享 `RateBar`，整页空态复用共享 `EmptyState`
- 通过率进度条在视觉上可见（含失败段）
- "任务未找到"分支回到共享骨架与工作台主题作用域内
- 新增样式全部走设计令牌，不引入新的硬编码色 / 字号 / 对称圆角 / 模糊阴影

**Non-Goals**

- 不把用例/步骤卡片抽成共享组件（`CaseBreakdown` 结构不同，需先统一数据形状）→ 变更 9
- 不改本页 `.detail-tabs` 对 `AppTabs` 的重写皮肤 → 变更 7
- 不改 `constants.ts` 的死常量与 `.doc-section` 口径 → 变更 14 / 7
- 不重排本文件既有的压缩式样式行（只做加法，保持 diff 可核）

## Decisions

**D1 优先复用共享件，而不是就地补齐等价样式**
理由：`frontend-l4-data-surface` 明文要求指标行复用 `KpiCard`；且 `.kpi-card` 是 `KpiCard` 的私有 scoped 类，就地补一份等于复制第二套 KPI 外观，与"单一真相源"冲突。
备选：在本文件定义 `.kpi-card/.kpi-dot/.kpi-value/.kpi-label` —— 否决。

**D2 通过率改用共享 `RateBar`**
理由：同模块 `index.vue` 已是唯一正确范式，且 `RateBar` 自带 95 / 80 阈值标签配色，与现状 `.rate-ok/.rate-warn/.rate-bad` 的意图一致；自建进度条是重复造轮子。
备选：就地补 `.progress-bar/.p-pass/.p-fail` —— 否决。

**D3 任务信息条复用本文件已定义的类名**
把模板的 `.task-meta-bar` / `.task-meta-item` 改为已存在的 `.task-meta-card` / `.meta-item`，只改模板不改样式。
理由：样式已存在且与 `ReportDetail.vue` 同名同构；新增同名异义的第二套类名会留下歧义。
备选：按模板现有名新增样式 —— 否决。

**D4 用例/步骤卡片样式就地补齐**
理由：该呈现为报告模块私有，且 `TaskReport` 与 `CaseBreakdown` 的数据形状与 DOM 结构不同，抽共享组件需先统一两者，属独立变更。
备选：本次直接抽 `CaseCard` 共享组件 —— 否决（范围爆炸），已登记为变更 9 的输入。

**D5 未找到分支回到骨架并使用 `EmptyState`**
理由：`frontend-l2-page-region` 要求每个 L2 页根复用 `.doc-page` 骨架并提供 `.wb-shell` 主题作用域；现状该分支两者皆无。

## Risks / Trade-offs

- [补齐样式后本文件超过 500 行] → 现 356 行，预计新增约 40 行仍低于上限；若超出则按 `frontend/AGENTS.md` §1.6 先拆样式层到 `TaskReport.style.css`
- [通过率列宽 140px 内放不下 RateBar] → `RateBar` 自带 `min-width:60px` 与 flex 布局；tasks 含该列渲染确认
- [新增 import 未被使用或签名不符导致类型/构建失败] → tasks 含 typecheck 与 build 验证
- [补齐样式属"新增代码"，可能引入新硬编码] → tasks 含按 `doodle-craft` 自检清单对本文件逐项扫描，并要求 `lint:styles` 通过

## Migration Plan

1. 先替换共享件（KpiCard / RateBar / EmptyState），再补样式，最后修未找到分支骨架
2. 回滚策略：单文件改动，回滚即 `git revert`；无数据、接口与路由迁移

## Open Questions

（无）