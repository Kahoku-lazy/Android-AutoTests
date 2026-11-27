## 1. 写库回到 api.py（task_list）

- [x] 1.1 `backend/apps/task_list/api.py` 新增 `save_task_run_payload(task, payload)` 与 `clear_tasks()`，并入 `__all__`。
  验证：`tests/arch/unit/test_view_write_convergence.py` 中 `task_list/views.py` 用例转绿。
- [x] 1.2 `backend/apps/task_list/views.py` 两处 `task.result=…; task.save()` 与清空端点 `Task.objects.all().delete()` 改调 api。
  验证：`python -m pytest -c tests/pytest.ini tests/task -q` 全绿。

## 2. 删号即失效（gateway）

- [x] 2.1 `backend/gateway/middleware.py` 的 `_disabled_account_response()` 区分三态：行不存在 → 401，停用 → 403，数据库异常 → 放行。
  验证：`tests/arch/unit/test_auth_single_verify.py::test_deleted_user_still_rejected` 转绿；`tests/auth -q` 全绿。

## 3. 前端死调用清理

- [x] 3.1 删除 `frontend/src/modules/ai-assistant/api/agents.ts`（整份死代码）。
  验证：`tests/arch/unit/test_api_path_callers.py` 中 `/ai/agents/` 的两条消失；`cd frontend; npm run typecheck` 通过。
- [x] 3.2 `frontend/src/modules/ops-console/api.ts::setOpsUserOperator` 改为模板内联三元。
  验证：同文件守护用例转绿，`/ops/users/{id}/grant-operator/` 与 `revoke-operator` 两条解析成功。

## 4. API 文档说明补齐

- [x] 4.1 新增 `backend/shared/api_docs.py`：资源中文名 + 动作动词规则表 + `OVERRIDES`，提供 `describe_operations` postprocessing hook。
  验证：`tests/arch/unit/test_api_docs_surface.py::test_every_operation_has_a_description` 转绿。
- [x] 4.2 `backend/config/settings.py` 的 `SPECTACULAR_SETTINGS` 注册 `POSTPROCESSING_HOOKS`。
  验证：`python manage.py spectacular --validate --file temps/schema-out.yaml` 退出码 0；抽样确认多个摘要为中文。

## 5. 关单

- [x] 5.1 `python -m pytest -c tests/pytest.ini tests/arch/unit -q` 0 失败（原 4 条红）。
- [x] 5.2 `python -m run check` 阻塞项 30/30。
- [x] 5.3 `openspec validate fix-arch-guard-backlog` 通过。
