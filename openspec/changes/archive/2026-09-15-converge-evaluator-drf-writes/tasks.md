## 1. 复核（实测，已完成）

- [x] 1.1 打印 `EvalRunSerializer` / `EvalResultSerializer` 字段可写性：
      `agent_id` / `bank_id` / `question_id` **全是 `ReadOnlyField`**；
      `framework` / `status` / `judge_provider` / `judge_model` 可写
- [x] 1.2 打 HTTP 实测 `POST /api/evaluator/runs/ {"agent_id":1,"bank_id":1}` → **201**，响应体
      `"agent_id":null,"bank_id":null`，落库同为 NULL（`EvalRun.agent` / `bank` 可空 → 不报错，是假成功）
- [x] 1.3 打 HTTP 实测 `DELETE /api/evaluator/runs/1/`（run 确实存在）→ **404「未找到。」**，`EvalRun` 计数不变
- [x] 1.4 定位 1.3 根因：`EvalRunViewSet.get_queryset()` 在 `destroy` 下返回已切片查询集；
      `qs.get(pk=...)` 抛 `TypeError: Cannot filter a query once a slice has been taken.`；
      `rest_framework/generics.py:18-21` 的 `get_object_or_404` 捕获 `TypeError` → `raise Http404`
- [x] 1.5 spy 实测 `DELETE /api/evaluator/banks/{id}/` → 204、库中已删，
      但 `api.delete_question_bank` **零调用**（默认 `instance.delete()` 直写）
- [x] 1.6 确认 `EvalResultViewSet` 是 `ReadOnlyModelViewSet`：`question_id` 只读**不是**缺陷（无 create 路径）
- [x] 1.7 确认 `api.delete_question_bank` / `api.delete_eval_run` 已在 `__all__`
      且被 legacy `views.py:102,353` 调用 → 无需新增 api
- [x] 1.8 确认前端 `frontend/src/modules/ai-assistant/evaluator-api.ts` **只消费 legacy 平铺端点**，
      不消费任何 DRF router 端点 → 本单无前端行为变化

## 2. 修改

- [x] 2.1 `apps/evaluator/serializers.py`：`EvalRunSerializer` 增 `agent_id` / `bank_id` 显式
      `IntegerField(allow_null=True, required=False)`（+5 行；附注释说明为何不用 `PrimaryKeyRelatedField`）
- [x] 2.2 `apps/evaluator/views_api.py`：`EvalRunViewSet.get_queryset()` 按 `self.action` 分派，切片只给 `list`
- [x] 2.3 `apps/evaluator/views_api.py`：`EvalRunViewSet.perform_create()` 解析两 id（不存在 → `NotFound`）、
      调 `api.create_eval_run`、`serializer.instance` 只读回取
- [x] 2.4 `apps/evaluator/views_api.py`：`EvalRunViewSet.perform_destroy()` → `api.delete_eval_run`
- [x] 2.5 `apps/evaluator/views_api.py`：`QuestionBankViewSet.perform_destroy()` → `api.delete_question_bank`
- [x] 2.6 `dev_docs/05-开发与测试/接口文档/API-评估器.md`：§4.1 补切片作用范围；§4.2 补存在性语义 + 错误码表；
      §4.4 补交叉引用；§7 新增第 8 条登记 `results` 恒空（+19/-2）

## 3. 验证

- [x] 3.0 **修复前对照实测**：把 2.1～2.5 反向回退后跑新测试 → **7 failed / 7 passed**
      （失败的 7 条正是针对三处缺陷：DELETE run 恒 404、DELETE bank 未走 api、
      POST run 落 NULL / 不校验不存在的 id / 未走 api）
- [x] 3.1 `tests/graybox/unit/test_evaluator_drf_writes.py` 新增 **14 条，全绿**：
      ① `DELETE /runs/{id}/` 现 204 且落库消失；② 走 `api.delete_eval_run`（spy）；③ 不存在的 run 仍 404；
      ④ `DELETE /banks/{id}/` 走 `api.delete_question_bank`（spy）；⑤ `POST /runs/` 现落 `agent_id`/`bank_id`；
      ⑥ 缺省两 id 允许落 NULL；⑦ 登记的缺省值不变；⑧⑨ 不存在的 agent/bank → 404 且不落库；
      ⑩ `POST /runs/` 走 `api.create_eval_run`（spy）；⑪ `list` 仍最多 50 条；⑫ `retrieve` 仍带详情字段；
      ⑬ `EvalResultViewSet` 仍是只读基类；⑭ 源码无 `serializer.save()` / `instance.delete()` / `.objects.create(`
- [x] 3.2 `python manage.py check` → System check identified no issues (0 silenced)；
      `python manage.py makemigrations --check --dry-run` → No changes detected
- [x] 3.3 `python -m ruff check .` → All checks passed!；
      `python -m ruff format --check apps/ config/ gateway/ shared/ models/ tests/` → 216 files already formatted
- [x] 3.4 `pytest tests/graybox/unit tests/arch -q` → **185 passed**（改动前 171，+14 即本单新测试）；
      `pytest tests/graybox/integration -q` → 16 passed
- [x] 3.5 `python tools/gen_arch_stats.py --check-boundaries` → 零违规
- [x] 3.6 收敛实测：对 `apps/evaluator/views.py` + `views_api.py` 跑 §7 直写扫描
      （`.objects.create|.save(|.delete(|.update(`）→ **零命中**
      （正对照：同一正则扫 `api.py` 命中 14 处 → 正则本身有效）

## 4. 发现的坑与新增缺陷（不在本单修复）

1. **DRF 把内部错误伪装成业务错误（本会话第三次踩）**：`rest_framework/generics.py:18-21` 的
   `get_object_or_404` 捕获 `(TypeError, ValueError, ValidationError)` 并 `raise Http404` ——
   于是「查询集写错」这类内部缺陷**永远不会 500，只会静默变成「未找到。」**。
   本单的 `DELETE /runs/{id}/` 恒 404 就是这条：切片查询集的 `TypeError` 被吞成 404。
   启示：**看到 404 不要只怀疑「对象不存在」，要同时怀疑查询集本身是坏的。**
2. **DRF 的 FK `*_id` 只读陷阱第三次**（workflow `parent_id` · element_locator 3 个 FK · evaluator `agent_id`/`bank_id`）。
   前两次后果是 500，这次是 **201 + 字段静默为 NULL**：HTTP 码与信封都「正常」，
   唯一线索是响应体里的 `null`。**假成功比 500 更难发现。**
3. **`GET /runs/{id}/` 的 `results` 恒为空数组**（实测：DB 有 2 条 `EvalResult`，响应 `"results": []`）：
   `EvalRunSerializer.get_results` 读 `obj._prefetched_results`，而该属性**全仓无写入点**
   （仅 `serializers.py:98,100` 两处引用）→ `get_queryset` 的 `prefetch_related("results__question")` 是死代码，
   `API-评估器.md` §4.3 的示例与实现不符。**未修**：`results` 的取数口径（改用 `obj.results.all()`？保留预取协议？）
   需要先定夺，属「面对模糊不清拒绝猜测」。已登记进 §7 第 8 条。
4. **扫描工具会误报**：`EvalResultSerializer.question_id` 只读**不是**缺陷 ——
   `EvalResultViewSet` 是 `ReadOnlyModelViewSet`，根本没有 create 路径。
   「只读 `*_id`」必须结合「该 ViewSet 有没有写路径」判定。

## 5. 归档

- [x] 5.1 记录 diff 范围：`apps/evaluator/serializers.py` 171→176 行（+5）；
      `apps/evaluator/views_api.py` 218→262 行（+44）；
      `dev_docs/…/API-评估器.md` +19/-2；新增 `tests/graybox/unit/test_evaluator_drf_writes.py` 218 行
- [x] 5.2 注：工作树累积多个未提交变更，`git diff --numstat` **无法区分本单**
      （`evaluator/api.py` 的 37/0 与 `views.py` 的 10/26 属前一单 `converge-evaluator-writes`）；
      `openspec/` 被 `.gitignore` 排除 → 回滚 = `git checkout` 源文件 + 删测试 + 手改文档
- [ ] 5.3 `openspec archive converge-evaluator-drf-writes -y --json`

## 6. 续做（不在本单）

- `api.create_eval_run(agent, bank, ...)` 收 ORM 实例做参数（calibration §6 规则 5 偏差）—— 需连同 legacy `views.py` 一起改
- `GET /runs/{id}/` 的 `results` 取数口径（见 §4 第 3 条）
- `element_locator/views_projects_drf.py` 的 `LocatorProjectViewSet` / `LocatorDirectoryViewSet` 隐式写（③-2）
- `case_manager/views_drf.py` · `workflow/views_api.py` 遗留 · `ai_assistant/views_drf.py` 的隐式写（③-3）
