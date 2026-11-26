# Proposal: fix-module-doc-drift

## Why

模块文档外置（`align-backend-docs-with-code` 的 5、6 两组）严格按「**只迁移、不改语义**」执行，
因此源 AGENTS.md 里那些**与代码不符**的说法被原样搬进了 `.agents/docs/**`。

这些文档现在是模块级约束的载体（各索引都写着「文档里的红线/契约/依赖方向效力等同模块级约束」），
失真会直接误导后续实现——本轮结构改造本身就是被失真文档误导出来的产物。

本变更**只做内容更正**：一条一条对着代码改，不碰结构、不合并篇章、不重排。

## What Changes

17 处，分三组：

- **A 组（tests，7 处）**：`.agents/docs/tests/**` 的目录清单、脚本映射、测试设施现状。
- **B 组（engines，7 处）**：`.agents/docs/engines/**` 与 `engines/AGENTS.md` 的目录清单、已退役路径、笔误、归档路径。
- **C 组（既有旧路径，3 处）**：`engines/agents` 于 2026-11-17 退役后遗留的指路漂移，见下方 C 组表。

**判定标准**：一律以**代码 / 仓库实际**为真相源，改文不改码。
**证据来源**：2026-11-23 文档外置时的逐行比对（两个并行审计），**每条执行前必须独立复核一次**（任务里给了复核命令），
不复核不动笔——审计结论本身也可能是旧的。

**明确不做**：
- 不重排、不合并、不新增章节；
- 不碰任何红线条款的**语义**；B7 那条红线措辞变更单独标注「须先获批」，未获批则跳过；
- 不改代码、不改 `.gitignore`、不改 `openspec/specs/**`；

## 逐条清单

### A 组 · tests 文档

| # | 文件（节） | 原文说法 | 实测（证据） | 改法 |
|---|---|---|---|---|
| A1 | `tests_integration_and_api.md`（脚本与模块映射表） | 设备检查器 → `tests/device/api/test_inspector.py`、`case/inspector.yaml` | 两个文件都不存在；`tests/device/api/` 只有 `test_devices.py` | 核实设备检查器是否已退役：是则整行删除，否则补真实落位 |
| A2 | `tests_directory_conventions.md`（迁移状态表） | `engines/agents/{unit,e2e}` | 目录不存在；实际为 `tests/engines/{ae_harness,backend_bridge,device}/unit`，无 e2e | 按实际目录重写这几行 |
| A3 | 同上 | `knowledge/{unit,integration}` | 实际为 `tests/knowledge_search/{unit,integration}` | 目录名更正 |
| A4 | 同上 | `models/{unit,integration}` | 只有 `tests/models/unit`，无 integration | 删掉 integration |
| A5 | `tests_unit_and_contract_parity.md`（「之所以放在 Python 侧」） | 「前端没有测试运行器（`frontend/src` 下无 spec/test 文件）」 | `frontend/package.json` 有 vitest 测试脚本，`frontend/tests/` 有 `.spec.ts` | 改为「前端有独立 runner，但 `frontend/src` 下无 spec；『路径能否被后端解析』只有后端能答」 |
| A6 | 同上（第 4 条举例） | `frontend/src/modules/ai-assistant/api/toolbox.ts` 的两处调用 | 该文件不存在；`api/` 下为 `agents.ts`、`assistants.ts` | 先找现行等价调用点，再换例子；找不到就删例子 |
| A7 | `tests_directory_conventions.md`（保留说明） | 「报告统一输出到 `reports/`」 | 根 `reports/` 不存在；实际产物在 `tests/reports/`（`tests_e2e.md` 亦如此写） | 统一为 `tests/reports/`，并同步 `tests/AGENTS.md` 索引的同一条规范 |

### B 组 · engines 文档

| # | 文件（节） | 原文说法 | 实测（证据） | 改法 |
|---|---|---|---|---|
| B1 | `engines/AGENTS.md`（职责） | 「`engines/agents/` 正在退役（见 `openspec/changes/retire-engines-agents`）」 | 目录已不存在；该变更已归档到 `openspec/changes/archive/2026-11-17-retire-engines-agents` | 改为「已于 2026-11-17 退役（archive 路径），目录不得重建」，与既有红线口径对齐 |
| B2 | `backend_bridge_role_assembly.md`（目录现状 + 红线 9） | 有 `events/` 目录，事件落库归它 | 无 `events/`；实际是 `event_log.py`、`workflow/cancel.py`；另有 `models/` 未列 | 按实际目录树重写清单 |
| B3 | `ae_harness_middleware_admission.md`（硬性边界 5） | 「配置只经 `agents/config.py`」 | 该文件不存在（随 platform-config-for-knowledge 删除） | 先定位现行配置载体，再改指向；没有则写明「无配置入口」 |
| B4 | `ae_harness_overview.md`（技术栈） | 「AgenScope」 | 应为 `AgentScope` | 更正笔误（不改版本号等其它内容） |
| B5 | `uart_log_serial_capture.md`（相关路径） | Agent 工具封装 `engines/agents/tools/tool_serial.py` | 该路径不存在（随 `engines/agents` 退役） | 删除该行，或指向现行工具封装（先核实有无） |
| B6 | `ae_harness_knowledge_kb_retrieval.md`（当前状态） | 评测能力见 `openspec/changes/add-knowledge-auto-eval` | 已归档为 `openspec/changes/archive/2026-11-18-add-knowledge-auto-eval` | 补 archive 路径 |
| B7 | `engines/AGENTS.md`（红线） | 「须先在**对应子 AGENTS** 立项」 | 子 AGENTS 已全部外置删除，指代失效 | 改为「对应模块文档（`.agents/docs/engines/**`）」——**属红线措辞，须先获需求方批准**；未批准则保留原文并在变更里登记 |

### C 组 · 既有旧路径（`engines/agents` 退役遗留，非本次外置造成，一并纳入）

| # | 位置 | 原文说法 | 实测（证据） | 改法 |
|---|---|---|---|---|
| C1 | `.agents/rules/engines-code-style.md` 第 6/17/85/110/122 行 | 指向 `engines/agents/AGENTS.md` | `engines/agents/` 已于 2026-11-17 退役，目录不存在 | 改为 `.agents/docs/engines/**` 对应篇，或删除该指路句 |
| C2 | `dev_docs/ARCH_PRD/ARCH-平台架构设计.md:168-170` | 表格三行 `engines/agents/`、`engines/agents/rag/`、`engines/agents/realtime_vocie/` | 目录已不存在 | 按现行引擎分层重写或标注退役 |
| C3 | `tests/arch/unit/test_channels.py:76` docstring | `engines/agents/rag/AGENTS.md` | 同上 | 改为 `.agents/docs/engines/ae_harness_knowledge/ae_harness_knowledge_kb_retrieval.md` 或删除引用 |

> 说明：这三处是 `retire-engines-agents`（2026-11-17）之后留下的指路漂移，与本次外置无关；
> 因为同属「文档指向不存在的 AGENTS」，放进同一个逐条复核的变更里收口，比另开一单更省。

## Capabilities

### New Capabilities

（无 —— 纯文档更正，不改变任何能力行为）

### Modified Capabilities

（无）

## Impact

- **文档**：`.agents/docs/tests/`（4 篇中的 3 篇）、`.agents/docs/engines/`（12 篇中的 6 篇）、`engines/AGENTS.md`、以及 A7 涉及的 `tests/AGENTS.md` 索引一条规范。
- **代码**：无。
- **时序（需求方 2026-11-23 裁定）**：**`align-backend-docs-with-code` 合并后再跑**，硬门控见 `tasks.md` 0.1。两单改同一批文件，本单只改文本，前置合并后才执行。
- **回退**：还原文档提交即回旧文本。

## 关联文档

- 前置：`openspec/changes/align-backend-docs-with-code`（结构外置，5、6 两组）
- 审计来源：2026-11-23 文档外置时的两份逐行比对结论（tests 7 条、engines 7 条）
