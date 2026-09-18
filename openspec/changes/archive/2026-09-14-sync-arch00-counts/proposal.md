## Why

ARCH-00 的**计数类事实**停在 2026-08-21 口径，与代码实测系统性不符；上一变更（`2026-09-14-fix-arch00-device-runner-drift`）已删掉 test_runner 的行，但按用户裁定**未重测其余数字**，仅在附录 A 加了口径注。本次把这批数字一次对齐。

**实测基线**（`python tools/gen_arch_stats.py --json`，2026-09-14，证据落盘 `temps/arch_stats_summary.json`）：

```
表 33（8 组前缀）· 路径端点 116 · Tool 12（3 类）· 前端模块 8 · WS 生产点 0
```

**逐 App 差额**（文档 → 实测）：

| App | 表 | 端点 | 说明 |
|-----|----|------|------|
| `accounts` | 0 → 0 | 5 → 5 | 一致 |
| `ai_assistant` | 7 → 7 | 15 + DRF → **25** | 文档把 DRF 生成另计，实测把 `urls.py` 里的 path 全数计入 |
| `case_manager` | **5 → 4** | **31 → 1** | 表：§3.2 记 `cm_`×5、A.2 行只列 3 个名字（两处都与实测 4 不符）；端点：`urls.py` 是 `*router.urls` + `move/`，静态 path 条目只有 1 |
| `dashboard` | 0 → 0 | 4 → 4 | 一致 |
| `device_inspector` | 1 → 1 | **6 → 7** | — |
| `device_pool` | 2 → 2 | 10 → 10 | 一致 |
| `element_locator` | **8 → 10** | **29 → 31** | A.2 漏 `el_locator_projects` / `el_locator_directories` |
| `evaluator` | 4 → 4 | 14 → 14 | 一致 |
| `report_generator` | 2 → 2 | 6 → 6 | 一致 |
| `workflow` | **2 → 3** | **10 → 13** | A.2 漏 `wf_prototypes` |
| **合计** | **35 → 33** | **143 → 116** | 前缀组 **9 → 8** |

**Tool 计数整体失效**（不只是数字）：文档 §4.5 与 A.3 把工具真相源写成 `ai_assistant/agent_scope/tool_registry.py`（**该目录/文件在仓库中已不存在**），清单为「26 个 / 7 组」。实测真相源是 `apps/ai_assistant/tools.py`：

- `TOOLS: dict[str, tuple]`（`:374-391`）**12 个**工具；
- `TOOL_META`（`:407-420`）给出 `(分类, module, action)` 三元组，分类只有 **3 类**（设备管理 / 设备检查器 / 工作流）；
- `TOOL_CATEGORIES`（`:398-402`）与 `AUTO_ALLOW_TOOLS`（`:365-372`，6 个免 HITL）与之配套；
- 装配链：`engines/ai/agentscope/tool_wrapper.py`（`PlatformFunctionTool` / `build_toolkit`）← `engines/ai/agentscope/model.py:300`。

**口径澄清（本次必须写进文档，否则新数字会被误读）**：`gen_arch_stats.py:68-75` 的端点口径是「**`urls.py` 中 `path(`/`re_path(` 静态入口条目数**」，DRF `router.urls` 展开的端点**不计**；表口径是 `models*.py` 中 `db_table = "..."` 的字面声明数（`gen_arch_stats.py:59-66`）。

## What Changes

只改 `dev_docs/03-设计与架构/ARCH-00-平台总体架构.md`：

1. **总量行**：§一「权威统计基准」（`:28`）与 §1.2 全景图存储节点（`:96`）→ 33 张表 / 8 组前缀 / 116 条路径端点 / 12 个 Tool（3 类）；删掉上一轮那句「表/端点/Tool 仍是 08-21 旧口径」的临时告示。
2. **§3.2 后端 App 速览**：11 行的「表 / 端点 / AI Tool」三列按实测回填（`device_pool` 9、`device_inspector` 1、`workflow` 2、`ai_assistant` 宿主 12，其余 —）；表头注改为说明端点口径与 router 化 App。
3. **附录 A 起始注**：改为「已按 2026-09-14 实测回填」+ 口径定义 + 与子 ARCH 逻辑端点口径的对照指引（保留「同源不同口径」的说法，不删）。
4. **A.1**：逐 App 表/端点数字与合计（33 / 116）；保留并改写子文档口径对照注。
5. **A.2**：标题改「33 张 · 8 组前缀」，表名按代码重列（`cm_` 4 个、`el_` 10 个、`wf_` 3 个全部补齐）。
6. **A.3**：标题改「12 个 · 3 类」，表格改为「分类（数量）| Tool 函数名 | `module.action` | 只读」四列，逐项列出 12 个（数据见 design.md D4）。
7. **§4.5**：工具单一真相源改为 `apps/ai_assistant/tools.py`（`TOOLS` + `TOOL_META`），数量 26 / 7 组 → 12 / 3 类；补一句装配链（`build_toolkit`）。
8. **§1.6**：#6 中「README 写「17 Tool」实为 26」→「实为 12」；#7（步骤类型计 45）**只核实状态**，若仍不一致保留登记不改数字。
9. **A.6**：`--check-md` 行的「表 35 / 路径端点 143 与 A.1 一致」→ 33 / 116。
10. **变更记录**：新增 v3.4 行。

## 关联文档

- 实测工具：`tools/gen_arch_stats.py`（`--json` / 默认输出 / `--check-md`）
- 计数真相源：`config/urls.py` · 各 App `urls.py` · 各 App `models*.py` · `apps/ai_assistant/tools.py`
- 前序变更：`openspec/changes/archive/2026-09-14-fix-arch00-device-runner-drift/`（本次收尾其登记的口径注）

**范围外登记（本次不动）**：

- **附录 A 改造成 `ARCH_STATS` 自动区域**（根治漂移）：工具能生成该区域，但生成的列（App|表|端点|代码行数|models|views|api|urls）与本文 §A.1 现有列（App|表|端点|层|Tool）不同，合并需先定表格契约 → 独立变更。
- `apps/ai_assistant/views/tool_gateway.py:7-8` 注释仍写「工具经 `agent_scope/tools.py`」——**代码注释**漂移（该路径不存在），属代码域另案。
- 子 ARCH 文档（ARCH-04/05/08/09）自身的端点数与其注口径。
- `dev_docs/03-设计与架构/技术栈参考.md` 的表前缀行（含已下线的 `tr_`）。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

（无；本次为纯文档计数回填，无需求级行为变化，`.openspec.yaml` 已声明 `skip_specs: true`）

## Impact

- **修改**：`dev_docs/03-设计与架构/ARCH-00-平台总体架构.md`（唯一文件）
- **不影响**：代码、运行时行为、API 契约、路由、DB、前端、`openspec/specs/`
- **测试范围**：`python tools/gen_arch_stats.py --json`（数字断言）· `--check-md`（漂移报告）· 文档内 `35` / `143` / `26 Tool` 残留 grep · `openspec validate sync-arch00-counts --strict`
