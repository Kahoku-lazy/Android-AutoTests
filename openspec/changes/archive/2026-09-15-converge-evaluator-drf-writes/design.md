## Context

evaluator 的写库收敛（`converge-evaluator-writes`）只处理了 `views.py`（legacy）与 `QuestionBankSerializer`，
`views_api.py` 的 ViewSet 层留有 3 处隐式写。本次排查又发现其中 2 处对应的**已登记端点在实现上是坏的**：
`DELETE /runs/{id}/` 恒 404，`POST /runs/` 静默丢 `agent_id` / `bank_id`。

前置事实（实测，见 proposal.md「Why」）：

- `EvalRunViewSet.get_queryset()` 在 `destroy` 下返回已切片查询集 → DRF `get_object_or_404` 把 `TypeError` 转成 404。
- `EvalRunSerializer.agent_id / bank_id` 是 `ReadOnlyField`（DRF 对 FK `*_id` attname 的默认行为）。
- `api.delete_question_bank` / `api.delete_eval_run` 已存在、已在 `__all__`、已被 legacy 调用。

## Goals / Non-Goals

**Goals:**

- `views_api.py` 的 ViewSet 不再有任何直写 ORM 的调用（`serializer.save()` / `instance.delete()`）
- `DELETE /api/evaluator/runs/{id}/` 与 `POST /api/evaluator/runs/` 按 `API-评估器.md` 登记行为工作

**Non-Goals:**

- 不动 legacy 平铺路径（它们本就直调 api）
- 不动 `api.create_eval_run` 的签名（收 ORM 实例做参数，§6 规则 5 的既有偏差，见「Open Questions」）
- 不动 `EvalResultViewSet`（`ReadOnlyModelViewSet`，无写路径；`submit_score` 已走 api）
- 不动前端（`evaluator-api.ts` 只消费 legacy 平铺端点，本单不涉）

## Decisions

### 1. 切片只用于 `list`，而不是覆写 `get_object`

- **选择**：`get_queryset()` 按 `self.action` 分派 —— `list` 返回 `...order_by("-created_at")[:50]`；
  `retrieve` 返回 `prefetch_related("results__question")`；其余动作（`destroy`）返回未切片的 `qs`。
- **理由**：`[:50]` 是 `list` 的展示上限（§4.1 登记），不是数据可见性边界。
  在 `get_queryset` 里给所有动作加切片，等于让详情动作无法按 pk 过滤。
- **备选**：覆写 `get_object()` 绕开切片 —— 否决，它把「查询集是错的」这个事实藏起来，
  且 `filter_queryset` / `check_object_permissions` 仍基于坏查询集。

### 2. `agent_id` / `bank_id` 用裸 `IntegerField` 而非 `PrimaryKeyRelatedField`

- **选择**：`IntegerField(allow_null=True, required=False)`。
- **理由**：与 `fix-workflow-directory-update-atomicity` / `converge-element-locator-drf-writes` 同一裁决 ——
  文档登记的是裸 id；用 `PrimaryKeyRelatedField` 会把存在性校验前移到 DRF 并产生技术化文案，
  且 `validated_data` 拿到的是对象而非 id。
- **代价**：不存在的 id 不在这层拦（由 `perform_create` 显式判，见决策 3）。

### 3. 存在性校验在视图、写库在 api

- **选择**：`perform_create` 里取 `AIAgent` / `QuestionBank` 实例；不存在则 raise
  `NotFound("agent not found")` / `NotFound("question bank not found")`（与同一 ViewSet 的 `start` 动作文案逐字一致），
  再调 `api.create_eval_run(...)`。
- **理由**：这是**入参校验**（apps/AGENTS.md：serializer/view 管校验）、且是读操作；写归 api。
  `perform_create` 没有返回通道，故用 DRF 异常而非 `Response`。

### 4. `perform_destroy` 调既有 api 函数，不新增 api

- **选择**：`api.delete_question_bank(instance.id)` / `api.delete_eval_run(instance.id)`。
- **理由**：两个函数已存在且已在 `__all__`，行为一致（`filter(id=...).delete()`，幂等）。
  **不**新增 api 函数，避免同一语义两条实现。

## Risks / Trade-offs

- [`DELETE /runs/{id}/` 由 404 → 204] → 这是恢复登记契约。前端 `evaluator-api.ts` 走 legacy
  `POST /runs/{id}/delete`，不消费该 DRF 端点 → **无前端行为变化**；已核对 `frontend/src/modules/ai-assistant/evaluator-api.ts`。
- [`POST /runs/` 开始真的落 `agent`/`bank`] → 同上，前端不消费；仅使登记契约成真。
- [切片按动作分派] → `list` 行为逐字不变（仍最多 50 条）；`retrieve` 分支原样保留。
- [裸 `IntegerField` 不做 FK 类型校验] → 传非整数由 DRF 给 400；传不存在的 id 由 `perform_create` 给 404。

## Migration Plan

1. 改 `EvalRunSerializer` 两字段；改 `EvalRunViewSet.get_queryset`；加两个 `perform_create` / `perform_destroy`；
   加 `QuestionBankViewSet.perform_destroy`
2. 新增 `tests/graybox/unit/test_evaluator_drf_writes.py`（含「修复前 404 / 修复前字段为 null」对照）
3. 更新 `API-评估器.md` §4.2 / §4.4
4. 验证 `manage.py check` · `makemigrations --check` · ruff · 全量 unit/arch/integration · `--check-boundaries`
5. 归档；回滚 = `git checkout` 两源文件 + 文档 + 删测试（`openspec/` 被 `.gitignore` 排除，不靠 git 回滚）

## Open Questions

- `api.create_eval_run(agent, bank, ...)` 收 ORM 实例做参数，与 `calibration.md` §6 规则 5
  「写操作校验与状态检查在 api 内完成」有偏差（其 docstring 自述「agent/bank 由调用方预取并校验存在」）。
  本单**不改**：`converge-evaluator-writes` 已归档该签名，且两个调用方都需要 ORM 实例驱动后台线程；
  改签名会连带改 `views.py` legacy 路径，超出「收敛隐式写」范围。登记为 ③ 续做项。
