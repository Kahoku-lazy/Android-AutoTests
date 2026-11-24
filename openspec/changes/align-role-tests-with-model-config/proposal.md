# Proposal: align-role-tests-with-model-config

## Why

`tests/ai_assistant` 全组有 **15 项红**，集中在两个文件，且**都不是产品缺陷**：

| 文件 | 红数 | 报错 |
|---|---|---|
| `tests/ai_assistant/api/test_roles.py` | 7 | `403` / 断言字段集合不符 |
| `tests/ai_assistant/api/test_role_kinds.py` | 8 | `403` + `{'detail': '不能使用该模型'}` |

根因是**两层欠账叠加**，都发生在角色 API 的两次演进之后：

1. **权限模型变了，夹具没跟上**
   - `RoleViewSet` 的写操作要求 `is_operator()`（`views_drf.py:118/144/172/192`），而 `test_roles.py` 的 `user` 夹具造的是普通用户 → 403。
   - 建/改角色还要 `can_select_model()` —— `ModelUseGrant` 里没有该用户那份名单就一律 False（**超管也不例外**，`api.py` 注释写明「空名单对任何模型都返回 False」），`test_role_kinds.py` 的 `operator` 夹具没授权 → 「不能使用该模型」403。
2. **契约变了，用例还在写旧形状**
   - 角色创建现在必填 `model_config_id`（`RoleInputSerializer`），`test_roles.py` 仍在传自由文本 `model_name` → 修好权限后也会 400。
   - 出参多了 `kinds`（`RoleOutputSerializer`），而 `test_roles.py` 的 `_FIELDS` 常量没这项 → 字段集合断言必挂。

所以这不是「补两个 fixture」能收的：`test_roles.py` 需要按新契约重写，`test_role_kinds.py` 只需要补授权。

## What Changes

- **`test_roles.py`**：夹具用户改为运营（`OPERATOR_GROUP`）；新增模型配置 + 给夹具用户授权
  （`ModelUseGrant`）；创建请求改用 `model_config_id`；`_FIELDS` 补 `kinds`；
  把「任意模型名可用」这条旧断言改为「未知 `model_config_id` → 400」。
  **保留原有测试意图**：201 + 字段集合、列表倒序、部分更新只改提交字段、删除后 404、未知 id 404、重名 409、空字段 400。
- **`test_role_kinds.py`**：`_config()` 之后给 `operator` 授权模型名单，权限语义不动，其余断言保持不变。
- **不碰产品代码**，不动任何规格（`skip_specs`）。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

（无 —— 产品行为正确，改的是测试资产）

## Impact

- **测试**：`tests/ai_assistant/api/test_roles.py`、`tests/ai_assistant/api/test_role_kinds.py`
- **代码**：无
- **回退**：还原这两个文件

## 关联文档

- 权限来源：`openspec/specs/assistant-author/spec.md`（写权限）、`openspec/changes/archive/2026-11-18-model-use-grant/`（模型名单）
- 契约来源：`backend/apps/ai_assistant/serializers.py` 的 `RoleInputSerializer` / `RoleOutputSerializer`
