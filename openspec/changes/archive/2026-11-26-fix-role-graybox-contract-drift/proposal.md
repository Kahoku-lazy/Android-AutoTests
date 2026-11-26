## Why

`tests/ai_assistant/api/test_roles.py` 与 `test_role_kinds.py` 在 HEAD 上 **15 条全红**，与本轮任何改动无关（`fix-assistant-log-report-id-404` 关单时用 stash 复现过）。两处漂移：

1. **使用名单**：生产路径 `api.create_model_config` 会把新模型自动写进全部超管的 `ModelUseGrant`；用例用 ORM 直接建 `AIModelConfig`，绕过了这一步，于是 `RoleViewSet.create` 的 `can_select_model` 判定失败，返回 403。
2. **入参契约**：`RoleInputSerializer` 早已是 `name` / `model_config_id` / `kinds` / `system_prompt`，`model_name`、`provider` 等是 `RoleOutputSerializer` 从 `model_config` 派生出来的只读字段；`test_roles.py` 仍按旧的 `model_name` 入参写，报 `TypeError` / `KeyError: 'role_id'`。

## What Changes

- **只改用例，不改生产代码**：两处漂移都证明是用例过期，生产契约是权威。
- `test_role_kinds.py`：`_config()` 改为「建 `AIModelConfig` + 给当前操作员建 `ModelUseGrant`」，与生产创建路径的授予行为一致。
- `test_roles.py`：按现契约重写 —— 入参加 `model_config_id` 与 `kinds`；`_FIELDS` 补 `kinds`；「任意 model_name 可接受」改为「不存在的 model_config_id 返回 400」；其余断言（路由、中间件 401、201 全字段、倒序、局部更新只改提交字段、删除后 404、重名 409、空名 400）保留。
- 不新增用例层，不把用例搬回 `tests/<模块>/unit/`（口径见 `tests/AGENTS.md`）。

## 关联文档

无 PRD 编号：来源是 2026-11-26 关单复跑时发现的用例漂移，属测试资产维护，不对应需求条目。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

（无 —— 生产行为不变，规格未动；本变更已在 `.openspec.yaml` 置 `skip_specs: true`）

## Impact

- **测试**：`tests/ai_assistant/api/test_roles.py`、`tests/ai_assistant/api/test_role_kinds.py`
- **生产代码**：0 行
- **接口**：不变
- **依赖与迁移**：无
