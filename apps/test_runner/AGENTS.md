# test_runner App AGENTS.md

> 执行引擎已下线。本 App 仅保留卸表迁移，禁止恢复 views / urls / WS / 执行器。

## 红线

| 只做 | 禁止 |
|------|------|
| 保留迁移链，使 `tr_*` 表可被 `migrate` 删除 | 恢复 `/api/runner/*`、`ws/test-run`、执行器、任务看板 |

跨模块写 `tr_` 已无目标表。报告模块返回空列表；用例单步调试不可用。
