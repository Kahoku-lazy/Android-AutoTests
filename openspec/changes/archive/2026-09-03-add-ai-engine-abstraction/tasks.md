## 1. 协议层（ai_engines 基础）

- [x] 1.1 新建 `ai_engines/base.py`：定义 `ModelSpec`/`ToolSpec`/`TaskRequest`/`TaskResult` dataclass 与 `AiEngine` Protocol（零 django/apps 依赖）；验证：`ruff check ai_engines/base.py` 通过，`python -c "from ai_engines.base import AiEngine"` 成功
- [x] 1.2 新建 `ai_engines/registry.py`：`AI_ENGINE_REGISTRY` + `get_ai_engine(name)` 惰性加载 + 进程内缓存 + `ConfigurationError` fail-fast；验证：单测覆盖未注册名抛 ConfigurationError、正常名返回单例
- [x] 1.3 新建 `ai_engines/__init__.py` 导出 `AiEngine`/`TaskRequest`/`TaskResult`/`get_ai_engine`；验证：`python -c "import ai_engines"` 成功
- [x] 1.4 `config/settings.py` 新增 `AI_ENGINE = os.environ.get("AI_ENGINE", "agentscope")`（对称 `DEVICE_ENGINE`）；验证：`python manage.py check` 通过

## 2. 平台工具剥离（框架无关）

- [x] 2.1 新建 `apps/ai_assistant/tools.py`：迁移 `agent_scope/tools.py` 中平台工具纯函数 + `TOOLS` 清单 + 只读/自动放行元数据（只 import 各 App api.py，不 import agentscope）；验证：`ruff check apps/ai_assistant/tools.py`，`list_tool_schemas()` 输出与迁移前一致
- [x] 2.2 `agent_scope/tools.py` 仅保留框架包装（`PlatformFunctionTool` + `build_toolkit`），改为接收纯函数 + 元数据；验证：`/api/ai/available-tools` 契约不变

## 3. 迁移 agent_scope → ai_engines/agentscope

- [x] 3.1 迁移 `model.py`/`workflow.py`/`config.py`/`provider_registry.py` → `ai_engines/agentscope/`，重连 import；验证：`python manage.py model_test planner "启动 govee 应用"` 可跑
- [x] 3.2 迁移 `tool_wrapper.py`（框架工具包装层）→ `ai_engines/agentscope/`；验证：`python manage.py platform_task_test ...` 可跑
- [x] 3.3 新建 `ai_engines/agentscope/engine.py`：`AgentScopeEngine.run(TaskRequest) -> TaskResult`，内部装配三 Agent + 跑 workflow + 归一化 `TaskResult`（device_control 结果非空）；验证：`python manage.py platform_task_test ...` 全绿

## 4. Django 解耦（engine_adapter + views_drf）

- [x] 4.1 新建 `apps/ai_assistant/engine_adapter.py`：`build_request(task, agent)` 读 `route_configs` 解密 + 收集 `ToolSpec` → 组装 `TaskRequest`；验证：单测断言 TaskRequest 字段与模型解密正确
- [x] 4.2 改 `views_drf.py` `_run_task_async` 走 `engine_adapter.build_request` + `get_ai_engine(settings.AI_ENGINE).run()`；删除 `agent_scope`/`asyncio.run`/`threading` 编排；验证：`grep -rE "agent_scope|asyncio\.run|AgentScope" apps/ai_assistant/views_drf.py` 无匹配，`ruff check` 通过
- [x] 4.3 结果归一化：两条线路统一 `TaskResult.summary` 落 `AITask.result`（device_control 不再恒空）；验证：单测断言 device_control 结果非空

## 5. 开发工具跟随

- [x] 5.1 改 `model_test.py`/`platform_task_test.py`/`ui_pipeline.py` 从 `ai_engines` 门面取 workflow/engine；验证：三条命令均可执行
- [x] 5.2 清理 `apps/ai_assistant/agent_scope/` 残留目录与过时 import；验证：`grep -r "agent_scope" apps/ai_assistant` 无残留引用

## 6. 门禁与文档同步

- [x] 6.1 `ruff.toml` `known-first-party` 加 `ai_engines`；验证：`ruff check .` 通过
- [x] 6.2 后端门禁：`python manage.py check && ruff check apps/ai_assistant ai_engines && pytest -m "unit or integration or api"`；验证：全绿、无回归
- [x] 6.3 边界检查：`python tools/gen_arch_stats.py --check-boundaries`；验证：零违规
- [x] 6.4 文档同步（已放弃：文档同步不做）

## 7. 回归验收

- [x] 7.1 真机两条线路 E2E 全链路（已放弃：真机验证不做）
- [x] 7.2 换引擎 fail-fast：临时把 `AI_ENGINE` 设为未注册名，确认抛 `ConfigurationError` 且任务落 failed；验证：单测
