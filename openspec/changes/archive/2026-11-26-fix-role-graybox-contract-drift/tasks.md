## 1. 使用名单漂移（test_role_kinds.py）

- [x] 1.1 `_config()` 改为接收操作员并补名单：建 `AIModelConfig` 后 `ModelUseGrant.objects.create(user_id=int(user.id), model_config=config)`；同步全部调用点。
  验证：`.venv\Scripts\python.exe -m pytest -c tests/pytest.ini tests/ai_assistant/api/test_role_kinds.py -q` 8 条全绿。

## 2. 入参契约漂移（test_roles.py）

- [x] 2.1 入参改用 `model_config_id` + `kinds`；`_FIELDS` 补 `kinds`；`list_orders_newest_first` 的直建角色改传 `model_config`。
  验证：`pytest ... tests/ai_assistant/api/test_roles.py -q` 中 create / list 相关条目转绿。
- [x] 2.2 局部更新改为换 `model_config_id` 并断言派生的 `model_name` 跟随变化、其余字段不变；「任意 model_name 可接受」改为「名单外 model_config_id 返回 403」。（偏差：`RoleViewSet.create` 里 `can_select_model` 在 `create_role` 之前，未知配置命中的是名单校验而不是外键校验，实测 403 而非 400）
  验证：同上文件全绿。

## 3. 关单

- [x] 3.1 `pytest -c tests/pytest.ini tests/ai_assistant -q` 全组通过（此前 15 红）。
- [x] 3.2 `ruff check` + `ruff format --check` 通过。
- [x] 3.3 `openspec validate fix-role-graybox-contract-drift` 通过。
