# API-执行引擎 — 已下线

> 2026-09-09：`apps/test_runner` 业务代码与 `/api/runner/*`、`ws/test-run/{run_id}` 已拆除。
> App 仅保留卸表迁移（`0020_delete_test_runner_models`），请执行 `python manage.py migrate test_runner` 删除 `tr_*` 表。
> 测试报告模块保留为空壳；用例管理单步调试不可用。
