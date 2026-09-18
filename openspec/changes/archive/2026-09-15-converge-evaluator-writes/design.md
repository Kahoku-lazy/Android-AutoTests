## Context

evaluator 的写库有 13 处绕过 `api.py`：8 处在 view 层的后台线程闭包，5 处在 serializer。两处 `_bg()` 是同一逻辑的拷贝，写点分布其间。

## Goals / Non-Goals

**Goals:**

- evaluator 的 view 层与 serializer 层不再直接 INSERT/UPDATE/DELETE，写全部经 `api.py` 白名单
- 让 legacy 与 DRF 两条题库写路径行为一致（`order` 口径统一）

**Non-Goals:**

- 不合并 `views.py` / `views_api.py` 的重复 `_bg()`（`apps/AGENTS.md` 明列「无行为变化的大搬家」属默认拒绝的重构；本单只收敛写点）
- 不动 `apps/evaluator/evaluator.py`（`api.py` 文件头已登记其为 service 层内部编排）
- 不改模型 / 迁移 / 前端

## Decisions

### 1. 新增两个**语义化**写原语，而不是暴露「随便存」

- **选择**：`mark_eval_run_failed` 与 `finish_external_eval_run`
- **理由**：原代码是「取实例 → 改 4~6 个字段 → save」。若给 api 一个裸 `save_run(run)` 会收 ORM 实例（违反「api 不收 Model / 返回可 JSON 化」的精神）；按**业务终态**命名则参数是简单类型，校验与字段组合留在 api 内

### 2. 严格保留「失败态不写 finished_at」的既有行为

- **选择**：`mark_eval_run_failed` 只写 `status` + `report_json`；`finished_at` 仅由 `finish_external_eval_run` 写
- **理由**：实测原 4 个失败分支都没有设 `finished_at`（只有外部框架正常跑完那条设了）。顺手「补全」会改变前端轮询看到的数据，属行为变更

### 3. serializer 指向既有 api 函数（而非给 api 加新函数）

- **选择**：`QuestionBankSerializer.create/update` 调 `api.create_question_bank` / `api.update_question_bank`
- **理由**：这两个函数**已存在且已被 legacy 路径使用**；serializer 侧是同功能第二实现。指向它即消除双实现，并把 DRF 更新时的 `order` 口径对齐到文档 §6.5 的「按数组下标重排」

### 4. 写完后按 id 只读回取实例

- **选择**：`return QuestionBank.objects.get(id=result["id"])`
- **理由**：api 不返回 ORM（§6 规则 4），DRF 又要用 `serializer.instance` 拼响应；**读**不受收敛约束，与上一变更 `fix-workflow-directory-update-atomicity` 的处理方式一致

## Risks / Trade-offs

- [DRF 更新时 order 语义变化] → 实测前端只走 legacy 路径，DRF `/banks/` 无消费方；文档 §3.4 未规定更新 order，与 §6.5 不冲突。风险记为「无消费方 + 双路径趋同」
- [后台线程异常路径] → 写原语内部 `EvalRun.objects.get` 若抛 `DoesNotExist`，与改动前一样冒泡到线程；不做额外兜底（不引入新行为）
- [api 收简单类型] → 两个新函数参数均为 int/str/float/dict，符合 §6 规则 2/4

## Migration Plan

1. `api.py` 加 2 函数 + `__all__`；`serializers.py` 指向既有 api；`views.py` / `views_api.py` 8 处替换
2. 新增单测；`makemigrations --check` 必须仍绿（无模型改动）
3. 验证 `manage.py check` · `ruff check .` · `pytest tests/graybox/unit -q` · `--check-boundaries`
4. 归档；回滚 = `git checkout` 这 4 个文件 + 删新测试
