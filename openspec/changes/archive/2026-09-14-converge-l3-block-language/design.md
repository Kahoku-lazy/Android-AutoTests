## Context

动机见 `proposal.md` - Why。现状（已核对）：

- `frontend/AGENTS.md` 的 AppCard 判据是**单口径**：「把一组内容框成『块』就用它；单条数据的卡片（设备卡/任务卡）用模块私有组件」。
- 2026-09-14 裁决口径是**二分**：页面级分区用 `.doc-section`、可复用数据块用 AppCard。两者在「分区 / 分组卡」上直接冲突。
- 实测分布：`.doc-section` 9 文件 58 处（dashboard 19 · report 列表 18 · EvaluatorTab 10 · ai 首页 3 · TaskBoard 3 · AgentDetail 2 · AgentBasicInfo / AgentModelConfig / AgentRouteConfig 各 1）；`AppCard` 8 文件（report 列表 3 处嵌于 `.doc-section` 内 · report 详情 ×3 顶层表格卡 · KnowledgeBase 子视图内 3 处 · 登录三视图 3 处认证卡）。
- 结论：**不存在需要迁移的块**——所有 AppCard 位置按角色二分后都是「数据块 / 认证卡 / 条目卡」，所有 `.doc-section` 都是「页面级分区」。缺陷只在判据缺失与文档口径冲突。

约束：不改任何代码；不制造可见观感变化；只在必须触碰处改文档。

## Goals / Non-Goals

**Goals:**

- 登记可判定的二分判据（spec + AGENTS 双登记）
- 消除 `frontend/AGENTS.md` 与裁决口径冲突的那一句
- 留下逐页判定表作为判据落地的证据

**Non-Goals:**

- 不迁移任何现有块（判定表显示无迁移项）
- 不重构 `AppCard` 组件 API，不改 `.doc-section` 外观
- 不动 L4 内部（KPI 网格 / 图表 / 表格）与模块私有卡片

## Decisions

### 1. 判据按「角色」二分，而非按「组件归属」

- **选择**：页面级分区（页头之下承载整段内容、含自有标题或说明）→ `.doc-section`；可复用数据块（图表卡 / 表格卡 / 指标卡 / 认证卡 / 条目卡）→ `AppCard`
- **理由**：两套实现各有专长——骨架块提供 `__title` / `__label` / `.doc-tag` 与分区排版；AppCard 提供 `color` 顶条与 `.wb-shell` 皮肤。按角色分才能各用其所
- **备选**：只留 AppCard（58 处 `.doc-section` 迁移）或只留 `.doc-section`（8 文件 AppCard 迁移）—— 均造成大面积可见变化与返工，否决

### 2. 本次零代码迁移

- **选择**：只登记判据与修正文档，不改任何 `.vue` / `.css`
- **理由**：逐页判定表显示现有实现已合规；为「写法整齐」而迁移属过度设计（违反「只碰必须碰的」）
- **备选**：把 report 详情顶层 `.ac-card` 包进 `.doc-section` —— 会新增一层无信息量的分区外壳，否决

### 3. 认证卡 / 条目卡仍归 `AppCard`

- **选择**：登录三视图的认证卡、report 详情的表格卡、`CaseBreakdown` 的条目卡保持 `AppCard`
- **理由**：AGENTS 已把「认证卡」列入 AppCard 场景；条目卡属单条数据卡，迁移无收益

### 4. 主题作用域是 `AppCard` 的显式前提

- **选择**：把「外观只在 `.wb-shell` / `.workflow-workbench` 内生效」写进 spec 与 AGENTS
- **理由**：这是既有事实（`AppCard.vue` 只转发 `el-card` + `.ac-card` 类，皮肤在 `workbench-theme.css` 内），不写成前提会被误用到无锚点页面（登录页是已登记的独立视觉）

### 5. 只改 AGENTS 的一句话判据

- **选择**：替换冲突那一句 + 补主题作用域前提，不重写 shared 清单其它条目
- **理由**：最小 diff；表格列宽、Tabs 白传等条目与本判据无关

## 判定表（现有实现 × 判据，文件级全覆盖）

### A. `.doc-section` 消费文件（9 个 / 58 处）

| # | 文件 | 处数 | 角色判定 | 合规 |
|---|------|:--:|---------|:--:|
| 1 | `dashboard/index.vue` | 19 | 页面级分区 | ✅ |
| 2 | `report-generator/index.vue` | 18 | 页面级分区 | ✅ |
| 3 | `ai-assistant/EvaluatorTab.vue` | 10 | 页面级分区 | ✅ |
| 4 | `ai-assistant/index.vue` | 3 | 页面级分区 | ✅ |
| 5 | `ai-assistant/components/TaskBoard.vue` | 3 | 页面级分区（子视图内） | ✅ |
| 6 | `ai-assistant/AgentDetail.vue` | 2 | 页面级分区 | ✅ |
| 7 | `ai-assistant/components/AgentBasicInfo.vue` | 1 | 子分区（内嵌） | ✅ |
| 8 | `ai-assistant/components/AgentModelConfig.vue` | 1 | 子分区（内嵌） | ✅ |
| 9 | `ai-assistant/components/AgentRouteConfig.vue` | 1 | 子分区（内嵌） | ✅ |
| | **合计** | **58** | | |

### B. `AppCard` 消费文件（8 个 / 14 处）

| # | 文件 | 处数 | 位置形态 | 角色判定 | 合规 |
|---|------|:--:|---------|---------|:--:|
| 1 | `report-generator/index.vue` | 3 | `.chart-card` ×2 + `.table-card` ×1，**嵌在 `.doc-section` 内** | 数据块 | ✅ |
| 2 | `report-generator/TaskReport.vue` | 1 | `.table-card`，`.doc-body` 顶层 | 数据块（表格卡） | ✅ |
| 3 | `report-generator/ReportDetail.vue` | 1 | `.table-card`，`.doc-body` 顶层 | 数据块（表格卡） | ✅ |
| 4 | `report-generator/CaseBreakdown.vue` | 3 | 按用例分组的 `color` 条目卡，`.doc-body` 内 | 条目卡 | ✅ |
| 5 | `ai-assistant/KnowledgeBase.vue` | 3 | 子视图 `.kb-view` 内（状态卡 / 引用范围 / 表格卡） | 子视图内数据块 | ✅ |
| 6 | `views/components/LoginCard.vue` | 1 | 页面主卡 | 认证卡 | ✅ |
| 7 | `views/components/RegisterCard.vue` | 1 | 页面主卡 | 认证卡 | ✅ |
| 8 | `views/components/AccountSwitchPrompt.vue` | 1 | 弹窗主卡 | 认证卡 | ✅ |
| | **合计** | **14** | | |

### C. 顶层块分布（按页面）

| 页面 | 顶层块 | 角色判定 | 合规 |
|------|--------|---------|:--:|
| `/dashboard` | `.doc-section` ×6 | 页面级分区 | ✅ |
| `/reports` | `.doc-section` ×3 + 内嵌 `.ac-card` ×3 | 分区 ⊃ 数据块 | ✅ |
| `/reports/{runId}` · `/reports/task/{id}` | `.ac-card` ×1（表格卡） | 数据块（页面主体无分区） | ✅ |
| `/reports/cases/{type}` | `.ac-card` ×3（条目卡，无 `.doc-section`） | 条目卡 | ✅ |
| `/ai-assistant/agents` · `/evaluator` · `AgentDetail` | `.doc-section` | 页面级分区 | ✅ |
| `/ai-assistant/knowledge`（子视图） | `.ac-card` ×3 | 子视图内数据块 | ✅ |
| `/login` · `/register` · 切账号 | `.ac-card` ×1 | 认证卡 | ✅ |

**结论：9 个 `.doc-section` 消费文件 + 8 个 `AppCard` 消费文件（14 处）全部合规，无迁移项**；缺陷只在判据缺失与 `frontend/AGENTS.md` 的口径冲突。

> 补记（apply 阶段核验修正）：「以分区组织内容」不是全站要求 —— `/inspector` 主体为模块私有 `.inspector-section` + 分栏 `.workspace`（`device-inspector/index.vue:59,119`，`doc-section` 命中 0），已在 spec 中显式排除，不判违规。

## 模块防火墙自检

- 跨 App import：不涉及（仅文档与 spec）
- 禁止跨 App import service/runner/consumer/state_machine：不涉及
- 所有 INSERT/UPDATE/DELETE 收敛到 api.py：不涉及（无写操作）
- 前端不直连数据库；仪表盘不做写操作：不涉及

## Risks / Trade-offs

- [判据靠人读文档，无强制力] → spec 提供 4 条可核验 Scenario + AGENTS 双登记；`vue-frontend-check` 复核
- [与「块优先 AppCard」的旧心智冲突] → AGENTS 显式写「顶层分区除外」，并保留反例说明
- [判定表会过期] → 判定表同时落在本变更 design 与 `报告-前端区域层级与L3现状复盘.html` §四，新增页面按判据执行

## Migration Plan

1. 产出逐页判定表（见上）
2. 修正 `frontend/AGENTS.md` 的 AppCard 判据一句 + 补主题作用域前提
3. spec 已在本变更登记
4. 静态核验：按 4 条 Scenario 逐条检查；`npm run typecheck` + 构建作为零改动基线确认
5. 回滚：仅文档改动，`git checkout` 即可
