# Tasks: fix-assistant-log-report-id-404

> 实施于 2026-11-24。仓库测试口径当日已变：`tests/**/unit/` 整体迁出，只剩灰盒（`api/`、`integration/`）+ `tests/arch/unit` 契约守护，
> 因此本变更的用例落在 `tests/ai_assistant/api/`（灰盒），不再新建单元用例。

## 1. 判定前移

- [x] 1.1 在 `backend/apps/ai_assistant/services/assistant_threads.py` 提取纯函数 `is_safe_report_id(report_id)`，
  规则与 `resolve_thread_report()` 原逻辑一致（`Path(id).name == id` 且非 `.`/`..`），并由 `resolve_thread_report()` 复用。
  经 `api.py` 导出（import 与 `__all__` 各一行），与 `resolve_thread_report` 同口径。
  - 验证：`tests/ai_assistant/api/test_assistant_thread_logs.py` 全绿；边界检查零违规
- [x] 1.2 `AssistantThreadLogFileView.get()` 中把该判定**前移到 `consume_log_ticket()` 之前**：非法 id 直接 404，不进入换票流程。
  - 验证：`test_unknown_report_is_404` 由 HEAD 的 **401 失败**转为通过
- [x] 1.3 补灰盒用例 `test_illegal_report_id_does_not_consume_ticket`：先为一轮已完成报告换票，再用非法 id 请求（带该票），
  断言 404 且随后 `consume_log_ticket(ticket, ...)` **不抛** —— 证明票没被烧掉。
  反向证据：修复前同一调用返回 401（原 `test_unknown_report_is_404` 的失败态），即票在非法 id 上被消耗。
- [x] 1.4 语义回归：合法 id 的三条既有行为不变 —— 无票 401、票有效但报告不存在 404、进行中 409。
  验证：该文件 **5 passed**（含 `test_running_report_is_409`、`test_log_rows_carry_local_time`、`test_running_log_row_has_no_time`）

## 2. 关单

- [x] 2.1 `tests/ai_assistant/api/test_assistant_thread_logs.py` 5 passed。**注**：`tests/ai_assistant` 全组另有 **15 项失败**，
  经查为既有问题、与本变更无关 —— 集中在 `test_roles.py` 等（`assert 403 == 201`，`assistant-author` 收紧写权限后用例未同步），
  `test_roles.py` 本身在本次改动中未被修改。该红单独立项处理。
- [x] 2.2 `ruff check` + `ruff format --check`（`backend/apps/ai_assistant`、`tests/ai_assistant`）：**All checks passed / 38 files already formatted**
- [x] 2.3 `python -m utils.gen_arch_stats --check-boundaries` → **退出码 0，零违规**
- [x] 2.4 `npx openspec validate fix-assistant-log-report-id-404` → **valid**

## 3. 归档时机

**合并进主干之后再归档**（需求方 2026-11-24 指定）。归档命令：`npx openspec archive fix-assistant-log-report-id-404 --yes`；
验证标准：`openspec list` 不再列出该变更，且 `openspec/specs/` 无新增 delta（本变更 `skip_specs`，不产生能力变更）。
