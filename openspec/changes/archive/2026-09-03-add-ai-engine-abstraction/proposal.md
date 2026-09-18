## Why

AI 助手已收敛为「任务发布」模式，但 Django 层（`views_drf.py`）仍直接 import `agent_scope` 框架内部实现、自己 `asyncio.run` + `threading.Thread`，返回契约是松散 dict，device_control 结果还恒为空。换 AgentScope → LangChain/Agno 必须改视图逻辑。需把 AI 能力抽成可替换「引擎」：Django 只传「任务表单 + 模型 + 工具」，引擎返回归一化结果。

## What Changes

1. 新建顶级包 `ai_engines/`：`base.py`（`AiEngine` Protocol + `ModelSpec`/`ToolSpec`/`TaskRequest`/`TaskResult` 纯类型）、`registry.py`（`AI_ENGINE_REGISTRY` + `get_ai_engine`，fail-fast）。
2. 迁移 `apps/ai_assistant/agent_scope/` 框架专用代码 → `ai_engines/agentscope/`（engine/model/workflow/tool_wrapper/provider_registry）。
3. 平台工具纯函数留在 Django 层（`apps/ai_assistant/tools.py`，只调各 App api.py），经 `TaskRequest.tools` 注入引擎。
4. 新增 `apps/ai_assistant/engine_adapter.py` 组装 `TaskRequest`；`views_drf.py` 解耦为「调 engine_adapter + `get_ai_engine().run()`」。
5. `config/settings.py` 加 `AI_ENGINE`（默认 `agentscope`）；结果归一化为 `TaskResult`，修 device_control 结果恒空。

**BREAKING**：无——`/api/ai/tasks/submit` 契约、`AITask` 表、前端均不变。

## 关联文档

- ARCH：`dev_docs/03-设计与架构/ARCH-08-AI助手.md`（§1.1 进程内 Agent、§3.1 文件结构、§3.2 进程内构建）
- 设计：`plans/ai-engine-abstraction.md`（D1~D7 决策、P1~P7 迁移）
- 规则：`android-autotests-rules`（引擎边界 L1c、防火墙、通道封闭集合）

## Capabilities

### New Capabilities

- `ai-engine-protocol`: AI 引擎抽象协议——Django 经 `AiEngine.run(TaskRequest) -> TaskResult` 调用可替换 AI 引擎；引擎零 apps 依赖（工具经注入）；换框架只换引擎实现。

### Modified Capabilities

（无）

## Impact

- 后端：新建 `ai_engines/`；`apps/ai_assistant` 的 `agent_scope/` 迁出、新增 `engine_adapter.py`/`tools.py`、`views_drf.py` 解耦。
- 配置：`config/settings.py` 加 `AI_ENGINE`；`ruff.toml` known-first-party 加 `ai_engines`。
- 规则/文档：`android-autotests-rules` 引用路径、ARCH-08、`apps/ai_assistant/AGENTS.md`。
- 测试：开发命令 `model_test.py`/`platform_task_test.py`/`ui_pipeline.py` 跟随；真机两条线路回归。
