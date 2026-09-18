## Context

动机见 `proposal.md` - Why。现状（逐一核对模块内全部 `.doc-page` 选择器，共 7 处）：

| # | 位置 | 选择器形态 | scope 后权重 | 声明是否生效 |
|---|------|-----------|:--:|------|
| 1 | `dashboard/DashboardView.style.css:6` | `.dashboard-workbench .doc-page` | 3 | 仅 `background-color` 生效（P0 已处理） |
| 2 | `device-inspector/index.vue:168` | `.doc-page` | 2 | `height` / `overflow` **死**；`background-color` 生效 |
| 3 | `report-generator/TaskReport.vue:336` | `.doc-page` | 2 | `height` / `overflow-y` **死** |
| 4 | `report-generator/ReportDetail.vue:438` | `.doc-page` | 2 | 同上 |
| 5 | `report-generator/CaseBreakdown.vue:413` | `.doc-page` | 2 | 同上 |
| 6 | `report-generator/index.vue:369` | `.doc-page` | 2 | `height` **死**；`overflow:hidden!important` **生效** |
| 7 | `ai-assistant/TaskDetailPage.vue:225` | `.task-detail-page.doc-page` + 两个 `!important` | 3 + important | **全部生效**（不属死声明） |

胜出规则（`App.vue`）：`.main-content__body[data-v] .doc-page { flex:1; min-height:0; height:auto; overflow:visible }` —— 权重 3。

约束：只删「静态可证被覆盖」的声明；带 `!important` 或复合选择器提升权重者一律不动。

## Goals / Non-Goals

**Goals:**

- 清掉 5 处失效的 `height` / `overflow` 声明，消除「读完 CSS 会误判滚动归属」的误导
- 修正 `frontend/AGENTS.md` L2 §⑥ 的清单（含纠正 ai-assistant / device-pool 的误列）

**Non-Goals:**

- 不动 `TaskDetailPage.vue` 的 `.task-detail-page.doc-page { … !important }`（实际生效，删了会改变钉底栏布局）
- 不动 `report-generator/index.vue` 的 `overflow:hidden!important`（实际生效）
- 不动任何 `.doc-section*` / `.doc-body` 覆写
- 不做 P2（`animations.ts` 死导出）、P3（死令牌）

## Decisions

### 1. 判据：只删「被更高权重规则覆盖且无 `!important`」的声明

- **选择**：逐处比对选择器权重与 `!important`，只有静态可证被覆盖的才删
- **理由**：`!important` 不受权重影响；复合选择器（`.a.b`）会把权重抬到 3 而打平 `:deep`，平手时由 CSS 加载顺序决胜（模块 chunk 后加载 → 模块胜），此时声明**实际生效**
- **备选**：按 L2 报告原清单一次性清 6 处 —— 会删掉 TaskDetailPage 正在生效的钉底栏布局，否决

### 2. `device-inspector` 只删 2 个属性，保留 `background-color`

- **选择**：保留 `display` / `flex-direction` / `background-color: var(--paper)`
- **理由**：`background-color` 权重 2 > 全局，**实际生效**并遮蔽主区涂鸦；删除属可见变化，不在本变更范围

### 3. `report-generator/index.vue` 只删 `height:100%`

- **选择**：保留 `overflow:hidden!important`
- **理由**：`!important` 使其实际生效（该页为策略② 工作台，需要页面根裁切）

### 4. 验证口径：以静态证明代替浏览器核验

- **选择**：验证方式 = 「权重比较 + `!important` 排查」的静态证明；**不做**浏览器目视
- **理由**：本变更只删除**被覆盖**的声明，被删语句从未参与级联 → 对渲染结果的影响为**恒等**；这比「目视无异常」更强（后者只能证明观察不到差异）
- **限制（如实声明）**：该结论依赖 `App.vue` 的 `:deep(.doc-page)` 规则不被改动；若后续有人改它，这 5 处的滚动归属会重新变得不确定 —— 已在 `frontend/AGENTS.md` L2 §⑥ 保留该约束说明

## 模块防火墙自检

- 跨 App import：不涉及（纯前端样式声明清理）
- 禁止跨 App import service/runner/consumer/state_machine：不涉及
- 所有 INSERT/UPDATE/DELETE 收敛到 api.py：不涉及（无写操作）
- 前端不直连数据库；仪表盘不做写操作：不涉及

## Risks / Trade-offs

- [误删生效声明] → 已逐处核对选择器形态与 `!important`；TaskDetailPage 与 report index 的生效声明明确保留
- [后续改动 `:deep(.doc-page)` 使滚动归属再不确定] → L2 §⑥ 保留说明，指明由外壳承担 `height/overflow`
- [清单仍有其它误列] → 本变更顺带修正 AGENTS 中 ai-assistant / device-pool 的误列

## Migration Plan

1. 复核 7 处 `.doc-page` 选择器的权重与 `!important`
2. 删除 5 处失效声明（共 9 条：`height` ×5、`overflow` ×4）
3. 同步 `frontend/AGENTS.md` L2 §⑥
4. `npm run typecheck` + `npx vite build --mode development` + `vue-frontend-check`
5. 回滚：`git checkout` 5 个 `.vue` + 文档，无数据迁移
