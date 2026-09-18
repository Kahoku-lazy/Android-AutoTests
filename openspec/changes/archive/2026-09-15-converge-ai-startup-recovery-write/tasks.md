## 1. 复核（已完成）

- [x] 1.1 定位目标：`apps/ai_assistant/apps.py` 的 `_run_startup_recovery` 内 `AITask.objects.filter(...).update(...)` 是本模块最后一处绕过 `api.py` 的写
- [x] 1.2 确认同模块同类写已在 api：`start_task` / `finalize_task` / `patch_task_progress` / `delete_task` / `clear_agent_tasks` 均在 `api.py` 且登记 `__all__`
- [x] 1.3 确认 `api.py` 已具备所需依赖：`timezone`（line 17）· `AITask`（line 20-28）· `TaskStatus`（round 13 引入）
- [x] 1.4 确认 `api.py` 的 `__all__` 有「任务操作」分段，新函数登记其中
- [x] 1.5 确认全仓既有测试**未覆盖**启动恢复（`grep recover_orphaned|_run_startup_recovery` 在 `tests/` 零命中）→ 本单补上

## 2. 修改

- [x] 2.1 `apps/ai_assistant/api.py`：新增 `recover_orphaned_tasks() -> int`（逐字迁入 filter / 目标态 / 文案 / `finished_at`）
- [x] 2.2 `apps/ai_assistant/api.py`：`__all__`「任务操作」段加 `"recover_orphaned_tasks"`
- [x] 2.3 `apps/ai_assistant/apps.py`：`_run_startup_recovery` 改调 `api.recover_orphaned_tasks()`；删因此变为未使用的 `from .models import AITask` · `from django.utils import timezone` · `from models.constants import TaskStatus`（第 3 个是本单自己造成的死 import，一并清掉）
- [x] 2.4 新增 `tests/graybox/unit/test_ai_startup_recovery.py`（3 条：行为等价 / 已进 `__all__` / `apps.py` 无 ORM 写痕迹）

## 3. 验证

- [x] 3.1 `python manage.py check` → 0 issues；`makemigrations --check --dry-run` → `No changes detected`
- [x] 3.2 `python -m ruff check .` → **All checks passed!**（F401 通过即证明无死 import）；`ruff format --check .` → **249 files already formatted**
- [x] 3.3 新测试 **3 passed**；**回退 `apps.py` 到 HEAD 后 `test_apps_config_has_no_direct_orm_write` FAILED**（`assert 'objects.filter' not in ...`）—— 证明静态收敛断言真的在守；恢复后全绿
- [x] 3.4 `pytest tests/graybox/unit tests/arch -q` → **112 passed**（109 + 新增 3）；`pytest tests/graybox/integration -q` → **16 passed**
- [x] 3.5 `--check-boundaries` → 零违规；范围 `git diff --numstat` = api.py 23/8 · apps.py 3/8 · 新增测试 62 行

## 4. 说明

- **为什么除行为测试外还要静态断言**：即使有人把等价直写搬回 `apps.py`，行为测试仍会通过。只有 `inspect.getsource` 检查「源码里不再出现 `objects.filter` / `.update(`」才能把「收敛」这件事钉住（与 `converge-evaluator-writes` 的 monkeypatch spy 同一目的）。
- **本单是 D3 的可交付切片**：`apps.py` 这处已关；`element_locator` 的隐式写路径需先拆 `views.py`（1353 行，🔴 体积项），不在本单范围。

## 5. 续做（D3 剩余）

1. `apps/element_locator/views.py`（1353 行）拆分 → 再收敛其隐式写路径与 `WebElementViewSet` / `WebPageFlowViewSet` 的 `serializer.save()`
2. 其余 ViewSet 的隐式写（`case_manager` 4 · `element_locator/views_projects_drf` 2 · `evaluator` 3 · `ai_assistant/views_drf` 1 个类）—— 建议统一按「序列化层 `create/update` 委托 api」手法
3. `api.py` 体积（848 行，超 §4 上限 2×，🔴）另单拆分
