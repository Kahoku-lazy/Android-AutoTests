## 1. 表与生成规则

- [x] 1.1 在 `backend/apps/ai_assistant/models.py` 新增 `AIRole`：`role_id`（`CharField(11, unique=True)`）、`name`（`CharField(200, unique=True)`）、`model_name`（`CharField(200)`）、`system_prompt`（`TextField(blank=True, default="")`）、`created_at`、`updated_at`，`db_table = "ai_roles"`；验证方式：`python -c "from backend.apps.ai_assistant.models import AIRole; print([f.name for f in AIRole._meta.fields])"` 输出含六个字段且无 `ai_agents` 字段。
- [x] 1.2 新建 `backend/apps/ai_assistant/role_id.py`，实现 `generate_role_id()`（`localtime` 日期 + `secrets.choice` 3 位 `[0-9a-z]`）与 `generate_unique_role_id()`（查重重试，上限 8 次）；验证方式：单元测试断言格式 `^\d{8}[0-9a-z]{3}$`、连续 500 次生成互不相同、已占用的标识会被跳过。
- [x] 1.3 生成迁移 `0066_airole.py`（只 `CreateModel`，`name` 列显式 `utf8mb4_bin` 排序规则），验证方式：`python manage.py makemigrations --check --dry-run` 无待生成变更，`python manage.py migrate ai_assistant` 成功建表。

## 2. 写库层（api.py）

- [x] 2.1 新增 `create_role(name, model_name, system_prompt="")`：生成 `role_id`，落库，`IntegrityError` 重试一次后转成明确的冲突错误；验证方式：单元测试覆盖「正常创建」「名称重复」「标识撞车后重试成功」三条路径。
- [x] 2.2 新增 `update_role(role, data)`：只改提交字段，名称变更前排除自身查重；验证方式：单元测试断言名称不变时可通过、改成他人名称时抛冲突。
- [x] 2.3 新增 `delete_role(role)`、`list_roles()`（`-created_at` 排序）、`get_role(role_id)`（不存在返回 `None`）；验证方式：单元测试断言列表顺序与未知标识返回 `None`。

## 3. 校验层与视图层

- [x] 3.1 在 `serializers.py` 新增 `RoleInputSerializer`（`name` 去空白后非空、`model_name` 非空且 ≤200、`system_prompt` 允许空）与 `RoleOutputSerializer`（六个下发字段，时间 ISO）；验证方式：单元测试覆盖空名称、全空白名称、超长模型名、空提示词四种输入。
- [x] 3.2 在 `views_drf.py` 新增 `RoleViewSet(ModelViewSet)`，`lookup_field = "role_id"`，覆写 `create`（201 + 信封）、`destroy`（200 + `{role_id}`）、`list` / `retrieve` / `update` / `partial_update` 全部包 `{status, data}`；验证方式：接口测试断言五个方法的状态码与信封形状。
- [x] 3.3 在 `urls.py` 的 `router` 注册 `roles`；验证方式：`python manage.py check` 通过，且 `resolve("/api/ai/roles/")` 与 `resolve("/api/ai/roles/20261115a3f/")` 均命中 `RoleViewSet`，不带尾斜杠的 `/api/ai/roles` 返回 404。
- [x] 3.4 在 `admin.py` 注册 `AIRole`（列表显示 `role_id` / `name` / `model_name` / `created_at`）；验证方式：`/admin/` 能打开该表列表页（`python manage.py check` 无 admin 报错）。

## 4. 接口与单元测试

- [x] 4.1 新增 `tests/ai_assistant/unit/test_role_registry.py`：ID 格式与唯一性、名称重复、部分更新、未知标识、排序；验证方式：`python -m pytest tests/ai_assistant/unit/test_role_registry.py -q` 全绿。
- [x] 4.2 新增 `tests/ai_assistant/api/test_roles.py`：五个方法的状态码、信封形状、字段集合、401 未登录、404 未知标识、409 重名、400 空字段；验证方式：`python -m pytest tests/ai_assistant/api/test_roles.py -q` 全绿。
- [x] 4.3 确认既有测试未被影响：`python -m pytest tests/ai_assistant -q` 与 `python -m pytest tests/arch/unit/test_api_path_callers.py -q` 全绿（新增路由的调用方即测试自身，路径须带尾斜杠）。

## 5. 边界自检与收尾

- [x] 5.1 自检「模型不对外」边界：确认本次未新增任何模型清单/取值接口；验证方式：`grep -rn "models.yaml\|load_models" backend/apps/ai_assistant/` 无命中。
- [x] 5.2 自检「提示词不旁路」边界：确认本次未读写 `engines/ae_harness/agents/config/prompts/` 也未改 `create_agent`；验证方式：`git diff --stat -- engines/` 为空。
- [x] 5.3 跑本地门禁：`python run.py check` 与 `python manage.py makemigrations --check --dry-run`；验证方式：退出码 0。
- [x] 5.4 用真机环境起服务做一次冒烟：`POST /api/ai/roles/` 建一条、`GET` 列表、`PATCH` 改名、`DELETE` 删除；验证方式：四步返回码与信封符合 spec，删除后详情 404。
- [x] 5.5 `openspec validate ai-role-registry --strict` 通过；验证方式：命令退出码 0。
