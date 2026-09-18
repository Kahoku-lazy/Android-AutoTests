## Context

`ai_assistant` 的任务写操作早已收敛在 `api.py`（`start_task` / `finalize_task` / `delete_task` 等），唯一例外是 `apps.py` 的启动恢复。本单把这一处搬回归口。

## Goals / Non-Goals

**Goals:**

- `AppConfig` 不再直接写库；启动恢复经 `api.py`
- 用测试同时锁住「行为等价」与「不再直写」两件事

**Non-Goals:**

- 不改恢复语义（filter / 目标态 / 文案 / `finished_at` 逐字不变）
- 不改线程模型（仍在 `ready()` 起后台线程、等 `ready_event` 后再查库）
- 不动 `element_locator`（需先拆 1353 行文件）

## Decisions

### 1. api 函数返回受影响行数，返回原始 int

- **选择**：`recover_orphaned_tasks() -> int`（`QuerySet.update()` 的返回值）
- **理由**：调用方要据此决定是否写日志（`if recovered:`）。按 §6 规则，api 不得返回 ORM/QuerySet —— `update()` 返回的是 int，合规

### 2. 顺带删除 apps.py 里因此变为未使用的两个 import

- **选择**：删 `from .models import AITask` 与 `from django.utils import timezone`
- **理由**：不删就是死 import（ruff F401 也会拦）；这是本单自己造成的，按「只清理自己造成的混乱」处理

### 3. 除行为测试外加一条静态收敛断言

- **选择**：`inspect.getsource(apps_module)` 断言源码中不含 `objects.filter` / `.update(`，且含 `recover_orphaned_tasks`
- **理由**：行为测试无法证明「写没有偷偷回到 apps.py」——即使 apps.py 再做一次等价直写，行为测试仍会通过。静态断言才能把收敛这件事钉住（与 `converge-evaluator-writes` 的 spy 断言同一目的）

## Risks / Trade-offs

- [App 装配期导入 `api` 引发循环导入] → `api` 的导入放在线程体内部（原 `from .models import AITask` 同位置），且已 `django_apps.ready_event.wait()`，与现状同一时序约束
- [恢复语义漂移] → 迁移逐字照搬；新测试断言 `finished_at` 非空与文案包含「服务重启」；`tests/graybox/unit` 全量兜底
- [api 体积] → `api.py` 已 848 行（超 §4 上限 2×，🔴 体积项另计）；本单净增约 8 行，不改善也不掩盖该问题

## Migration Plan

1. `api.py` 加函数 + `__all__`；`apps.py` 改调 api 并删死 import
2. 新增测试；跑静态门禁与全量单测
3. 归档；回滚 = `git checkout apps/ai_assistant/api.py apps/ai_assistant/apps.py` + 删测试
