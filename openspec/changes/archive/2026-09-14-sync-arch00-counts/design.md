## Context

- 变更性质：**纯文档计数回填**（单文件），无代码改动 → `.openspec.yaml` 声明 `skip_specs: true`。
- 实测基线（2026-09-14，`python tools/gen_arch_stats.py --json`，摘要落盘 `temps/arch_stats_summary.json`）：

  | 指标 | 文档现值 | 实测值 |
  |------|---------|--------|
  | 表总数 | 35 | **33** |
  | 表前缀组 | 9 | **8**（`ai_ cm_ di_ dp_ el_ ev_ rg_ wf_`） |
  | 路径端点 | 143 | **116** |
  | AgentScope Tool | 26（7 组） | **12**（3 类） |
  | 前端模块 | 8（上轮已修正） | 8 ✓ |
  | WS 生产点 | 0（上轮已修正） | 0 ✓ |

- **口径定义**（读自 `tools/gen_arch_stats.py`，须写进文档）：
  - 端点 = `apps/<app>/urls.py` 中 `^\s*(path|re_path)\(` 的**静态入口条目数**（`:68-75`）——DRF `DefaultRouter` 展开的 ViewSet 路由**不计**；空串根路径计。
  - 表 = `apps/<app>/models*.py` 中 `db_table = "..."` 的**字面声明数**（`:59-66`，含 `models_*.py` 分表）。
  - Tool = `apps/ai_assistant/tools.py` 中 `TOOLS` 字典的条目数（用 AST 扫描，`scan_tools()` `:94-127`）。
- 口径影响实例（解释「文档 31 → 实测 1」这类看似剧烈的差异）：
  - `case_manager/urls.py` = `*DefaultRouter.urls`（4 个 ViewSet 注册）+ `path("move/")` → 静态条目 **1**；
  - `workflow/urls.py` = `DefaultRouter`（3 注册）+ legacy 平铺 path → 静态条目 **13**；
  - `ai_assistant/urls.py` = `DefaultRouter(trailing_slash=False)`（3 注册）+ 一批显式 `path()` APIView（Batch 1-3 迁移新增）→ 静态条目 **25**。
- Tool 真相源已迁移：`apps/ai_assistant/agent_scope/` **目录不存在**；ARCH-00 §4.5 与 A.3 指向的 `agent_scope/tool_registry.py` 是已消失的旧注册表。

## Goals / Non-Goals

**Goals:**

- 让 ARCH-00 的计数类事实与 `gen_arch_stats.py` 实测**逐项相等**，并把口径写清楚，使读者不会把「机器口径」误读成「平台端点缩水」。

**Non-Goals:**

- 不把附录 A 改造成 `ARCH_STATS` 自动区域（见 D1）。
- 不改任何代码、`openspec/specs/`、子 ARCH 文档、`技术栈参考.md`。
- 不修 `views/tool_gateway.py` 注释里的 `agent_scope/tools.py` 悬空路径（代码域另案）。
- 不动前端模块数 / WS 生产点（上轮已修正，本次只保证总量行不与之矛盾）。

## Decisions

**D1 人工回填，不初始化 `ARCH_STATS` 自动区域。**
工具能生成 `<!-- ARCH_STATS -->` 区域（默认输出里可见），但它的表格列是 `App|表|端点|代码行数|models|views|api|urls`，而本文 §A.1 的列是 `App|表|端点|层|Tool`——直接嵌入会丢掉「层」与「Tool」两列（本文作为架构总纲需要的语义）。合并两种列需先定表格契约，且会改变 `--check-md` 的语义，属独立决策 → 登记为范围外，本次先用人工回填保证**正确性**。
备选：把 §A.1 降级为工具生成表 + 手工补列 → 结构改动大，收益（自动防漂移）需单独评估。

**D2 端点采用「机器口径为主 + 双口径对照」呈现。**
附录 A.1 的数字用机器口径（116），并在同一处保留/改写「子文档端点口径对照注」，并把 router 化 App 的单列说明写进 §3.2 表头注。这样既与工具一致（可自动核对），又不抹掉「逻辑端点更多」的事实。

**D3 表清单按代码 `db_table` 重列，修掉 A.2 的自相矛盾。**
现状 §3.2 记 `cm_`×5 而 A.2 行只列 3 个名字（两处与实测 4 均不符）；`el_` 漏 2 个；`wf_` 漏 1 个。改为 33 张逐名列出：
`ai_`7 · `cm_`4（`cm_case_projects`/`cm_case_directories`/`cm_case_files`/`cm_test_definitions`）· `di_`1 · `dp_`2 · `el_`10（+ `el_locator_projects`/`el_locator_directories`）· `ev_`4 · `rg_`2 · `wf_`3（+ `wf_prototypes`）。

**D4 Tool 口径切换为 `apps/ai_assistant/tools.py`，并逐项列出 12 个。**
A.3 表格列改为「分类（数量）| Tool 函数名 | `module.action` | 只读」，数据（来自 `TOOLS` + `TOOL_META` + `scan_tools()`）：

| 分类 | Tool | `module.action` | 只读 |
|------|------|------------------|:--:|
| 设备管理（9） | `get_online_devices` | `devices.list_online` | ✅ |
| | `list_devices` | `devices.list_all` | ✅ |
| | `acquire_device` | `devices.acquire` | ❌ |
| | `release_device` | `devices.release` | ❌ |
| | `list_apps` | `devices.list_apps` | ✅ |
| | `device_action` | `devices.action` | ❌ |
| | `click_ratio` | `devices.click_ratio` | ❌ |
| | `drag_ratio` | `devices.drag_ratio` | ❌ |
| | `xpath_action` | `devices.xpath_action` | ❌ |
| 设备检查器（1） | `screenshot_page` | `inspector.screenshot` | ✅ |
| 工作流（2） | `list_page_flows` | `workflow.list_page_flows` | ✅ |
| | `get_page_flow` | `workflow.get_page_flow` | ✅ |

补充登记：`AUTO_ALLOW_TOOLS`（`:365-372`）含 6 个免 HITL 工具（`acquire_device`/`release_device`/`device_action`/`click_ratio`/`drag_ratio`/`xpath_action`）。

**D5 §3.2 的「AI Tool」列按 `TOOL_META` 的 module 归属回填。**
`devices.*` → `device_pool` **9**；`inspector.*` → `device_inspector` **1**；`workflow.*` → `workflow` **2**；`ai_assistant` 记「宿主 **12**」；其余 App 记 `—`。这比现状（4/2/7/6/—/26/2）既改数字也改归属口径，需在表头注说明「按工具 `module` 归属，而非函数所在文件」。

**D6 §1.6 #7（步骤类型 45 vs 37）只核实、不改数。**
该条是既有的工具口径遗留登记；本次只运行工具比对 `StepType`(37)/`STEP_TYPE_META`(29) 后更新其状态描述，若仍不一致**保留登记**，不顺手改工具或枚举（AGENTS.md：只碰必须碰的）。

## Risks / Trade-offs

- [「端点 143 → 116」被读成平台能力缩水] → D2 的双口径对照 + router 化 App 逐例说明（case_manager 1、workflow 13、ai_assistant 25）。
- [人工回填的数字下次再漂移] → D1 已登记根治方案（ARCH_STATS 自动区域）为独立候选；本次至少在 §A.6 保留 `--check-md` 的核对结论。
- [§3.2 Tool 列改归属会与 §A.1 的「Tool」列产生两套说法] → 两处统一为同一口径（按 `module` 归属、宿主 12），并在 A.3 里给出完整清单作为唯一明细。
- [ai_assistant 的 25 会随 DRF 迁移继续变] → 表头注保留「迁移进行中，数字会变」的提示（原文已有）。
