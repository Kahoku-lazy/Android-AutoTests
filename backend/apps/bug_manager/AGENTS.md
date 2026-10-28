# bug_manager App AGENTS.md

> **AGENTS 层级**：二级约束 —— 根 `AGENTS.md` 与上级 `backend/apps/AGENTS.md` 优先于本文件。

## 职责

- 拥有 `bug_tickets` 表：任务错误的分类、错误正文、处理状态与任务快照。
- 提供 `/api/bugs/`：列表/统计、详情、状态更新、历史同步。
- 从 `task_list.Task` 终态提取两类问题：`ui_automation` 与 `case_authoring`。

## 红线

| 只做 | 禁止 |
|------|------|
| BUG 台账的读写经 `api.py` | 在 view 直写 ORM |
| 只读 `Task` Model 做同步扫描 | 修改任务状态、结果或验收结论 |
| `task_id` 快照 + 唯一 `(task_id, category, source_ref)` | 建 FK 级联删除审计记录 |
| 自动登记失败只记日志 | 让台账失败影响任务终态 |

## 依赖方向

- `bug_manager` → `task_list`：只读 `Task` Model；不 import `task_list` 的 views/runner/task_reports。
- `task_list` → `bug_manager`：只在终态后调用 `bug_manager.api.record_task_bugs`。
- `bug_manager` 不依赖前端或引擎。

## 关单附加项

```
[ ] python manage.py check
[ ] makemigrations --check
[ ] python -m pytest -c tests/pytest.ini tests/graybox/unit/test_bug_ticket_*.py tests/api/test_bug_tickets.py
[ ] python -m ruff check backend/apps/bug_manager backend/apps/task_list
[ ] python utils/gen_arch_stats.py --check-boundaries
```
