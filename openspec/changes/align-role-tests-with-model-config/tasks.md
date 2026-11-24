# Tasks: align-role-tests-with-model-config

> 实施于 2026-11-24。**只改测试资产**，产品代码与规格零改动。

## 1. test_role_kinds.py（只补授权）

- [x] 1.1 `_config(user)` 改为接收用户：建 `AIModelConfig` 后为该用户建一条 `ModelUseGrant`；`_create()` 用 `_config(user)`，各用例用 `_config(operator)`。
  - 验证：`test_role_kinds.py` **11 passed**（此前 8 红）
- [x] 1.2 权限语义未动：没有放宽 `can_select_model()`、没有改 `is_operator`；「无授权 → 403」继续由 `test_model_grant.py` 覆盖。

## 2. test_roles.py（按新契约重写）

- [x] 2.1 夹具 `user` 加 `OPERATOR_GROUP`（角色写操作要求运营）；新增 `_config(user)` 建配置并授权，返回配置主键。
  - 验证：写操作不再 403
- [x] 2.2 创建请求统一改传 `model_config_id` + `kinds`（新契约 `RoleInputSerializer`）；`_FIELDS` 补 `kinds`。
  - 验证：`test_create_returns_201_and_full_record` 通过，字段集合与 `RoleOutputSerializer` 一致
- [x] 2.3 旧断言「任意模型名可用」删除，替换为 `test_model_outside_grant_is_403`（未授权模型建角色 → 403 且不落库）。
- [x] 2.4 其余用例保持原意图并转绿：列表倒序（`AIRole` 直建改用 `model_config_id`）、部分更新只改提交字段（改 `system_prompt`，断言 name / model_config / role_id 不变）、删除后 404、未知 id 404、重名 409、空名 400。
  - 验证：`test_roles.py` **11 passed**（此前 7 红）

## 3. 关单

- [x] 3.1 `python -m pytest -c tests/pytest.ini tests/ai_assistant -q` → **68 passed，0 failed**（此前 15 红 / 54 绿）
- [x] 3.2 `ruff check` 通过；`ruff format --check` → **2 files already formatted**
- [x] 3.3 `npx openspec validate align-role-tests-with-model-config` → **valid**
