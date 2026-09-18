## Why

🟠 **evaluator 写库未收敛到 `api.py`**（D3-2 写库收敛违规），实测 13 处，分两类：

**① view 层直接改 ORM 状态并落库（8 处）** —— `views.py` 与 `views_api.py` 的后台评测线程闭包 `_bg()` 里，直接 `run = EvalRun.objects.get(...)` → 改字段 → `run.save()`：

| 文件 | 行 | 场景 |
|---|---|---|
| `views.py` | 281 · 325 · 329 · 341 | legacy `runs/start` 后台线程：未知框架 / 跑完终态 / 异常 / 自评测异常 |
| `views_api.py` | 145 · 189 · 193 · 209 | DRF `runs/start/` 后台线程：同上四种 |

两处 `_bg()` 是**同一段逻辑的两份拷贝**，8 个写点都绕过了本 App 的 `api.py` 白名单（`apps/evaluator/api.py` 文件头即写明「View 调用 api.py 函数写 DB，禁止直接 ORM INSERT/UPDATE/DELETE」）。

**② Serializer 绕过已存在的 api 函数（5 处）** —— `QuestionBankSerializer.create/update` 直接 `QuestionBank.objects.create` / `Question.objects.create`（×2）/ `instance.questions.all().delete()`；而 `api.py` **已有** `create_question_bank` / `update_question_bank` 做同样的事 —— 等于同一操作两条写路径，且语义已漂移：

| 路径 | 更新时 `questions[].order` |
|---|---|
| legacy `POST /banks/{id}/update` → `api.update_question_bank` | **按数组下标重排**（文档 §6.5 明写） |
| DRF `PUT/PATCH /banks/{id}/` → `QuestionBankSerializer.update` | 取客户端 `order`，缺省才用下标 |

实测前端 `evaluator-api.ts` **只消费 legacy 平铺路径**（`/banks`、`/banks/create`、`/banks/{id}/update`、`/banks/seed`），DRF `/banks/` 无消费方 —— 故把 serializer 指向 api 是「让双路径行为一致」而非改前端可见行为（文档 §3.4 只写「`questions` 全量替换」，未规定更新时的 order 口径，与 §6.5 不冲突）。

> 说明：`api.py` 文件头已声明「评测引擎（`evaluator.py` 的 `run_evaluation`）运行时状态更新属 service 层内部编排，不在此收敛」；本单**不动** `evaluator.py`，只收敛 view 层与 serializer 层。

## What Changes

- `apps/evaluator/api.py`：新增两个写原语并登记 `__all__`
  - `mark_eval_run_failed(run_id, message)` —— 失败态落库（只写 `status` + `report_json`，与既有行为一致：**不写** `finished_at`）
  - `finish_external_eval_run(run_id, *, status, total_score, total_questions, completed_questions, report)` —— 外部框架终态落库（含 `finished_at`）
- `apps/evaluator/views.py` + `apps/evaluator/views_api.py`：8 处 `run.save()` 改为上述两个 api 调用；删除各处 `EvalRun.objects.get` + 字段赋值
- `apps/evaluator/serializers.py`：`QuestionBankSerializer.create/update` 改为调 `api.create_question_bank` / `api.update_question_bank`，随后按 id **只读**回取实例返回（写不再落 serializer）
- 新增 `tests/graybox/unit/test_evaluator_writes.py`：① 跑失败态 api → 库内 `status=failed` 且 `report_json` 含 message；② 终态 api → `status/total_score/completed_questions/report_json/finished_at` 全落库；③ serializer 建/改题库走 api 且**更新时 order 按数组下标重排**（双路径一致）
- **BREAKING**：无（前端只消费 legacy 路径，其行为不变；DRF `/banks/` 无消费方）
- 按 schema 约定设 `skip_specs: true`

## 关联文档

- 门禁：`django-backend-check/references/calibration.md` §2 🟠「写库在 views 但同 App 未抽 api（收敛违规）」· §6 api.py 契约硬规则 5「写操作校验与状态检查在 api 内完成」
- App 约束：`apps/evaluator/AGENTS.md`（信封双口径 · 评估后台任务失败须有 message/日志）· `apps/AGENTS.md` §1.2（View 只分发，写库走 api）
- 契约真相源：`dev_docs/05-开发与测试/接口文档/API-评估器.md` §3.4 / §6.5
- 前置变更：本会话 D3 复查（缺陷 D3-2 在 evaluator 的落点）

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

（无 —— 不改 Requirement 文本，故无 delta）

## Impact

- 源码：`apps/evaluator/api.py`（+2 函数 +2 import）· `views.py`（-8 写点）· `views_api.py`（-8 写点）· `serializers.py`（`create/update` 重写）
- 测试：新增 `tests/graybox/unit/test_evaluator_writes.py`
- 验证：`manage.py check` · `makemigrations --check`（无模型改动）· `ruff check .` / `ruff format --check .` · 新测试 + `tests/graybox/unit` 全量 · `--check-boundaries`
- 不在本单范围：`apps/evaluator/views.py` 与 `views_api.py` 的 **`_bg()` 逻辑重复**（两处拷贝）只收敛写点、不做大搬家；`engines/` 无关
