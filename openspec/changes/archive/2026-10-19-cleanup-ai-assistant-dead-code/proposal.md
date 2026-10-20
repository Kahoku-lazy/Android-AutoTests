## Why

`apps/ai_assistant` 从「规划工作流引擎」切到「平台 SOP」后，旧链路的适配层、查询函数与异常类留下了 11 处零引用符号和若干死片段；它们既误导后续维护者（看起来仍在使用），也让 `api.__all__` 这份跨模块契约失真。先做零行为变化的删除，把真正的功能缺口（过程记录、费用）留给后续独立变更。

## What Changes

- 删除 `api.py` 中仓内零引用的查询函数：`get_agent`、`get_agent_by_scope_id`、`list_active_agents`、`get_conversation`、`get_or_create_conversation`、`log_confirm_result`，并从 `__all__` 同步移除。
- 删除 `permissions.check_can_delete_agent`（从未被调用）。
- 删除 `skills_catalog.list_enabled_skill_dirs`（唯一调用方 `model_assembly.py` 已在本轮清理中删除）。
- 删除 `views_drf.call_model_api`（模型探测统一走 `_call_config_api`）。
- 删除 `views_toolbox_drf.Conflict`（409 异常类从未 raise），并移除随之不再使用的 `APIException` import。
- 删除 `engine_adapter._resolve_device_serial` 兼容别名。
- 删除 `views/tool_gateway.py::_model_to_dict` 内的空 `if hasattr(instance, "page")` 死块。
- 合并 `views_drf.py` 三处函数内重复的 `from rest_framework.exceptions import ValidationError`。
- 清理 `tools.PARAM_LABELS` 中已无对应平台工具的 18 条参数标签。
- 删除生产零调用的进度写库链：`task_runner.persist_task_progress_safe`、`api.patch_task_progress`、`views_drf` 的 `noqa: F401` 再导出，以及守护它的 `test_task_progress_persist.py`。
- 不在本单内：`AIExecutionLog` 表、会话/聊天整栈、僵尸端点、死字段（需迁移或改 API 面，另行立项）。

## 关联文档

纯实现层清理，无需求级行为变化，不关联 PRD 编号。`skip_specs: true`。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

无（删除的均为零引用符号与死片段，对外行为、路由、响应形状均不变）。

## Impact

- 代码：`apps/ai_assistant/` 下 `api.py`、`permissions.py`、`skills_catalog.py`、`engine_adapter.py`、`task_runner.py`、`tools.py`、`views_drf.py`、`views_toolbox_drf.py`、`views/tool_gateway.py`。
- 测试：删除 `tests/graybox/unit/test_task_progress_persist.py`；其余测试不改。
- API / 数据库 / 前端：无变化。
- 验证：`python manage.py check`、`ruff check`、`ruff format --check`、`pytest tests/graybox/unit -k "ai_ or task_"`。
