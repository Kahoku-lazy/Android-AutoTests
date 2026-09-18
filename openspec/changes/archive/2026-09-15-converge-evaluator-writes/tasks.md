## 1. 复核（已完成）

- [x] 1.1 全仓扫描 views/serializers/apps/consumers 的 ORM 写：evaluator 13 处（views 4 · views_api 4 · serializers 5）· element_locator 2 · ai_assistant 1
- [x] 1.2 确认 evaluator `api.py` 文件头已声明「View 调用 api.py 写 DB，禁止直接 ORM」，且 `run_evaluation` 属豁免的 service 层
- [x] 1.3 确认 `api.create_question_bank` / `update_question_bank` **已存在**且已被 legacy `views.py:79,93` 使用 —— serializer 侧是同功能第二实现
- [x] 1.4 确认 `order` 口径漂移：legacy/api 按数组下标（文档 §6.5 明写）vs serializer 取客户端 order（文档 §3.4 未规定，故不冲突）
- [x] 1.5 确认前端 `evaluator-api.ts` 只消费 legacy 平铺路径，DRF `/banks/` 无消费方（对齐口径不改前端可见行为）
- [x] 1.6 实测原失败分支均**不写** `finished_at`（仅外部框架正常跑完那条写）—— 收敛时按此保留

## 2. 修改

- [x] 2.1 `apps/evaluator/api.py`：加 `mark_eval_run_failed` / `finish_external_eval_run` + 登记 `__all__`（+2 import）
- [x] 2.2 `apps/evaluator/views.py`：external / self 两个 `_bg()` 的 4 处写点改 api 调用
- [x] 2.3 `apps/evaluator/views_api.py`：`_start_external_framework` / `_start_self_evaluator` 的 4 处写点改 api 调用；顺带删除因此变为未使用的 `import json`（F401）
- [x] 2.4 `apps/evaluator/serializers.py`：`create/update` 改调 `api.create_question_bank` / `api.update_question_bank` + 按 id 只读回取
- [x] 2.5 新增 `tests/graybox/unit/test_evaluator_writes.py`（4 条：失败态 / 终态 / create 走 api（spy）/ update 走 api 且 order 按下标）

## 3. 验证

- [x] 3.1 `python manage.py check` → 0 issues；`makemigrations --check --dry-run` → `No changes detected`
- [x] 3.2 `python -m ruff check .` → **All checks passed!**；`ruff format --check .` → **244 files already formatted**
- [x] 3.3 新测试 **4 passed**；`pytest tests/graybox/unit tests/arch -q` → **92 passed**（改动前 88 + 新增 4）
- [x] 3.4 复扫 `apps/evaluator` 的 `views*.py` / `serializers*.py` → ORM 写**零命中**（残留 `.objects.get()` 均为读）
- [x] 3.5 `python tools/gen_arch_stats.py --check-boundaries` → 零违规；范围核对 `git diff --numstat` = api.py 37/0 · serializers.py 17/22 · views.py 10/26 · views_api.py 10/27 · 新增测试 108 行

## 4. 剩余（后续变更）

- `apps/element_locator/views_drf.py` 2 处 `serializer.save()`（另有 `perform_update` 内 `allowed`/`actual`/`extra` 三个**未被使用**的局部变量，属 F841 类死代码 —— ruff 当前未选该规则）
- `apps/ai_assistant/apps.py:47` 1 处 `AITask.objects.filter(...).update(...)`（启动恢复扫描）
- `apps/evaluator/views.py` 与 `views_api.py` 的 `_bg()` 逻辑重复未合并（`apps/AGENTS.md` 默认拒绝无行为变化的大搬家）
