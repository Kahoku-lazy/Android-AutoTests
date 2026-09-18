## 1. 工具层：FunctionTool 方案

- [x] 1.1 新建 `apps/ai_assistant/agent_scope/tools.py`：`PlatformFunctionTool(FunctionTool)` 权限子类（只读 ALLOW / 写 ASK）+ `TOOLS` 注册表骨架（工具名 → (函数, is_read_only)）+ `build_toolkit(tool_names)`；验证：`python manage.py check` + `ruff check apps/ai_assistant/agent_scope/tools.py` 通过
- [x] 1.2 迁移 33 个工具为普通函数（`device_action` 返回 JSON ToolChunk、`screenshot_page` 返回含 `DataBlock(Base64Source)` 的 ToolChunk），函数内直调 `apps.device_pool.api` / `apps.device_inspector.api`；验证：单测断言 `screenshot_page` 返回 ToolChunk 含图片 DataBlock、`device_action` 返回文本 ToolChunk
- [x] 1.3 删除 `tool_registry.py` + `in_process_tool.py`，同步改写引用（`api.py`/`views_drf.py`/`tool_gateway.py` 的 TOOL_SCHEMAS/TOOL_CATEGORIES/resolve 改读 `tools.py`）；验证：`ruff check` + `pytest tests/ai_assistant -m "unit or integration"` 中不再 import 已删文件

## 2. 智能体管理：agent_manager.py

- [x] 2.1 新建 `apps/ai_assistant/agent_scope/agent_manager.py`：`Harness` dataclass（name/provider/model_name/system_prompt/tools/parameters/context_config/react_config/enabled）+ `INTENT_PROMPT` + `INTENT_VISION/REASONING/STRONG` 常量 + `AgentManager`（`_build` 建 4 套 Harness、`get_harness`、`is_strong_enabled`、`build_agent` 装配 `Agent(name, system_prompt, model, toolkit, context_config, react_config)`）；验证：单测断言 4 套 Harness 构建成功、strong 默认 `enabled=False`、`build_agent` 返回 AgentScope Agent
- [x] 2.2 单测 `Harness` 字段默认值 + `is_strong_enabled` 开关语义；验证：`pytest tests/ai_assistant/test_agent_manager.py` 通过

## 3. 模型实例 + 意图路由：model_instance.py

- [x] 3.1 新建 `apps/ai_assistant/agent_scope/model_instance.py`：`create_model`（按 provider 分发 `DeepSeekChatModel`+`DeepSeekCredential`+`Parameters` / `OpenAIChatModel`）+ `IntentResult` dataclass + `run_intent`（`model.__call__` + 容错解析 `{intent, intent_code, prompt}`）+ `route`（强模型开关短路 / code 1/2 选择）+ `resolve`（返回 agent + prompt）；验证：`ruff check` 通过
- [x] 3.2 单测 `create_model` 分发（deepseek → DeepSeekChatModel、其它 → OpenAIChatModel）、`route` 三路（开关 ON / code=1 / code=2）、`run_intent` 容错（合法 JSON / 垃圾输出 / 模型异常降级 code=2）；验证：`pytest tests/ai_assistant/test_model_instance.py` 通过

## 4. Django 薄壳改造

- [x] 4.1 改造 `views/chat_views.py`：`_agent_stream` 退化为「读配置建 `AgentManager` → `resolve(manager, dialog)` → reply_stream 流式 → `save_message`」，移除其中的意图分类、`_restore_context` 裁剪、`_build_history_text` 等智能体逻辑（已删 `agent_factory.py` / `intent_router.py`）；验证：`python manage.py check` + `ruff check`，SSE 仍流式返回
- [x] 4.2 下线知识库/技能相关入口：删除 `rag_service.py`、`skill_registry.py`、`init_knowledge_base.py`，`views_knowledge_drf.py` 改空壳（接口保留返回空）；验证：`pytest tests/ai_assistant -m "unit or integration"` 无残留 import，`manage.py check` 通过

## 5. 全链路验证

- [x] 5.1 跑后端门禁：`python manage.py check && ruff check && pytest tests/ai_assistant -m "unit or integration"`；验证：命令全绿、无回归（92 passed）
- [x] 5.2 跑架构红线：`python tools/gen_arch_stats.py --check-boundaries`（跨模块 import/写库合规）；验证：零违规
- [ ] 5.3 端到端手测（≥2 次）：真实对话分别输入「点击涂鸦」（意图 code=1 → 视觉 Harness）、「测试制冰机功能」（意图 code=2 → 推理 Harness）、「你好」（code=2 → 推理 Harness 兜底），强模型开关 ON 时短路；验证：意图路由正确、SSE 流式正常、截图回显正常
