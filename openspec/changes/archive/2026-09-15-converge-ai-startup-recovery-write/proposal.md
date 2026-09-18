## Why

🟠 **D3 写库收敛残留：`AppConfig.ready` 里的启动恢复直接 ORM 写**（`apps/ai_assistant/apps.py`）。

实测（2026-09-15）：

```python
def _run_startup_recovery(self) -> None:
    ...
    from .models import AITask
    recovered = AITask.objects.filter(status=TaskStatus.RUNNING).update(
        status=TaskStatus.FAILED,
        result="执行中断：服务重启导致任务线程终止",
        finished_at=timezone.now(),
    )
```

问题有两条：

1. **写库越过 api 白名单**（`apps/AGENTS.md` §1.2：`View / Consumer / Tool` 直接 ORM 写属违规；本模块 `api.py` 的文件头也把「写操作收敛到本文件」写成铁律）。同类的 `start_task` / `finalize_task` 早已在 `api.py` 内，唯独这处恢复逻辑留在 `apps.py`。
2. **状态口径散落**：`"执行中断：服务重启导致任务线程终止"` 这条用户可见文案与状态迁移逻辑写在框架装配文件里，前端轮询到的 `result` 文案无法与任务状态机同处维护。

> 注：本单是 D3 收敛的**可交付切片**。同样属 D3 的 `element_locator` 隐式写路径需要先拆 `apps/element_locator/views.py`（1353 行，🔴 体积项），不在本单范围。

## What Changes

- `apps/ai_assistant/api.py`：新增写原语 `recover_orphaned_tasks() -> int` 并登记 `__all__`（放在「任务操作」段）—— 把「running → failed + 文案 + finished_at」这条迁移整体搬进写库归口
- `apps/ai_assistant/apps.py`：`_run_startup_recovery` 改为调 `api.recover_orphaned_tasks()`；删掉因此变为未使用的 `from .models import AITask` 与 `from django.utils import timezone`
- 新增 `tests/graybox/unit/test_ai_startup_recovery.py`：① 只把 `running` 置 `failed`，`pending`/`completed` 不动，且 `finished_at` / 文案落库；② 静态断言 `apps.py` 源码里**不再出现 ORM 写痕迹**（`objects.filter` / `.update(`），并确实调用 api

- **BREAKING**：无（恢复语义逐字保持一致：同一 filter、同一目标态、同一文案、同一 `finished_at`）
- 按 schema 约定设 `skip_specs: true`

## 关联文档

- 分层纪律：`apps/AGENTS.md` §1.2（内部层纪律表 · L4 总体禁止）· `apps/ai_assistant/api.py` 文件头（写操作收敛铁律）
- App 约束：`apps/ai_assistant/AGENTS.md`
- 门禁：`django-backend-check/references/calibration.md` §2 🟠「写库在 views 但同 App 未抽 api（收敛违规）」· §6 api.py 契约 · §7
- 前置分析：本会话 D3 复查（缺陷 D3-2 在 `ai_assistant` 的最后落点）

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

（无 —— 不改 Requirement 文本，故无 delta）

## Impact

- 源码：`apps/ai_assistant/api.py`（+1 函数 +1 `__all__` 项）· `apps/ai_assistant/apps.py`（恢复逻辑改调 api，净减行）
- 测试：新增 `tests/graybox/unit/test_ai_startup_recovery.py`
- 验证：`manage.py check` · `makemigrations --check`（无模型改动）· `ruff check .` / `ruff format --check .` · 全量单测 · `--check-boundaries`
- 不在本单范围：`element_locator/views.py` 的 1353 行拆分 + 其隐式写路径收敛（需先拆文件）· 其余 ViewSet 的隐式 `serializer.save()`
