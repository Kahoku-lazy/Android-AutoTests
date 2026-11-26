## Context

`RoleViewSet.create` 的准入链是三段：`is_operator(user_id)`（超管或在「运营」组）→ `RoleInputSerializer`（`name` / `model_config_id` / `kinds` / `system_prompt`）→ `api.can_select_model(user_id, model_config_id)`（查 `ModelUseGrant`）。

`RoleOutputSerializer` 的 `provider` / `api_key_env` / `model_name` / `base_url` / `api_protocol` 全部 `source="model_config.*"`，`kinds` 来自 `SerializerMethodField`；也就是说这五个字段**不可写**。

两个用例文件的失败正是这两点的两侧：

- `test_role_kinds.py` 已经改成新入参（`model_config_id` + `kinds`），但 `_config()` 走 ORM 直建配置，没有补 `ModelUseGrant`，卡在 `can_select_model` → 403「不能使用该模型」。
- `test_roles.py` 仍按 `model_name` 入参写，`RoleInputSerializer` 直接丢弃该字段，随后 `create` 的「名称与模型配置不能为空」或 `role_id` 取值失败。

## Goals / Non-Goals

**Goals:**

- 两个文件在 HEAD 上转绿，且断言的是**功能级可观察结果**（状态码、信封、库里记录），不是实现细节。
- 用例的建数据路径与生产路径的授权行为保持一致（新建模型即给超管发名单）。

**Non-Goals:**

- 不改 `can_select_model` 让超管绕过名单 —— 规格 `model-use-grant` 的「新模型默认只有超级管理员可用」是靠创建时自动发名单实现的，放宽校验会让「名单管理」失去意义。
- 不补 `kinds` 之外的字段级用例（已由 `test_role_kinds.py` 覆盖）。
- 不动 `test_model_grant.py`（它本来就通过 API 建配置，行为正确）。

## Decisions

1. **用例侧补 `ModelUseGrant`，不改生产。**
   依据：`api.create_model_config` 明确写了「给全部超管发名单」，这正是规格说的「新模型默认只有超级管理员可用」；用例用 ORM 造数据属于捷径，补一条 grant 就等于补齐生产那一跳。
   备选（否）：让 `can_select_model` 对超管直接返回 True —— 会让「运营新增配置后超管自动可用」的实现路径失效，且规格未授权该放宽。
2. **`test_roles.py` 整体按现契约重写，而不是逐条打补丁。**
   依据：8 条失败横跨 create / list / patch / delete，逐条改只会留下两套入参风格；重写后与 `test_role_kinds.py` 共用「配置 + 名单」的造数据范式。
3. **「任意 model_name 可接受」换成「不存在的 model_config_id 返回 400」。**
   依据：`model_name` 已不可写，原断言的对象不存在了；该位置该守的是「外键指向不存在的配置时给出 4xx 而不是 500」。
4. **每个功能一条用例的颗粒度不变**，不新增按分支拆的用例；`kinds` 的 6 条边界继续留在 `test_role_kinds.py`。

## Risks / Trade-offs

- [造数据与生产路径仍不完全等价] → 差异只在「谁发 grant」，断言的是角色 CRUD 行为，不依赖发 grant 的实现细节；后续若生产改成信号量发 grant，用例不受影响。
- [重写后覆盖变弱] → 保留原有 8 个断言语义（路由、401、201 全字段、倒序、局部更新、删除后 404、重名 409、空名 400），只替换已失效的两处入参断言。
- [与 `fix-assistant-log-report-id-404` 的关单门禁重叠] → 本变更完成后该门禁的「全组通过」才成立，两单按此顺序关。

## 模块防火墙自检

- 只动 `tests/**`，不新增跨 App import；用例经 `views_drf` 调用，与生产入口一致。
- 写库只经 ORM 造夹具，不绕过 View 的业务校验（校验仍在 View 内执行）。
- 不新增异常类、不改依赖方向、不碰钱与配额口径。
