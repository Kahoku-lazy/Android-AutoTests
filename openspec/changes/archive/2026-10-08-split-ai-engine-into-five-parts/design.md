# 设计：AI 引擎内部结构拆分为五个部分

## Context

动机见 proposal.md - Why。以下是本方案需要的事实与约束（均以代码为准）：

**现状规模**（`engines/ai/`，共 9 个 Python 文件 / 约 2100 行）：

| 文件 | 行数 | 现在装了什么 |
| --- | --- | --- |
| `agents/workflow.py` | 903 | 三角色编排 + 5 个数据契约 + 进度组装 + 过程记录组装 |
| `agents/model.py` | 734 | 角色规格 / 角色基类 / 三个角色 / 模型连接创建 / 回复解析 / 上下文摘要 |
| `agents/config.py` | 208 | 三角色模型配置 + 三份系统提示词 + 三份工具子集 |
| `agents/logcheck.py` | 209 | 点击证据配对 + 日志证据文本渲染 |
| `agents/tool_wrapper.py` | 100 | 平台工具 → 框架工具包装 + Toolkit 装配 |
| `agents/engine.py` | 77 | 引擎组合根（装配三角色 → 交给工作流） |
| `agents/billing.py` / `usage.py` | 68 / 59 | 价目与单轮费用 / 用量累加 |
| `agents/evidence.py` | 56 | 验收截图落盘 |
| `base.py` / `registry.py` | 112 / 77 | 引擎协议与注册表 |

**约束**：

1. 引擎层零 `django.*` / `apps.*` 依赖；平台工具函数由 `TaskRequest.tools` 注入。
2. 主规格 `ai-engine-protocol` 的「系统提示词随引擎走」明写提示词常量位于 `engines/ai/agents/config.py`；前端模块约束与接口文档也引用该路径。
3. 架构守卫 `tests/arch/test_channels.py` 断言 `engines/ai/agents` 目录存在、且该目录下不得出现 `agentscope/`、`adapters/`、`rag/`。
4. 注册名 `agentscope`（`settings.AI_ENGINE`）表达"用的是 AgentScope 框架"，与目录名无关，本单不动。
5. 本单零行为变化，故验收复用现有测试，只跑与改动直接相关的最小集（不发起全量回归）。
6. 第二单已定：智能体通信改为事件流消费、直接以日志形式打印（框架提供 `reply_stream` 逐条事件：思考/文本/工具调用/工具返回增量与暂停点），不做前端流式推送、不新增通道。
7. **验收集基线（搬迁前，2026-10-08 实测）**：任务清单 §3.1 点名的 11 个单元测试文件 + 架构守卫 `test_channels.py`，共 **164 项全绿**，耗时约 4 分 20 秒。搬迁后该集合必须仍是 164 项全绿——**数量与结果都要对上**，任何失败都归因于本单而非存量问题。

## Goals / Non-Goals

**Goals:**

- `engines/ai/` 内部按「智能体 / 消息与事件 / 工具 / 工作流 / 费用计算」五部分归位，依赖方向单向、无循环。
- 引擎对外只暴露"协议（任务单/结果单）+ 注册表 + 包级公开入口"，上层不再按分包深引用内部实现。
- 为第二单（事件流消费）与后续 MCP / 工具组确定**唯一接缝**，使替换或接线只落在单个包内。
- 现有测试**断言不改**，只改 import 路径。

**Non-Goals:**

- 不改任何行为：函数体不重写、日志文案逐字保留、结果字段与 JSON 键不变、提示词与工具子集不变、计价数值不变。
- 不接 MCP 与工具组实现，不改权限姿态（框架对 MCP 工具与自定义函数工具默认 ASK，平台当前无人工确认通道 —— 属接 MCP 的前置条件，见 D6，本单只登记不实现）。
- 不拆 `config.py`、不把提示词挪出 `agents/`（保持约束 2 的路径有效，使本单成为零规格改动）。
- 不动前端、通道、数据库；不加迁移、不加端点。
- 不引入未接线的参数与占位类（"留位"的口径见 D6）。

## Decisions

### D1 五部分 = 五个包 + 一个组合根，边界按"职责"划，不按"框架概念"划

| 包 | 收编内容（现状 → 新位置） | 唯一职责 | 谁可以用 |
| --- | --- | --- | --- |
| `agents/` **智能体** | `config.py`（原地不动）+ `model.py` 中的角色规格、三个角色类、模型连接创建 | 配一个 Agent：`name` / `system_prompt` / `model` / `toolkit` | 组合根、工作流、模型调试台（经包级入口） |
| `messaging/` **消息与事件** | 从 `model.py` 拆出：`RoleResult` + 回复解析（思考 / 工具调用 / 工具返回 / 截图路径 / 脱敏截断） | 智能体通信的读取与记录；第二单的事件出口落在这里 | 智能体（收本轮报告）、工作流、调试台 |
| `tools/` **工具** | `tool_wrapper.py` | `ToolSpec` → 框架工具 / `Toolkit` 的**唯一构造点**（工具、技能；MCP 与工具组将来的接线点） | 智能体（装配 toolkit） |
| `workflow/` **工作流** | `workflow.py` + `logcheck.py` + `evidence.py` | 三角色编排 + 步骤/结果契约 + 点击与日志证据 + 验收截图落盘 | 组合根 |
| `billing/` **费用计算** | `usage.py` + `billing.py` | 用量累加（总量 / 按模型 / 按角色）+ 价目与单轮费用 | 智能体（算本轮费用）、工作流（累总账） |
| 根 | `base.py`、`registry.py`、`engine.py`（组合根） | 引擎协议、注册表、把任务单装配成工作流 | 后端（经注册表取引擎） |

依赖方向固定为单向，禁止反向（叶子包在下、组合根在上）：

```
registry ──> engine（组合根）──> agents ──> tools
                    |              |  \
                    |              |   └──> billing（叶子）
                    |              └──────> messaging（叶子）
                    └────> workflow ──> agents / messaging / billing
```

- 叶子包：`messaging`、`billing`、`tools`（只依赖 `base.py` 与框架库）。
- `agents → messaging / tools / billing`；`workflow → agents / messaging / billing`；`engine → agents / workflow`。
- `messaging` MUST NOT 反向依赖 `agents`：它只消费框架的消息与事件类型。
- **文件名规则**：既存模块文件**只改位置、不改文件名**。这样主规格与文档引用的 `engines/ai/agents/config.py` 仍然有效，测试改动面也更小；包内文件名冗余（`workflow/workflow.py`、`billing/billing.py`）本单接受，若日后要改名另立小单，不混在本次。唯一新增的文件是消息与事件包内承载"回复解析"代码的模块（该代码从 `model.py` 拆出，需要一个新落点，建议命名 `messaging/messages.py`）。

**文件归位对照表（apply 阶段照此执行）**：

| 现状 | 去向 | 内容与说明 |
| --- | --- | --- |
| `ai/base.py` | 不动 | 引擎协议、任务单/结果单、工具与日志证据提供者协议 |
| `ai/registry.py` | 改 1 行 | 实现路径 → `engines.ai.engine.AgentScopeEngine`；注册名 `agentscope` 不变 |
| `agents/engine.py` | → `ai/engine.py` | 组合根（D3） |
| `agents/config.py` | **原地不动** | 三份提示词 + 三角色模型配置 + 三份工具子集（D2、D2 灰区） |
| `agents/model.py` | 留在 `agents/`，拆出解析部分 | 保留：角色规格、`AgentRole` 骨架、三个角色类、`create_model`、provider 常量 |
| `agents/model.py` 的解析部分 | → `messaging/messages.py`（新文件） | `RoleResult`、思考/工具调用/工具返回收集、工具返回脱敏与截断、截图与路径提取、输入文本提取、上下文摘要（D4） |
| `agents/tool_wrapper.py` | → `tools/tool_wrapper.py` | 工具包装与 Toolkit 装配（D6，全仓唯一构造点） |
| `agents/workflow.py` | → `workflow/workflow.py` | 三角色编排 + 五个契约 + 进度/过程记录组装 |
| `agents/logcheck.py` | → `workflow/logcheck.py` | 点击证据配对 + 日志证据文本渲染（D5） |
| `agents/evidence.py` | → `workflow/evidence.py` | 验收截图落盘（D5） |
| `agents/usage.py` | → `billing/usage.py` | 用量累加 |
| `agents/billing.py` | → `billing/billing.py` | 价目与单轮费用（D7） |
| `ai/skills/` | 不动 | 知识包（5 个技能），与五部分无关 |

**文档与工具链引用（已逐条核实，结论：全部不受影响）**：

- 引用 `engines/ai/agents/config.py` 的共有 6 处——4 份主规格（`ai-engine-protocol`、`ai-executor-output`、`ai-verifier-output`、`ai-device-planner-tools`）、前端模块约束 `frontend/src/modules/ai-assistant/AGENTS.md`、接口文档 `dev_docs/DEV_TEST/接口文档/API-AI助手.md`。该路径保持不动，故全部无需改动（这也是本单能设 `skip_specs` 的依据）。
- 引用 `engines/ai/skills` 的位置（`ruff.toml` 的 vendored 排除项、`tools/check_gates.py` 的 `VENDORED`、前端装配台文案、`ai-shared-skill-upload` 规格、接口文档）不受影响，因为 `skills/` 不移动。
- `tests/arch/` 下**只有** `test_channels.py` 触碰 `engines/ai`，且除那三条路径断言外没有"目录形状"断言，故任务 2.3 的守卫收口是纯增量、不会误伤新包。
- 全仓 `Toolkit(` 构造点核实为**唯一一处**（`agents/tool_wrapper.py`），任务 1.4 的验证口径成立。

**代码引用改动面（已逐文件核实）**：后端 3 个文件需要改 import（`model_debug.py` 深引用 config / logcheck / model 三处；`ui_pipeline.py` 与 `model_test.py` 各改 workflow 一行）。单元测试 11 个文件引用引擎内部路径，其中**恰为 7 个**需要改：`test_ai_model_debug`、`test_ai_debug_log_check`（`RoleResult` → `messaging`）、`test_ai_executor_output_contract`、`test_ai_executor_log_check`、`test_ai_verifier_output_contract`、`test_ai_workflow_log_evidence`、`test_ai_workflow_progress`（`workflow` / `logcheck` 路径）；另 4 个（`test_ai_engine_config`、`test_ai_role_tool_subsets`、`test_ai_platform_tool_debug`、`test_device_log_read_tool`）只引用 `config` / `model`，路径保持有效，**零改动**。

### D2 提示词与角色配置留在 `engines/ai/agents/`，路径不变

主规格与前端约束都写死了 `engines/ai/agents/config.py` 是提示词唯一真相源（约束 2）。保持该路径不动，主规格正文、前端模块约束、接口文档**零改动**，本单成为纯重构（`skip_specs: true`）。

备选：拆出 `agents/prompts.py` 让职责更纯 —— 要连带改主规格正文、前端约束与接口文档，收益不抵改动面；留待第二单或后续按需另立。

**已知灰区（本单刻意不拆）**：`config.py` 里的三角色配置 `DeviceExecutionConfig` 同时携带两个工作流参数（每步最大重试次数 `max_loops`、读日志前等待 `log_wait_seconds`）。按职责它们属于工作流，但拆开就要动 `agents/config.py` 的路径与调用方，与本单"零规格改动"的目标相抵。故本单让它们随 `config.py` 留在智能体包，并在设计中登记为后续可选的小变更（把工作流参数下沉到 `workflow/`）。

### D3 组合根迁到 `engines/ai/engine.py`，注册表值随之改写

组合根做的是"按配置装配三角色 → 交给工作流"，跨五部分，不属于其中任何一块。放在与 `base.py`/`registry.py` 同层，五个子包才各自纯粹。

备选：留在 `agents/engine.py` —— 注册表与架构守卫零改动，但"智能体"包被组合根污染，与本次目的相悖，否决。
影响：注册表内一行路径（`engines.ai.agents.engine.AgentScopeEngine` → `engines.ai.engine.AgentScopeEngine`）；注册名与协议不变。若将来新增第二个框架实现，其组合根按 `engines/ai/<framework>/` 组织，本层的 `engine.py` 是当前实现的组合根。

**必须同步删除的一行（否则成环）**：`agents/__init__.py` 现在写着 `from .engine import AgentScopeEngine`（把引擎入口再导出）。组合根迁出后 `engine.py` 要 import `agents`，而导入 `agents` 的任何子模块都会先执行该包的 `__init__`，于是形成 `agents → engine → agents`（以及经工作流的 `agents → engine → workflow → agents`）。故 `agents/__init__.py` MUST 只导出智能体侧的名字（角色规格与三个角色类、`build_device_models`、角色配置与提示词），MUST NOT 再导出引擎入口；引擎入口只由注册表按模块路径直接取用，上层不直接引用它。

**环检测证据（本轮已实测）**：把现状 9 个文件的 import 语句按上表映射到新归属后做有向图环检测，唯一出现的环正是上述 `agents/__init__.py → engine`。删除该行后依赖图无环，实际边为：`agents → {billing, tools}`、`workflow → {agents, billing}`、`engine → {agents, workflow}`（`messaging` 为叶子、无出边）。

### D4「消息与事件」收编的是"回复解析 + 轨迹/截图提取"

这些函数的实质是"把框架回复读成语义化记录"，与智能体装配无关；第二单要把它们从"事后翻上下文"换成"事件流消费"，归属先立好，替换面就收敛在一个包内（这也是本次拆分的最大收益点）。

边界（只搬这些，不多搬）：`RoleResult` 报告结构、思考/工具调用/工具返回的收集、截图与截图路径提取、工具返回的脱敏与截断、输入文本提取、上下文摘要。
**不搬**：用量累加（属费用计算）、点击与日志证据配对（属工作流证据）、角色规格与提示词（属智能体）。

**接口不变**：`AgentRole` 对外的读取入口保持原签名，改为委派给 `messaging` 的实现——工作流调用的 `tool_results_seen()`（用于"只取本步新增工具返回"的切片）必须继续可用，MUST NOT 改成让工作流直读智能体上下文。搬迁后 `AgentRole` 的公开方法集合与返回类型与搬迁前一致。

### D5 点击证据、日志证据、验收截图落盘归「工作流」

它们的输入是"工具轨迹 + 设备日志窗"，服务的是工作流的判定与留痕（`executor_log_check` / `log_evidence` / 验收证据图），语义上不属于智能体通信。备选：放进 `messaging` —— 会把"设备侧证据"与"智能体通信"混为一谈，第二单做事件流时边界会再次糊掉，否决。

### D6「工具」包只做框架侧包装与装配，平台工具函数本体留在后端

引擎 MUST NOT import `apps.*`（约束 1）。本包是 `ToolSpec` → 框架工具 / `Toolkit` 的**唯一构造点**，因此也是 MCP 客户端与工具组将来唯一的接线点：接 MCP 时只需改本包一个函数入参 + 在智能体侧声明权限姿态，不需要动工作流与消息事件。

**"留位"的明确口径**：本单**不**新增未接线参数、不写占位类、不加 TODO 分支；接缝以"唯一构造点"这一事实存在，并在此登记接线时必然要处理的前置项：

> 框架对**自定义函数工具**与 **MCP 工具**的默认权限是 ASK（需人工确认）。平台当前没有人工确认通道，只因所有写工具都在自动放行名单内才未暴露。一旦接入 MCP，智能体会停在确认点；而现有 `reply()` 会把"停住"当成正常结束（不报错、无结果），任务会以"输出无效"失败。故接 MCP 前 MUST 先在智能体侧显式声明权限姿态（或为工具注入明确的放行规则），并让消息与事件侧识别暂停点。

### D7「费用计算」只搬不改

用量累加与单轮费用保持现状，包括与后端计价表"双份且需同步"的既有关系（`engines/ai/agents/billing.py` 的价目常量与 `apps/ai_assistant/deepseek_billing.py` 对齐）。本单不碰任何数值与口径。

### D8 日志文案逐字保留

链路排障与既有测试按日志文案判读（工具调用/返回、日志窗口、token 消耗、验收结论）。改结构不应改可观测文本：搬迁后同一场景的日志输出 MUST 与搬迁前逐字相同。

### D9 上层只经引擎包级公开入口

`engines/ai/agents/__init__.py` 声明本包的公开导出（角色规格与三个角色类、角色配置）；`engines/ai/messaging/__init__.py` 声明消息与事件的公开导出（角色报告结构 `RoleResult` 等）；`engines/ai/workflow/__init__.py` 声明工作流公开导出（编排与证据渲染函数）。`apps/ai_assistant/model_debug.py` 现引用引擎 4 个内部模块（`agents/config`、`agents/logcheck`、`agents/model`），改为经上述包级入口引用：角色类与配置取自 `agents`，点击/日志证据渲染取自 `workflow`，报告结构取自 `messaging`。调用方式与返回形状不变，方向是收紧而非放开。

## 模块防火墙自检

- **跨 App import**：无新增。引擎仍零 `apps.*` 依赖，工具函数继续经 `TaskRequest.tools` 注入；本单只改引擎内部路径与上层的引用形式。
- **写库路径**：零写库改动，无迁移、无 ORM 变更、无新端点。
- **前端**：零改动（无新端点、无新通道、无字段变化，故前端 api 层与页面均不动）。
- **引擎边界**：上层仍不得 import `airtest` / `uiautomator2`、不得直触引擎内部实现体；本单把 `apps` 对引擎的引用从"分包深引用"收敛为"包级公开入口"，方向是收紧。
- **架构守卫**：`tests/arch/test_channels.py` 的 AgentScope 段按新布局复核——保留"`engines/ai/agents` 必须存在、不得再出现 `engines/ai/agentscope`"，并把"不得出现 `adapters/`、`rag/`"的检查范围从 `agents/` 扩展到 `engines/ai/` 根（语义随布局迁移，不放宽）。

## Risks / Trade-offs

- [搬迁漏改引用 → 运行期 `ImportError`] → 改完全仓 grep 旧路径**零命中**（含 `tests/`、`apps/`、文档字符串）；不留兼容转发模块，避免出现两处真相源。
- [行为被无意识改动] → 本单只做移动与 import 改写，函数体不重写；验收以"相关单测全绿 + 关键常量逐字比对"为准（提示词三份、工具子集三份、5 个数据契约字段名、价目表）。
- [分包后出现循环 import] → 依赖方向按 D1 固定；**已实测发现唯一的环**来自 `agents/__init__.py` 对引擎入口的再导出（见 D3），该行随本单一并删除；关单前以 Python 直接导入注册表路径做一次真导入核验（`get_ai_engine("agentscope")` 能构建即证明无环）。
- [架构守卫语义随目录变化被悄悄放宽] → 在同一单内显式扩展检查范围到 `engines/ai` 根，并在关单时跑 `tests/arch/test_channels.py`。
- [上层深引用被误判为"顺便重构"而扩大改动面] → 仅把 `model_debug.py` 的引用形式改为包级，不改其行为与返回；其余上层文件只改路径字符串。
- [日志文案被顺手"优化"导致排障基线漂移] → D8 明确逐字保留，关单时抽查关键日志格式串未变。

## Migration Plan

1. 先建五个包与组合根，同批把文件搬入并改写全部 import（一次性完成，避免中间态被提交）。
2. 旧路径**不留转发**；全仓 grep 旧路径零命中后方可进入验收。
3. 跑相关最小测试集（见 tasks.md §3），并做关键常量比对与后端自检。
4. 回滚策略：本单无数据库变更、无对外契约变更，回退 = `git revert` 本次提交；不需要数据侧恢复动作。

## Open Questions

- 第二单的日志流形态（日志级别、单步事件条数上限、是否同时落进任务过程记录）尚待定；不影响本单的包边界与接缝选择。
