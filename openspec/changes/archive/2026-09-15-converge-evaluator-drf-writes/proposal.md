## Why

🟠 **evaluator 的 DRF 写路径：3 处隐式写越过 api.py；其中 2 个已登记端点实际不工作**（D3）。

实测（2026-09-15，HTTP 打端点 + 打印 `serializer.fields`，探针见归档 tasks §1）：

**① `DELETE /api/evaluator/runs/{id}/` 恒 404，删除从未生效。**
`EvalRunViewSet.get_queryset()` 对非 `retrieve` 动作返回**已切片**查询集 `...order_by("-created_at")[:50]`，
`destroy` 经 `get_object()` → `qs.get(pk=...)` 抛 `TypeError: Cannot filter a query once a slice has been taken.`；
DRF 的 `get_object_or_404` 把 `TypeError` 吞成 `Http404`（`rest_framework/generics.py:18-21`）→ **404「未找到。」**。
实测：建 1 条 run → `DELETE /runs/1/` → 404，`EvalRun` 计数仍为 1。
而 `API-评估器.md` §4.4 登记的是 **204 / 级联删除逐题结果** —— 登记契约与实现相反。

**② `POST /api/evaluator/runs/` 201 成功但静默丢弃登记的字段。**
`EvalRunSerializer` 的 `agent_id` / `bank_id` 是 `ReadOnlyField`（DRF 对 FK 的 `*_id` attname 一律建成只读），
而 `API-评估器.md` §4.2 把这两个字段登记为「可写字段」。
实测：`POST /runs/ {"agent_id": 1, "bank_id": 1}` → **201**，响应体 `"agent_id": null, "bank_id": null`，落库同为 NULL。
（`EvalRun.agent` / `bank` 可空，故不报错 —— 是「假成功」而非 500，比 500 更隐蔽。）

**③ 两处 `destroy` 用 DRF 默认 `instance.delete()` 直写库。**
`QuestionBankViewSet` / `EvalRunViewSet` 均未覆写 `perform_destroy` → 越过 `api.py`（D3 契约「写库只经 api.py」）；
而 `api.delete_question_bank` / `api.delete_eval_run` **已存在**且 legacy 路径正在用（`views.py:102,353`）。
实测：`DELETE /banks/{id}/` → 204、库中已删，但 `api.delete_question_bank` **零调用**（monkeypatch spy）。

## What Changes

- `serializers.py`：`EvalRunSerializer` 的 `agent_id` / `bank_id` 改为可写
  `IntegerField(allow_null=True, required=False)`（兑现 §4.2 登记的「可写字段，均非必填」）
- `views_api.py`：
  - `EvalRunViewSet.get_queryset()`：**切片只用于 `list`**；`retrieve` / `destroy` 返回未切片查询集（修 404 根因）
  - `EvalRunViewSet.perform_create()`：解析 `agent_id` / `bank_id`（不存在 → 404，与 `start` 动作同文案），
    再调 `api.create_eval_run(...)`，`serializer.instance` 只读回取 —— 删除隐式 `serializer.save()`
  - `EvalRunViewSet.perform_destroy()` → `api.delete_eval_run(instance.id)`
  - `QuestionBankViewSet.perform_destroy()` → `api.delete_question_bank(instance.id)`
- `dev_docs/05-开发与测试/接口文档/API-评估器.md`：§4.2 补 `agent_id`/`bank_id` 的存在性校验与错误码；§4.4 补删除语义说明
- 新增 `tests/graybox/unit/test_evaluator_drf_writes.py`

- **BREAKING**：无（`DELETE /runs/{id}/` 由恒 404 → 204 是修 bug；`POST /runs/` 由静默丢字段 → 按登记契约落库）
- 按 schema 约定设 `skip_specs: true`（不改 Requirement 文本）

## 关联文档

- 契约真相源：`dev_docs/05-开发与测试/接口文档/API-评估器.md` · `apps/evaluator/AGENTS.md`
- 前置变更：`converge-evaluator-writes`（同 App，写库已收敛到 api.py；本单收它的漏网 ViewSet）
- 同模式先例：`fix-workflow-directory-update-atomicity` · `converge-element-locator-drf-writes`（DRF `*_id` 只读陷阱）
- 门禁：`django-backend-check/references/calibration.md` §2（🔴 假成功/契约错误 · 🟠 写库未抽 api）· §6 · §7

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

（无 —— 不改 Requirement 文本，故无 delta）

## Impact

- 源码：`apps/evaluator/serializers.py` · `apps/evaluator/views_api.py`
- 文档：`dev_docs/05-开发与测试/接口文档/API-评估器.md`
- 测试：新增 `tests/graybox/unit/test_evaluator_drf_writes.py`
- 验证：`manage.py check` · `makemigrations --check` · `ruff` · 全量 unit/arch/integration · `--check-boundaries`
- 不在本单范围：`api.create_eval_run` 收 ORM 实例做参数（§6 规则 5「校验在 api 内」，另单）·
  `GET /runs/{id}/` 的 `results` 恒空数组（`obj._prefetched_results` 全仓无写入点，取数口径待定夺；已登记 `API-评估器.md` §7.8）·
  `element_locator/views_projects_drf.py` · `case_manager` · `workflow` · `ai_assistant/views_drf.py` 的隐式写（③-2/③-3）
