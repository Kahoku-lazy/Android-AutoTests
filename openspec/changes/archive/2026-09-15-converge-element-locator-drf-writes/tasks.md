## 1. 复核（已完成）

- [x] 1.1 打印两 Serializer 字段可写性：`WebElementSerializer.group_id` 只读（`api.update_web_element` 不依赖它）；`WebPageFlowSerializer` 的 `from_group_id` / `to_group_id` / `trigger_element_id` **全只读**
- [x] 1.2 推出 `POST /web-flows/` 必现 500：`validated_data` 只含 `trigger_action` → `create()` 缺 `from_group` → NOT NULL 违约
- [x] 1.3 确认目录校验取 `validated_data.get("from_group")` 恒 None → 死代码
- [x] 1.4 确认 `perform_update` 的 `allowed`/`actual`/`extra` 三局部变量从未使用，且引用的 `alias`/`notes` 字段不存在
- [x] 1.5 确认 `api.create_web_page_flow` 唯一调用方 `views_flows.web_flows_handler` 忽略返回值 → 改返回 dict 零适配

## 2. 修改

- [x] 2.1 `serializers.py`：`from_group_id` / `to_group_id` → `IntegerField()`；`trigger_element_id` → `IntegerField(allow_null=True, required=False)`（附注释说明为何不用 `PrimaryKeyRelatedField`）
- [x] 2.2 `views_drf.py`：`WebPageFlowViewSet.perform_create` → 先取 `WebGroup` 实例判目录（校验变可达），再调 `api.create_web_page_flow`，`serializer.instance` 回取；删 `serializer.save()`
- [x] 2.3 `views_drf.py`：`WebElementViewSet.perform_update` → `api.update_web_element(instance.id, validated_data)` + 回取；删 3 个死局部变量
- [x] 2.4 `api.py`：`create_web_page_flow` 返回 `{"id": flow.id}`（§6 规则 4）
- [x] 2.5 新增 `tests/graybox/unit/test_element_locator_drf_writes.py`（5 条）

## 3. 验证

- [x] 3.1 `python manage.py check` → 0 issues；`makemigrations --check` → `No changes detected`
- [x] 3.2 `python -m ruff check .` → **All checks passed!**；`ruff format` 已跑
- [x] 3.3 新测试 **5 passed**（含「修复前 500 的对照」：create 现 201 并落库；目录端点现 400）
- [x] 3.4 spy 断言：`POST /web-flows/` 走 `api.create_web_page_flow`；`PATCH /web/{id}/` 走 `api.update_web_element`；`views_drf.py` 源码无 `serializer.save()`
- [x] 3.5 `pytest tests/graybox/unit tests/arch -q` → 全绿；`tests/graybox/integration -q` → 16 passed；`--check-boundaries` → 零违规

## 4. 顺带修掉的一个必现 500

`POST /api/elements/web-flows/` **修复前必现 500**（Serializer 的 3 个 FK 字段全只读 → `create()` 缺非空 FK）。
这与 `fix-workflow-directory-update-atomicity` 的 `parent_id` 只读是**完全同一模式**：DRF 把 FK 的 `*_id` attname 建成 `ReadOnlyField`。
修法也一致：改成裸 `IntegerField`，把存在性/业务校验留给 view 与 api.py。

## 5. 续做

- `views_projects_drf.py` 的 `LocatorProjectViewSet` / `LocatorDirectoryViewSet` 仍用 DRF 默认 `perform_create`/`perform_update`（隐式写）
- `api.py` 其余写函数仍返回 ORM（`create_page` / `create_page_manually` / `upsert_element` / `update_element` / `create_flow` / `get_or_create_flow` / `create_web_element` / `update_web_element` / `create_api_endpoint` / `update_api_endpoint`）—— 约定 §6 规则 4，需与各自的 legacy 消费方一起改
- 其余 App 的 ViewSet 隐式写（`case_manager` 4 · `evaluator` 3 · `ai_assistant/views_drf` 1）
