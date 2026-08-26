# PRD-07 — 测试报告 (Report Generator)

> 关联模块：`apps/report_generator/` · 前端：`frontend/src/modules/report-generator/`
> 关联全局：[`需求大纲.md`](./需求大纲.md) §5.7（执行结果收口）
> 关联上游：[`PRD-06-执行引擎`](./PRD-06-执行引擎.md)（执行记录 / 任务卡片 / 迭代结果）
> 关联下游：[`PRD-01-仪表盘`](./PRD-01-仪表盘.md)（报告数统计）
> 版本：v7.2 · 状态：评审中 · 日期：2026-08-21

**修订记录**

| 版本 | 日期 | 变更摘要 |
|------|------|----------|
| v7.2 | 2026-08-21 | run 状态大小写收敛：§4.1 状态枚举、F-03-01 Tab 值改小写（completed/failed/stopped）；§4.3 补登记 STATUS_LABEL_MAP 双份定义（api.ts vs constants.ts） |
| v7.1 | 2026-08-19 | 补齐各 F「职责与边界」声明（筛选口径后端同源、KPI 只展示、图表不重算、列表只读、详情不落库、故障分析不接缺陷系统、任务视角无操作、文件服务范围） |
| v7.0 | 2026-08-19 | 按 PRD-03 设备检查器格式重构：移除设计目录/数据流/验收汇总/实施状态/已知问题旧章节，补齐十章 + 附录A；同步代码真相（6 端点 `/api/reports/*`、报告数据实时读 tr_ 表、4 Tab、图表 7/30/90、阈值 95/80）；登记 rg_ 两表零读写与死代码偏差 |
| v6.1 | 2026-07-27 | ErrorState 错误处理补全、RateBar 组件化、useExpandCollapse 接入、死代码清理 |
| v6.0 | 2026-07-25 | KPI 卡片拍立得化、useECharts 接入、字体统一、模块色收束 c-dashboard→c-report |

---

## 1. 功能定位

测试报告是平台的**执行结果收口**：用户在此查看历史执行记录、分析通过率趋势、定位失败原因、下载文件归档。页面由三个区域自上而下排列：统计概览 → 数据图表 → 测试报告列表；另含报告详情、用例故障分析、任务报告三个子页面。

**核心职责**：

- **执行记录列表**：全部执行记录 + 6 维筛选 + 状态 Tab 分组
- **统计概览**：KPI 摘要（执行次数 / 通过 / 失败 / 通过率）+ Bug 聚合子文本
- **趋势图表**：通过率趋势折线图 + 每日通过/失败柱状图（7/30/90 天窗口）
- **失败定位**：用例级失败聚合、问题去重统计、失败步骤与原因
- **报告详情**：单次 run 聚合报告（用例明细 / 失败分析 / 步骤截图）
- **文件归档**：CSV / LOG / MD 文件下载与在线预览

测试报告是**只读聚合模块**：报告数据**实时读取执行引擎的 `tr_` 表**（TestRunRecord / TaskCard / TestResult），本模块不产生写入路径；自有 `rg_` 两张表（文件记录 / 报告模板）当前零读写（见 §6 偏差登记）。

---

## 2. 功能详细规格

### 2.1 模块一：报告主页

**核心功能**

- **统计概览**：筛选栏 + 4 张 KPI 卡片
- **数据图表**：通过率趋势 + 每日通过/失败双图联动
- **报告列表**：状态 Tab 分组 + 通过率进度条

**F-01-01 筛选栏**

**功能实现逻辑**：用户设定筛选条件缩小执行记录范围，筛选同时作用于列表、KPI、图表与故障分析（同一过滤口径）。

**详细功能点**：

- **筛选控件（6 维）**：日期范围（start_date / end_date）→ Run ID（部分匹配）→ 任务名称 → 设备 serial → 创建人
- **图表范围**：7 / 30 / 90 天（默认 30）
- **执行统计摘要**：「共 N 次执行 · M 次迭代」；有筛选条件时显示「清空条件」

**职责与边界**：筛选口径由后端统一（列表 / KPI / 趋势 / 故障分析同源，§4.1），前端只透传 query 参数不本地重算。

**验收方式**：任一筛选条件改变后，列表 / KPI / 图表同步缩小；清空条件恢复全量。

**F-01-02 KPI 卡片（×4）**

**功能实现逻辑**：页面顶部 4 张拍立得卡片展示筛选后执行摘要。

| 卡片 | 颜色 | 数据来源 | 交互 |
|------|------|------|------|
| 总执行次数 | `--c-workflow` 天蓝 ◆ | `summary.total_runs` | — |
| 通过 | `--c-device` 薄荷绿 ▲ | `summary.total_pass` | 点击 → 用例通过明细 |
| 失败 | `--c-runner` 桃粉 ■ | `summary.total_fail` | 点击 → 用例故障分析（含 Bug 统计子文本） |
| 通过率 | `--c-dashboard` 柠黄 ● | `summary.pass_rate`% | 显示迭代次数子文本 |

**职责与边界**：仅聚合展示，无写操作入口（本模块只读，见附录A）；卡片点击为查看入口，非操作入口。

**验收方式**：KPI 数字与列表行聚合一致；失败卡点击跳转故障分析。

**F-02-01 通过率趋势折线图**

**功能实现逻辑**：单系列折线 + 渐变面积填充，展示窗口内每日通过率；dataZoom 支持缩放与拖拽。

**详细功能点**：数据为窗口内**零填充**逐日序列（无执行日按 0 计）；与柱状图经 `echarts.connect('report-trend')` 联动缩放。

**组件**：`PassRateTrendChart.vue`。

**职责与边界**：趋势数据由后端零填充聚合返回（§4.1），前端只渲染不重算；窗口切换经 `chart_range` 参数控制。

**验收方式**：窗口边界正确（7/30/90）；无数据日期显示 0；双图联动缩放。

**F-02-02 每日通过/失败柱状图**

**功能实现逻辑**：双系列分组柱状图（通过绿 / 失败红），dataZoom 支持缩放。

**组件**：`DailyPassFailChart.vue`。

**职责与边界**：与趋势折线图共用同一 `trend` 数据源，仅渲染口径不同（双系列），前端不自行聚合。

**验收方式**：每日通过/失败数与列表一致；缩放与折线图联动。

**F-03-01 测试报告列表**

**功能实现逻辑**：报告列表按状态 Tab 分组展示，每行含 Run ID / 设备 / 用例数 / 通过 / 失败 / 通过率 / 状态 / 创建时间；点击 Run ID 进入报告详情。

**详细功能点**：

- **状态 Tab（4 组）**：全部 / 已完成（completed）/ 失败（failed）/ 已停止（stopped）——状态取值来自执行引擎 `TestRunRecord.status`（已收敛小写）
- **通过率进度条**：双色（绿=通过占比 / 红=失败占比）+ 百分比；颜色阈值：≥95% 绿、80-95% 黄、<80% 红
- **空态**：EmptyState 提示

**职责与边界**：列表只读展示执行记录；「重新执行」不在本模块（跳转执行引擎，见附录A）。

**验收方式**：Tab 分组正确；通过率颜色阈值（95/80）生效；Run ID 跳转详情。

### 2.2 模块二：子页面

**F-04-01 报告详情（ReportDetail）**

**功能实现逻辑**：`/reports/:runId` 展示单次 run 的聚合报告：4 张 KPI（执行用例 / 通过 / 失败 / 通过率）+ 任务元数据条 + 用例明细 / 失败分析 Tab + 步骤截图。

**详细功能点**：

- **用例明细**：每用例 planned / actual / pass / fail / rate + 迭代明细（iteration / result / duration_ms / detail），失败用例排前
- **失败分析**：仅存在失败时显示
- **步骤截图**：`step_details[]`（含 caseId / caseTitle / 截图路径 / 步骤结果）
- **趋势**：`recent_runs`（最近 10 次）折线

**职责与边界**：数据实时读 tr_ 表聚合（§4.1），本模块不落库、不缓存副本。

**验收方式**：用例聚合数与迭代明细一致；失败用例排序在前；截图可查看。

**F-04-02 用例故障分析（CaseBreakdown）**

**功能实现逻辑**：`/reports/cases/:resultType` 按用例聚合通过 / 失败数据：顶部 3 张 KPI（独立问题数 / 问题出现次数 / 涉及用例），下方按用例展开的折叠面板（含任务 → 失败步骤明细）。

**详细功能点**：

- **数据来源**：`GET /reports/cases?result=pass|fail`（同筛选口径）
- **问题去重**：失败按「步骤类型 + 描述 + 结果」签名去重，聚合出现次数与涉及任务数
- **Bug 汇总**：`bug_summary`（含 cases 明细：issue_count / total_occurrences / issues[]）

**职责与边界**：失败问题仅做聚合展示与统计；问题修复与缺陷跟踪（对接缺陷管理系统）不在本模块范围。

**验收方式**：问题签名相同只计一个独立问题；出现次数与涉及任务数正确；result=pass/fail 切换正确。

**F-04-03 任务报告（TaskReport）**

**功能实现逻辑**：`/reports/task/:taskId` 从任务卡片视角展示：KPI（总迭代 / 通过 / 失败 / 通过率）+ 任务元数据（结论 / BUG 单 / 轮次）+ 用例明细 / 失败分析 / 执行历史 Tab。

**详细功能点**：

- **执行历史**：`linked_runs`（最近 10 次 run 摘要）
- **任务结论**：`conclusion` / `bug_ticket` / `failed_steps`
- ⚠️ 偏差：前端「性能统计卡片」依赖后端未提供的 `_perf` 字段，当前不渲染（已登记，见 §4.3）

**职责与边界**：任务视角只读；任务删除、重跑、取消排队归执行引擎（PRD-06），本模块不提供操作按钮。

**验收方式**：任务元数据完整；执行历史列出关联 run；结论与 BUG 单可见。

### 2.3 模块三：文件下载与预览

**F-05-01 文件下载 / 在线预览**

**功能实现逻辑**：执行产生的 CSV / LOG / MD 归档文件可下载（FileResponse）或在线预览（CSV 结构化解析为表格）。

**详细功能点**：

- **下载**：`GET /reports/{filename}`（MIME 按后缀：csv / md / log）；文件名经 `Path(filename).name` 防目录穿越
- **在线预览**：`GET /reports/{filename}/content` → CSV 解析为 `rows[] / headers[]`
- ⚠️ 偏差：端点已就绪但前端页面暂无入口按钮（已登记，见 §4.3）

**职责与边界**：仅下载/预览归档目录（LOG_DIR）内文件；报告文件生成与落盘归执行引擎（PRD-06），本模块只读文件。

**验收方式**：下载文件内容完整；预览 CSV 表格列与文件一致；路径穿越被拦截（404）。

---

## 3. 布局与视觉设计

> 全部颜色/字号引用 Doodle Craft 主题令牌（[`frontend/AGENTS.md` §2](../../frontend/AGENTS.md)）。模块色 `--c-report`。

### 3.1 主页布局

```
┌─────────────────────────────────────────────────┐
│ WorkbenchHeader（标题 + 副标题）                   │
├─────────────────────────────────────────────────┤
│ ① 统计概览：筛选栏（6 维）+ 执行统计摘要            │
│    KpiCard × 4（总执行/通过/失败/通过率）           │
│ ② 数据图表：趋势折线图 | 每日柱状图（联动缩放）       │
│ ③ 报告列表：状态 Tab（全部/已完成/失败/已停止）       │
│    AppTable（Run ID 下划线链接 + 通过率进度条）      │
└─────────────────────────────────────────────────┘
```

### 3.2 子页面布局

- **ReportDetail**（`/reports/:runId`）：KPI × 4 + 任务元数据条 + Tab（用例明细 / 失败分析）+ 步骤截图
- **CaseBreakdown**（`/reports/cases/:resultType`）：KPI × 3 + 用例折叠面板 + Bug 问题汇总 Tab
- **TaskReport**（`/reports/task/:taskId`）：KPI × 4 + 任务元数据 + Tab（用例明细 / 失败分析 / 执行历史）

### 3.3 组件规格

| 元素 | 规格 |
|------|------|
| KPI 卡片 | 拍立得风格（KpiCard）；失败卡附 Bug 统计子文本 |
| 通过率进度条 | 双色（绿/红）+ 百分比；≥95 绿 / 80-95 黄 / <80 红 |
| Run ID | 下划线链接样式，点击跳详情 |
| 图表 | ECharts，dataZoom + 渐变面积，双图联动缩放 |

### 3.4 边界状态（场景）

| 场景 | 行为 |
|------|------|
| 报告为空 | EmptyState 空态 |
| 无趋势数据 | 图表区不显示（仅在有趋势数据时显示） |
| 筛选无结果 | 列表空 + KPI 归零 |
| run 不存在 | 详情页 404 提示 |
| 下载文件不存在 | 404「not found」 |
| 请求失败 | ErrorState 错误态 + 重试 |
| result 参数非法（cases） | 400「result 必须为 pass 或 fail」 |

---

## 4. 后端功能逻辑

### 4.1 数据口径（实时聚合，无落库）

报告数据**不落 `rg_` 表**：列表 / 详情 / 故障分析全部实时读取执行引擎的 `tr_` 表（`TestRunRecord` + `TaskCard` + `TestResult`）。

- **列表行**：以 `TestRunRecord` 为主，按 `client_task_id` 关联 `TaskCard`（批量单查询，无 N+1）；有任务卡片时以卡片聚合计数为准，否则以 TestResult 计数兜底
- **KPI**：`summary` = 展示行聚合（total_runs / total_iterations / total_pass / total_fail / pass_rate）
- **趋势**：窗口零填充逐日序列，`chart_range` 仅接受 7/30/90，非法回落 30
- **故障分析**：优先读 `TaskCard.case_items`（执行时聚合），无卡片时回退 TestResult 逐行
- **状态枚举**：本模块不定义状态，`status` 直接透传执行引擎的 `TestRunRecord.status`（已收敛小写，`models/test_models.py` `TestRunStatus`）；前端映射文案（completed→通过 / failed→失败 / running→运行中 / stopped→已停止 / pending→排队中）

### 4.2 Bug 聚合口径

失败按「步骤类型 + 描述 + 结果」签名去重：`unique_issues`（独立问题数）/ `total_occurrences`（出现次数）/ `affected_cases`（涉及用例数）。列表端点仅返回 3 个汇总字段；`/reports/cases`（fail）返回含 `cases[]` 明细的完整结构。无步骤明细的迭代失败归为「iteration / 执行失败（无步骤明细）」占位签名。

### 4.3 已知偏差登记

| 偏差 | 说明 |
|------|------|
| `rg_` 两表零读写 | `rg_reports` / `rg_report_templates` 仅 Model + admin 注册，无端点、无视图读写；报告数据实时读 tr_ 表（登记为技术债，或补齐或下架） |
| 死代码 | `service.py` 的 `save_csv` / `generate_json_report` / `save_json_report` 与 `api.py` 的 `save_report` 无调用方（仅 `save_log` 被执行引擎消费） |
| 性能统计卡片不渲染 | `TaskReport.vue` 的 perf-stat 卡片依赖后端未返回的 `_perf` 字段，恒为空 |
| 下载/预览无前端入口 | 后端 2 个文件端点就绪，前端 api.ts 已封装但页面无入口按钮 |
| 信封平铺 | 列表/详情响应为 `{status, ...}` 平铺（非 `{status, data}`），字段名 snake_case（已登记） |
| 前端 `STATUS_LABEL_MAP` 双份定义 | `api.ts:40-46` 与 `constants.ts:69-75` 各维护一份相同的小写状态文案映射（completed/failed/running/stopped/pending），待收敛为单一真相源，禁止新增第三份 |

---

## 5. API 接口功能

鉴权：全部端点需 JWT Bearer。响应 `{status, ...}` 平铺 + snake_case；文件端点返回 FileResponse。状态码语义：400 参数非法 / 404 资源不存在。

### 5.1 端点总览（6 端点）

| # | 方法 | 端点 | 功能 | 前端消费 |
|---|------|------|------|:--:|
| 1 | GET | `/api/reports/` | 执行记录列表 + KPI + 趋势 + Bug 摘要（F-01/F-02/F-03） | ✅ |
| 2 | GET | `/api/reports/cases` | 用例通过/失败分层分组 + Bug 明细（F-04-02） | ✅ |
| 3 | GET | `/api/reports/run/{run_id}` | 单次 run 聚合报告（F-04-01） | ✅ |
| 4 | GET | `/api/reports/task/{task_id}` | 任务视角报告（F-04-03） | ✅ |
| 5 | GET | `/api/reports/{filename}/content` | 文件在线预览（CSV 结构化） | ❌（api 已封装无入口） |
| 6 | GET | `/api/reports/{filename}` | 文件下载（FileResponse） | ❌（api 已封装无入口） |

### 5.2 端点 1 — 报告列表

**接口地址**：`GET /api/reports/`

**请求参数**（query，均可选）：`start_date` / `end_date`（ISO 日期）/ `run_id` / `task_name` / `device_serial` / `creator`（部分匹配）/ `chart_range`（7\|30\|90，默认 30）。

**响应字段**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `status` | boolean | true |
| `summary` | object | `total_runs` / `total_iterations` / `total_pass` / `total_fail` / `pass_rate` |
| `bug_summary` | object | `unique_issues` / `total_occurrences` / `affected_cases`（不含 cases 明细） |
| `trend` | object | `range_days` / `dates[]` / `labels[]` / `pass[]` / `fail[]` / `rate[]`（零填充逐日） |
| `runs[]` | array | `run_id` / `status` / `device_serial` / `loop_count` / `case_count` / `total` / `passed` / `failed` / `rate` / `duration` / `started_at` / `finished_at` / `client_task_id` / `task_name` / `creator` / `outcome` |

### 5.3 端点 2 — 用例故障分析

**接口地址**：`GET /api/reports/cases`

**请求参数**：`result`（必填，pass\|fail）+ 端点 1 全部筛选参数。

**响应字段**：`status` / `result_type` / `total` / `case_count` / `groups[]`（`case_title` / `case_id` / `count` / `tasks[]`，fail 时 task 含 `failed_steps[]`）；`result=fail` 追加完整 `bug_summary`（含 `cases[]`：`issue_count` / `total_occurrences` / `issues[]` 带 `step_type` / `description` / `result` / `count` / `task_count` / `task_ids[]`）。

**错误**：400「result 必须为 pass 或 fail」。

### 5.4 端点 3 — 报告详情

**接口地址**：`GET /api/reports/run/{run_id}`

**响应字段**：`status` + `run{}`：`run_id` / `status` / `device_serial` / `loop_count` / `selected_cases` / `started_at` / `finished_at` / `duration` / `total_iterations` / `total_pass` / `total_fail` / `pass_rate` / `case_count` / `cases[]`（`case_id` / `case_title` / `planned` / `actual` / `pass` / `fail` / `rate` / `iterations[]`）/ `recent_runs[]` / `client_task_id` / `task_name` / `task_creator` / `task_outcome` / `task_conclusion` / `task_bug_ticket` / `task_failed_steps` / `task_round` / `step_details[]`。

**错误**：404「run not found」。

### 5.5 端点 4 — 任务报告

**接口地址**：`GET /api/reports/task/{task_id}`

**响应字段**：`status` + `task{}`：`task_id` / `name` / `creator` / `mode` / `device_serial` / `loop_count` / `interval_seconds` / `status` / `outcome` / `round` / `conclusion` / `bug_ticket` / `failed_steps` / `case_ids` / `case_items` / `overall_pass` / `overall_fail` / `pass_rate` / `created_at` / `updated_at` / `linked_runs[]`（最近 10 次）/ `step_details[]`。

**错误**：404「task not found」。

### 5.6 端点 5/6 — 文件下载与预览

**接口地址**：`GET /api/reports/{filename}` / `GET /api/reports/{filename}/content`

- 下载：MIME `text/csv` / `text/markdown` / `text/plain`；404「not found」
- 预览：`status` / `name` / `type`（csv\|md\|log）/ `size` / `content` / `rows[]` / `headers[]`（仅 CSV 解析）；404「not found」

### 5.7 契约变更

| 版本 | 变更 |
|------|------|
| v6.x | 数据驱动重构：报告从文件解析改为实时读 `tr_` 表（TestRunRecord/TaskCard/TestResult） |
| v6.x | 新增 `/cases`、`/run/{run_id}`、`/task/{task_id}`、`/{filename}/content` 端点；`chart_range` 支持 7/30/90 |
| v7.0 | 端点总览按代码真相校正为 6 端点；登记信封平铺与 rg_ 零读写偏差；无字段契约破坏 |

---

## 6. 数据来源表

| 表 | 表前缀 | 说明 |
|------|:--:|------|
| `rg_reports` | rg_ | 报告文件记录（**当前零读写**，仅 Model + admin） |
| `rg_report_templates` | rg_ | 报告模板配置（**当前零读写**，仅 Model + admin） |
| `tr_test_runs` | tr_ | **只读**：执行记录主数据（主权 PRD-06） |
| `tr_task_cards` | tr_ | **只读**：任务卡片聚合/元数据（主权 PRD-06） |
| `tr_test_results` | tr_ | **只读**：迭代结果与步骤截图明细（主权 PRD-06） |

---

## 7. 非功能需求

| 类别 | 指标 | 目标值 |
|------|------|------|
| 性能 | 列表查询 | 任务卡片批量单查询（无 N+1）；`/runs` 上限 50 条（执行引擎口径） |
| 性能 | 详情趋势 | `recent_runs` 最近 10 次 |
| 可靠性 | 文件下载 | 文件名 `Path(name)` 防目录穿越，不存在 404 |
| 兼容性 | 图表窗口 | 7 / 30 / 90 天，非法值回落 30 |
| 一致性 | 筛选口径 | 列表 / KPI / 趋势 / 故障分析共用同一过滤条件 |

---

## 8. 非目标（Non-goals）

| 不做的功能 | 原因 |
|------|------|
| PDF 导出 | 未实现（无任何后端/前端代码） |
| 报告模板管理 UI | `rg_report_templates` 仅 Model 壳，无端点无页面 |
| 执行测试 / 重新执行 | 由执行引擎（PRD-06）承担，本模块只读 |
| 用例定义管理 | 由用例管理（PRD-05）承担 |
| 报告推送通知（邮件/钉钉/企微） | 平台范围外（需求大纲 §1.3） |

---

## 9. 关键约束速查

| 编号 | 约束 | 实施位置 |
|------|------|------|
| C-01 | 只读聚合：报告数据实时读 tr_ 表，不落 rg_ 表 | `views.py` |
| C-02 | 筛选口径统一：列表/KPI/趋势/故障分析共用同一过滤 | `views.py` `_filter_run_queryset` |
| C-03 | 状态枚举不自有：透传执行引擎 `TestRunRecord.status` | `views.py` / 前端 `constants.ts` |
| C-04 | 响应 `{status, ...}` 平铺 + snake_case | 全部端点 |
| C-05 | 文件服务防目录穿越（`Path(filename).name`） | `views.py` download/view |
| C-06 | 颜色/字号引用 Doodle Craft 令牌 | `frontend/src/modules/report-generator/` |

---

## 10. 相关文件索引

| 层 | 文件 | 说明 |
|------|------|------|
| 前端 | `frontend/src/modules/report-generator/index.vue` | 报告主页编排（筛选 + KPI + 图表 + 列表） |
| 前端 | `frontend/src/modules/report-generator/ReportDetail.vue` | 单次 run 报告详情 |
| 前端 | `frontend/src/modules/report-generator/CaseBreakdown.vue` | 用例故障分析 |
| 前端 | `frontend/src/modules/report-generator/TaskReport.vue` | 任务视角报告 |
| 前端 | `frontend/src/modules/report-generator/components/DailyPassFailChart.vue` | 每日通过/失败柱状图 |
| 前端 | `frontend/src/modules/report-generator/components/PassRateTrendChart.vue` | 通过率趋势折线图 |
| 前端 | `frontend/src/modules/report-generator/api.ts` | 数据层（6 端点 + 工具函数） |
| 前端 | `frontend/src/modules/report-generator/constants.ts` / `routes.ts` | 常量 / 路由 `/reports` 等 4 条 |
| 后端 | `apps/report_generator/urls.py` | 6 端点路由 |
| 后端 | `apps/report_generator/views.py` | HTTP 入口（列表/分组/详情/任务/文件） |
| 后端 | `apps/report_generator/models.py` | rg_ 2 表定义（零读写） |
| 后端 | `apps/report_generator/service.py` | 报告文件服务（仅 save_log 被消费） |
| 后端 | `apps/report_generator/api.py` | 跨模块写白名单（save_report 无调用方） |
| 路由 | `config/urls.py` | `api/reports/` |

---

## 附录A：功能边界规则

| 边界 | 规则 |
|------|------|
| 我能做什么 | 执行记录列表与筛选、KPI 统计、趋势图表、用例故障分析、单次/任务报告详情、文件下载与预览 |
| 我不能做什么 | 执行测试（PRD-06）、管理用例（PRD-05）、管理设备（PRD-02）、任何写操作（本模块只读聚合） |
| 如需越界 | 「重新执行」跳转执行引擎（预填原任务配置）；数据全部经执行引擎 tr_ 表只读获取 |
| 数据可见性 | 执行记录与报告为平台共享，不按用户隔离；文件下载仅限 LOG_DIR 内归档文件 |
