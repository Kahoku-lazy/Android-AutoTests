## 1. 取证基线

- [x] 1.1 运行 `python tools/gen_arch_stats.py --json`（经 `temps/dump_arch_stats.py`）落盘 `temps/arch_stats_summary.json`，记录 `summary` 四项（33/116/12/8）、11 个 App 的表/端点、12 个 Tool、8 个前端模块

## 2. 总量与概览行

- [x] 2.1 §一「你能从文档获取什么信息」的权威统计基准行：33 张表（8 组前缀）/ 116 条路径端点 / 12 个 Tool（3 类）/ 8 个前端模块 / 0 个 WS 生产点；删除上一轮那句「表 / 端点 / Tool 仍是 08-21 口径」临时告示
- [x] 2.2 §1.2 全景图存储节点：`33 张业务表 · 8 组前缀`

## 3. §3.2 后端 App 速览

- [x] 3.1 表头注改写：端点口径 = `urls.py` 静态 path 条目（router 展开不计）+ case_manager/workflow/ai_assistant 三例说明 + ai_assistant 迁移中提示
- [x] 3.2 表格「表」「端点」两列逐行回填（ai_assistant 25 · case_manager 4/1 · device_inspector 7 · element_locator 10/31 · workflow 3/13，其余按实测）
- [x] 3.3 表格「AI Tool」列按 `module` 归属回填：device_pool 9 · device_inspector 1 · workflow 2 · ai_assistant 宿主 12 · 其余 —
- [x] 3.4 标题与结尾口径与 §A.1 一致（活跃 10 个 + test_runner 已下线）

## 4. 附录 A 起始注 + A.1

- [x] 4.1 附录 A 起始注改写：声明「已按 2026-09-14 实测回填」+ 写出表/端点/Tool 三项口径定义 + 指向 `gen_arch_stats.py` 行号
- [x] 4.2 A.1 表格数字逐行回填；合计行改 **33** / **116**（+「DRF 生成路由另计」保留）
- [x] 4.3 A.1 下方「子文档端点口径（同源不同口径）」注改写：保留 ARCH-01/04/05/08/09 对照示例，补 case_manager（router 化 → 机器口径 1）说明

## 5. 附录 A.2

- [x] 5.1 标题改「A.2 数据库表清单（33 张 · 8 组前缀）」
- [x] 5.2 表名补齐并逐名核对：`cm_` 4 个（补 `cm_case_files` 并删多余）、`el_` 10 个（补 `el_locator_projects` / `el_locator_directories`）、`wf_` 3 个（补 `wf_prototypes`）；其余前缀保持

## 6. 附录 A.3 + §4.5

- [x] 6.1 A.3 标题改「12 个 · 3 类」，表格改四列（分类（数量）| Tool | `module.action` | 只读），逐项列出 design.md D4 的 12 行
- [x] 6.2 A.3 下补一句 `AUTO_ALLOW_TOOLS`（6 个免 HITL）
- [x] 6.3 §4.5：工具单一真相源由 `ai_assistant/agent_scope/tool_registry.py` 改为 `apps/ai_assistant/tools.py`（`TOOLS` + `TOOL_META` + `TOOL_CATEGORIES`）；数量 26 / 7 组 → 12 / 3 类；补装配链 `engines.ai.agentscope.tool_wrapper.build_toolkit` ← `model.py:300`

## 7. 登记项与变更记录

- [x] 7.1 §1.6 #6：「README 写「17 Tool」实为 26」→「实为 12」
- [x] 7.2 §1.6 #7：核实 `gen_arch_stats.py` 步骤类型计数与 `StepType`(37) / `STEP_TYPE_META`(29) 是否仍不一致；按核实结果更新该条状态描述（不一致则保留登记）
- [x] 7.3 A.6 `--check-md` 行：「表 35 / 路径端点 143 与 A.1 一致」→「表 33 / 路径端点 116 与 A.1 一致」
- [x] 7.4 变更记录新增 v3.4 行（口径：计数同步 + 端点/Tool 口径澄清）

## 8. 验证

- [x] 8.1 总量一致性：`temps/verify_arch00_counts.py`（重跑 `--json` 现取）→ **problems 0**；文档 §A.1 逐行求和 = 表 33 / 端点 116 = 实测 `table_count`/`endpoint_count`；§A.2 标题 33 张 · 8 组前缀；§A.3 标题 12 个 · 3 类；§一 总量行含「33 张表（8 组前缀）」「116 条路径端点」「12 个 Tool（3 类）」
- [x] 8.2 逐 App 一致性：A.1 与 §3.2 的表/端点两列与 `--json` 的 `django_apps` 逐项相等（脚本逐 App 断言，0 差异；`accounts`/`dashboard` 表 0、端点 5/4 一致；`workflow` 3/13、`element_locator` 10/31、`case_manager` 4/1、`ai_assistant` 7/25、`device_inspector` 1/7、`device_pool` 2/10、`evaluator` 4/14、`report_generator` 2/6）
- [x] 8.3 残留 grep：`26 Tool` / `agent_scope` / `tool_registry` 已清零（除 v3.0/v3.4 变更记录历史行）；本轮连带修正 §1.3/§3.1 图中的「26 Tool」、§二 L3 行的 `ai_assistant.agent_scope`、§3.1 的 `ai_ + agent_scope/` 与 `tool_registry` 连边、§A.5 三处 `tool_registry` 标注 → 统一为 `apps/ai_assistant/tools.py`（`tools.py 工具层`）
- [x] 8.4 A.2 表名清单与代码 `db_table` 声明集合完全相等：脚本比对 **33 个名字集合一致**（含本轮补入的 `cm_case_files` / `el_locator_projects` / `el_locator_directories` / `wf_prototypes`，无文档独有项）
- [x] 8.5 `python tools/gen_arch_stats.py --check-md` → 退出码 0，输出「💡 ARCH-00-平台总体架构.md 需要初始化 ARCH_STATS 区域」；已据此更正 §A.6 该行的能力描述（原写「表/端点与 A.1 一致」，实测无自动区域、无法机器比对）
- [x] 8.6 `openspec validate sync-arch00-counts --strict` → **Change is valid**
- [x] 8.7 附加：§1.6 #7 复核完成——工具仍计 **45** 种步骤类型，而 `models/step_types.py` 实测 `StepType` **37** 成员 / `STEP_TYPE_META` **29** 条 / `UI_LABELS` **28** 条，故**保留登记**并把证据写进该行（未改工具）
