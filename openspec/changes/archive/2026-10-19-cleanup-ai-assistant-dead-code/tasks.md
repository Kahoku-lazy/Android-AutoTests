## 1. api.py 零引用函数

- [x] 1.1 删除 `get_agent` / `get_agent_by_scope_id` / `list_active_agents` / `get_conversation` / `get_or_create_conversation` / `log_confirm_result`，并同步删除 `__all__` 中对应条目；验证：全仓 grep 上述 6 个名字仅剩 openspec 文档命中，`python manage.py check` 通过
- [x] 1.2 删除 `patch_task_progress` 及其 `__all__` 条目；验证：全仓 grep 仅剩 openspec 文档命中，`python manage.py check` 通过

## 2. 权限、Skill 目录与适配别名

- [x] 2.1 删除 `permissions.check_can_delete_agent`；验证：全仓 grep 零代码引用，`ruff check apps/ai_assistant` 通过
- [x] 2.2 删除 `skills_catalog.list_enabled_skill_dirs`；验证：全仓 grep 零代码引用，`python manage.py check` 通过
- [x] 2.3 删除 `engine_adapter._resolve_device_serial` 兼容别名；验证：全仓 grep 零代码引用，`python manage.py check` 通过
- [x] 2.4 删除 `views_drf.call_model_api`；验证：全仓 grep 零代码引用，`ruff check` 通过
- [x] 2.5 删除 `views_toolbox_drf.Conflict` 与随之失效的 `APIException` import；验证：`ruff check apps/ai_assistant/views_toolbox_drf.py` 通过（无 F401）

## 3. 死片段

- [x] 3.1 删除 `views/tool_gateway.py::_model_to_dict` 内的空 `if hasattr(instance, "page")` 块；验证：`ruff check` 通过，工具网关相关单测通过
- [x] 3.2 合并 `views_drf.py` 三处函数内重复的 `ValidationError` 函数内导入，改用文件顶部已导入的符号；验证：`ruff check apps/ai_assistant/views_drf.py` 通过
- [x] 3.3 按当前 `TOOLS` 实际入参收窄 `tools.PARAM_LABELS`（删除 17 条已无工具的条目），并同步更新守护它的 `test_tool_debug_param_labels.py`；验证：参数标签相关单测通过（未登记参数仍回退英文名）

## 4. 进度写库链

- [x] 4.1 删除 `task_runner.persist_task_progress_safe`、`views_drf` 的 `noqa: F401` 再导出与 `tests/graybox/unit/test_task_progress_persist.py`；验证：全仓 grep `persist_task_progress_safe` 零命中，`python manage.py check` 通过
- [x] 4.2 全仓 grep 复核本单删除的全部符号名均无残留引用；验证：一条 grep 命令输出为 0 条代码命中（仅 openspec 文档）

## 5. 门禁与回归

- [x] 5.1 `python manage.py check` + `python manage.py makemigrations --check --dry-run` 通过
- [x] 5.2 `python -m ruff check apps/ai_assistant` + `python -m ruff format --check apps/ai_assistant` 通过（含既有 `apps.py` 格式修复）
- [x] 5.3 AI / 任务相关单测回归：apply 期间仓内测试目录被并行重构（`tests/graybox` 整体移除），重构前该切片为 **158 passed / 1 failed**，唯一失败为既有的 `TaskStatus.cancelled` 断言过期（与本单无关）；重构后跑现存架构门禁 `pytest tests/arch -q` → **27 passed**
- [x] 5.4 `python tools/gen_arch_stats.py --check-boundaries` 仍为零违规
