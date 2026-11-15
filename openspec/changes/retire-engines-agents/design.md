# retire-engines-agents 设计

## Context

动机见 `proposal.md - Why`。当前状态与方案直接相关的约束：

- `engines/backend_bridge` 已承接平台单角色会话（`platform_ui`）、模型计费副本、SOP 装配（`workflow/sop_ui.py`）与报告路径，只依赖 `ae_harness` 的 `agents/tools/event/middleware/workflow.sop` 五个子包。
- `engines/agents` 仍被 5 个后端 app 的 22 处 import 与 `engines/device/android/recent_apps.py` 1 处反向依赖绑住。
- 两套提示词已经分叉：执行者（`ae_harness` 9945 B vs `agents` 6042 B）、验收者（`agents` 4793 B vs `ae_harness` 3835 B）；`CASE_*` 两份完全一致。
- `ae_harness/knowledge/` 与 `agents/rag/` 各自声明 `SQLiteVectorStore`，各自索引（`engines/ae_harness/knowledge/index/` 与 `data/rag_index/`）。
- `openspec/changes/ae-harness-knowledge-tool` 仍在进行中（15/19，剩余为效果评测），本变更保留其产出物 `ae_harness/knowledge/`，不改其评测任务。

## 变更申请（按根 AGENTS.md 行为规范 4）

| 要素 | 内容 |
| --- | --- |
| **改什么** | ① `engines/AGENTS.md` 一级子包删 `agents/`，依赖边界改为 `backend → backend_bridge → ae_harness` 单向；② 删除以 `agents/` 为落点的红线（`tools/tool_*.py` 命名、`tools_config.py` 分配、`role_sys_prompts.py` 提示词入口、`AgentRoleFactory` / `agent_builders.build_*` 装配）；③ `engines/backend_bridge/AGENTS.md` 结构与红线扩到承接事件落库、平台 SOP 取消、语音下线后的边界；④ `engines/ae_harness/AGENTS.md` 目录结构补 `agents/config/app_info/` 与 `log_keywords/` |
| **为什么必须改** | 平台侧不再有第二个 Agent 落点，保留旧清单会让下一位读者按已删目录找入口；红线指向的代码将不存在，规则失去可执行性 |
| **影响面** | 删 `engines/agents` 88 文件 / 14106 行 + 6 类配置资产；删 `backend/apps/knowledge_assistant` 8 文件与前端 17 文件；改后端 10 个模块；`backend_bridge` 增至约 25 文件 / 2500 行；68 个测试文件需改或删；5 个 openspec 主规格落点调整 |
| **怎么回退** | 单主干 `Kahoku` 逐批提交，B0～B4 各一个 commit；`git rm -r engines/agents` 只在 B4 执行，之前每批提交后 `python run.py check` 全绿。任一批出问题单独 revert 该 commit，回到「包仍在、链路已切」的可用态 |

## Goals / Non-Goals

**Goals:**

- 删除后仓内只有一个 Agent 落点、一份原语、一条依赖方向。
- 平台任务链（启动、取消、事件落库、报告、用量）在删除后行为不变。
- 退役状态可被 `python run.py check` 机械校验，防止回潮。

**Non-Goals:**

- 不改 SOP 的步骤语义、不新增步骤 YAML、不改验收判据。
- 不改前端 AI 助手对话页、任务列表页、报告页的既有展示。
- 不顺带重写 `ae_harness` 的 adb 工具、事件渲染或 SOP 抽象。
- 不恢复 TTS（现状无生产调用方）。

## Decisions

### D1 整包删除，而不是保留「UI 执行子集」

删除 `config`/`models`/`case_file` 后，`platform_run → ui_auto_workflow → step_brief` 与 `agent_builders → assistant → models` 两条链会同时断，剩下能独立存活的部分不足 1.5k 行，且全部是 `backend_bridge` 已在做的事。保留半包会留下无人调用的死代码与二套工具/二套向量库。

**备选**：先把 `task_list` 切到 `sop_ui`、再分批删子集（我原先提的 B 方案）——在多轮决策收缩后收益不再成立，改为一次性收口。

### D2 任务不再落事件明细，改为直出报告 + 列表直达

平台任务的事件落库链（`EventRecord` → 折叠 → `TaskEventSink`）与 `ae_harness` 的记录模型不是同一种形状：前者按 `ModelCallEndEvent` / delta / 媒体分片落 `task_events`，后者产 `RunRecord`（步骤 + 观测 + 用量）。要让两者对齐得写一层逐字段翻译，且保真度只能靠真机比对。

需求方决定**不迁移这层翻译**：任务清单不要详情，跑完直接看 `backend_bridge` 生成的 HTML 报告（`REPORT_ROOT`）。于是 `EventRecord`、事件折叠与 `task_events` 写入随旧包退役，报告改为「一份 HTML 直出」。

**备选**：给 `run_sop` 加 `on_event` 钩子 + 翻译适配器（约 200–300 行）—— 被否决，因为产品不再需要事件明细。

**影响**：`/api/tasks/{id}/report/` 的任务详情报告下线；用量与费用仍走既有账本，口径不变。

### D3 用例 YAML 通道直接下线，不搬去 `backend_bridge`

用户决策为「用例 YAML 模型去掉」，且步骤统一改走 SOP steps YAML。若把 `case_file` 搬走，等于同时维护「用例 YAML」与「SOP steps YAML」两种步骤格式，与 `backend_bridge/AGENTS.md` 红线「禁止自创步骤格式」冲突。

**后果（已在 proposal 声明）**：`case_manager` 的 YAML 导入/导出与 `task_list` 的 YAML 附件入口下线；用例库不再接受 YAML 文件。

### D4 提示词以「各取较新者」为基线合并

执行者取 `ae_harness` 版（含新增锚点与工具说明），验收者取 `agents` 版（比 harness 版更厚、判据更严）；`CASE_*` 两份一致，直接随包删除。合并后统一放 `engines/ae_harness/agents/config/prompts/`，差异在 B2 由人工比对一次并记录到 `tasks.md` 勾选项，不静默择一。

**备选**：两个都取 harness 版——会削弱验收强度，属于无声明地改变执行质量。

### D5 配置资产按「执行链在用 / 已无用」二分

| 资产 | 处置 | 理由 |
| --- | --- | --- |
| `app_info/` | 迁 `ae_harness/agents/config/app_info/` | 执行者要靠应用短卡拿被测应用上下文 |
| `log_keywords/` | 迁 `ae_harness/agents/config/log_keywords/` | 验收者按机型核对日志证据 |
| `prompts/` | 合并为 4 份（删 `KNOWLEDGE_CHAT_PROMPT`） | 见 D4 |
| `models.yaml` | 以 `ae_harness` 版为准，比对后只留一份 | 单一模型表 |
| `knowledge_bases.yaml` | 只留 `ae_harness/knowledge/config/` 一份 | 知识库唯一配置 |
| `skills/` | 随包删除 | 无运行时调用方，仅被两个检查器的跳过名单引用 |

### D6 向量库留 `ae_harness/knowledge/`，索引重建不迁移

`agents/rag` 随包删除；`ae_harness/knowledge/` 保留。索引不迁移 SQLite 文件（切块版本与表结构独立，直接迁移会带不确定性），改为在 B1 用 `python -m engines.ae_harness.knowledge index` 重建一次，并把 `data/rag_index/` 删除。

### D7 批次顺序：先切后删，删除放最后

`case_file` / `config` / `models` 一删，`platform_run` 立即断链，`task_list` 会直接不可用。因此顺序固定为：**B0 解反向依赖 → B1 下线知识助手 → B2 平台任务链切换（含事件落库与取消）→ B3 删用例 YAML 通道 → B4 整包删除**。每批一个 commit，B4 之前包一直处于可运行状态。

### D8 新增退役门禁，先加检查再删包

在 B0 就把静态检查写进 `utils/check_gates.py`：`engines/agents` 目录缺失、全仓无 `engines.agents` 导入、无 `knowledge_assistant` 路由与前端模块。检查以「允许清单递减」方式加入，避免 B4 前自己先红。

## 模块防火墙自检

- 跨 App import：本次不新增任何 `backend/apps` 之间的跨 App 依赖；`task_list`、`case_manager` 对引擎的调用点减少而非增加。
- 禁止跨 App import service/runner/consumer：删除 `knowledge_assistant/consumer.py`，不存在把 consumer 引入其它 app 的新路径。
- INSERT/UPDATE/DELETE 收敛到 `api.py`：事件落库迁入 `engines/backend_bridge` 后仍由后端既有写入入口执行，`engines` 侧零数据库写入。
- 前端不直连数据库：删除知识助手模块，其余页面不动；仪表盘无写操作，无变化。

## Risks / Trade-offs

- [验收强度下降] 验收者提示词换版 → B2 用 agents 版为基线合并，并在真机跑一轮 `run_ui_sop` 对比驳回率。
- [用例 YAML 入口消失导致用例库变只读] → 在 B3 前设置决策点（见待决策），确认用例数据的后续来源，未确认不执行 B3。
- [平台任务链切换引入回归] → B2 保留 `run_ui_sop` 与旧 `run_platform_sop` 并存一个 commit，回归通过后再删旧路径。
- [提示词与短卡迁移遗漏] → B4 前用 `grep -rn "config/data"` 兜底扫描残留引用。
- [索引重建期间知识检索不可用] → `ae_harness/knowledge` 当前未挂载，重建期间无生产影响。

## Migration Plan

1. **B0**：`engines/device` 改走 `utils.logs`；`check_gates` 加退役检查（允许清单先含现状）。
2. **B1**：删知识助手（后端 app、前端模块、路由/侧栏、2 个规格、`tests/knowledge`）；删 `agents/{knowledge_chat,realtime_vocie,realtime_vocie_agent,workflow/voice,rag}`；重建 `ae_harness/knowledge` 索引并删 `data/rag_index/`。
3. **B2**：`messaging/{event_sink,record,fold}` 与 `platform_run` 的取消能力迁入 `backend_bridge`；`task_list` 切到 `sop_ui`；合并提示词、迁 `app_info` 与 `log_keywords`。
4. **B3**：删 `case_file`/`case_goal_workflow`/`case_artifact*`/`step_brief`，下线 `case_manager` 与 `task_list` 的 YAML 入口（需先过决策点）。
5. **B4**：删 `engines/agents` 余下部分、6 类配置资产与无效引用；门禁转为「目录必须不存在」。
6. 各批之间跑 `python -m pytest -c tests/pytest.ini` 对应子集与 `python run.py check`，全部通过才进下一批。

**回退**：逐批 `git revert` 对应 commit。B2 之前回退无数据影响；B3 之后若需恢复 YAML 通道，需从归档规格重建，成本较高，故 B3 单独成 commit 且不与其他批次合并。

## Open Questions

1. **`case_manager` 用例库的数据来源**（阻塞 B3，不阻塞立单）：YAML 导入/导出下线后，用例库是转为只读历史数据、改由 `sop/steps` YAML 替代录入、还是在 `backend_bridge` 重建一套用例模型？三者工作量差异大，需在 B3 前定。
2. `data/rag_index/` 删除后是否需要保留一份只读归档（当前判定：不需要，`ae_harness/knowledge` 从 `product_manuals` 源文档重建）。
