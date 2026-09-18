## Why

🟠 **element_locator 的 DRF 写路径：越过 api 白名单 + 契约未兑现（含一处必现 500）**（D3）。

实测（2026-09-15，`serializer.fields` 打印 + 代码阅读）：

**① `WebPageFlowViewSet.perform_create` 必现 500。** `WebPageFlowSerializer` 的
`from_group_id` / `to_group_id` / `trigger_element_id` **全是 `ReadOnlyField`**（DRF 对 FK 的 `*_id` attname 一律建成只读），
于是 `serializer.validated_data` 只含 `trigger_action`；`serializer.save()` → `WebPageFlow.objects.create(trigger_action=...)`
→ `from_group_id` NOT NULL 违约 → **IntegrityError → 500**。
同函数里的「源/目标不能是目录」校验取 `validated_data.get("from_group")`，永远拿到 `None` → **校验是死代码**。
（与 `fix-workflow-directory-update-atomicity` 的 `parent_id` 只读是同一模式。）

**② `WebElementViewSet.perform_update` 直写库。** `serializer.save()` 越过 `api.py`（D3 契约「写库只经 api.py」）；
其上方三个局部变量 `allowed` / `actual` / `extra` **从未被使用**（且引用的 `alias` / `notes` 字段在 Serializer 上并不存在）——死代码。

## What Changes

- `serializers.py`：`WebPageFlowSerializer` 的 `from_group_id` / `to_group_id` 改为可写 `IntegerField`，
  `trigger_element_id` 改为可写 `IntegerField(allow_null=True, required=False)`（兑现文档 §web-flows 契约：int id / 可空）
- `views_drf.py`：
  - `WebPageFlowViewSet.perform_create`：改为**单一 api 写路径** —— 先校验源/目标是否为目录（现在真能取到），再调 `api.create_web_page_flow(...)`，成功后 `serializer.instance = WebPageFlow.objects.get(id=result["id"])`；删 `serializer.save()`
  - `WebElementViewSet.perform_update`：改为调 `api.update_web_element(instance.id, validated_data)` + 只读回取 `serializer.instance`；删 3 个死局部变量
- `api.py`：`create_web_page_flow` 返回 `{"id": flow.id}`（§6 规则 4：api 不返回 ORM）；调用方 `views_flows.web_flows_handler` **本就忽略返回值**，无需改动
- 新增 `tests/graybox/unit/test_element_locator_drf_writes.py`：① POST `/api/elements/web-flows/` 成功落库（修复前为 500）；
  ② 源/目标为目录 → 400（校验由死代码变为可达）；③ spy 断言 web 元素 PATCH 走 `api.update_web_element`；
  ④ POST `/api/elements/web-flows/` 走 `api.create_web_page_flow`

- **BREAKING**：无（web-flows create 从 500 变为按契约工作；字段类型仍是 int id）
- 按 schema 约定设 `skip_specs: true`

## 关联文档

- 契约真相源：`dev_docs/05-开发与测试/接口文档/API-元素定位.md` · `apps/element_locator/AGENTS.md`
- 前置变更：`split-element-locator-views` · `remove-dead-element-locator-group-writes`（同文件域）
- 门禁：`django-backend-check/references/calibration.md` §2（🔴 假成功/契约错误）· §6 api 契约 · §7

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

（无 —— 不改 Requirement 文本，故无 delta）

## Impact

- 源码：`serializers.py`（3 字段可写）· `views_drf.py`（2 处 `perform_*` 重写）· `api.py`（`create_web_page_flow` 返回 dict）
- 测试：新增 `tests/graybox/unit/test_element_locator_drf_writes.py`
- 验证：`manage.py check` · `makemigrations --check` · `ruff` · 全量 unit/arch/integration · `--check-boundaries`
- 不在本单范围：`views_projects_drf.py` 的 ViewSet 隐式写 · `api.py` 其余写函数返回 ORM（另单）
