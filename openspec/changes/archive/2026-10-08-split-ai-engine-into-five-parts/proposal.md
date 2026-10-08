# AI 引擎内部结构拆分为五个部分

## Why

`engines/ai/agents/` 现在是个大杂烩：智能体装配、工作流编排、工具包装、回复解析、点击与日志证据、用量与计费全挤在同一层，最大单文件 903 行；改一处要看五件事。其中"把智能体回复读成语义记录"（思考 / 工具调用 / 工具返回 / 截图路径）的代码散在智能体类内部，是本链路最容易出错的部位——它靠**事后翻上下文**推导，代码注释里已记着"真机验证时踩到过"。

下一步已确定要把智能体通信改为**事件流消费**（框架本身提供逐条事件），并预留 MCP 客户端与工具组。在杂烩目录上继续叠加能力，成本只会更高；先把内部职责分成五块，替换面才能收敛在一个包内。

## What Changes

- 把 `engines/ai/` 按五个职责重新分层：**智能体 / 消息与事件 / 工具 / 工作流 / 费用计算**；引擎协议、注册表与组合根（引擎入口）留在本层。
- 五部分与现有文件的对应关系见 design.md「Decisions · D1」；每个包的职责与可用方向在 design.md 固定下来。
- **BREAKING**（限仓库内部引用者）：引擎内部模块路径变化，外围 3 个后端文件与 11 个单元测试文件中**约 7 个**的 import 需同步改写（其余引用的是保持原位不动的 `agents/config.py`、`agents/model.py`）。引擎**对外**的协议（任务单 / 结果单）、注册名（`settings.AI_ENGINE = "agentscope"`）、提示词常量路径（`engines/ai/agents/config.py`）均不变。
- 本单只做结构搬迁：**零行为变化**——函数体不重写、提示词与工具子集不改字、日志文案不改、结果字段不改、前端不改、数据库不改、不新增通道。

## 关联文档

无关联需求编号：本单是纯内部重构（结构分层），不改变任何对外行为与验收口径，故不关联 PRD / ARCH 需求条目。承接它的第二单「智能体通信改为事件流消费并直接以日志形式打印」另行立项。

## Capabilities

### New Capabilities

无。本单不引入任何新能力。

### Modified Capabilities

无。本单不改变任何能力的验收行为：`ai-engine-protocol`（协议、任务单/结果单、提示词归属、注册 fail-fast）、`ai-multi-agent-orchestration`、`ai-executor-log-check`、`device-log-evidence`、`ai-model-debug` 的对外行为全部原样保留；提示词常量路径刻意保持 `engines/ai/agents/config.py` 不变，主规格正文无需改动。按 schema 约定，纯重构在 `.openspec.yaml` 设 `skip_specs: true`。

## Impact

- **引擎**：`engines/ai/` 9 个 Python 文件归位到 5 个职责包 + 1 个组合根；注册表内一条 import 路径改写（`engines.ai.agents.engine.AgentScopeEngine` → `engines.ai.engine.AgentScopeEngine`）。
- **后端**：`apps/ai_assistant/model_debug.py`（现直接引用引擎 4 个内部模块，改为经引擎包级公开入口引用）、`management/commands/ui_pipeline.py`、`management/commands/model_test.py` 三处 import 同步改写。不改接口、字段、写库路径。
- **测试**：11 个单元测试文件（`test_ai_engine_config` / `test_ai_model_debug` / `test_ai_role_tool_subsets` / `test_ai_executor_output_contract` / `test_ai_verifier_output_contract` / `test_ai_executor_log_check` / `test_ai_debug_log_check` / `test_ai_platform_tool_debug` / `test_ai_workflow_log_evidence` / `test_ai_workflow_progress` / `test_device_log_read_tool`）引用引擎内部路径，其中约 7 个需改 import，**断言行零改动**；架构守卫 `tests/arch/test_channels.py` 的 AgentScope 段按新布局复核，并把"不得出现 adapters / rag"的检查范围随布局扩展到 `engines/ai` 根。
- **文档**：主规格与前端模块约束、接口文档中引用的提示词常量路径不变，预期零改动；完成后以 grep 复核。
- **前端 / 数据 / 通道**：零改动（无迁移、无新端点、无 WS / SSE）。

## 非目标

- 不新增任何行为：不接 MCP 与工具组实现、不改权限姿态、不改 `reply()` 的调用方式（事件流属第二单）。
- 不引入未接线的参数或占位类来"表示留位"；接缝以"唯一构造点"的形式存在（见 design.md D6）。
- 不拆 `config.py`、不重命名提示词常量、不改提示词正文与工具子集。
- 不清理既有事实之外的周边（例如模型调试台仍以进程内直调方式使用引擎角色）。
