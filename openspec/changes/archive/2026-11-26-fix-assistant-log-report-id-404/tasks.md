# Tasks: fix-assistant-log-report-id-404

## 1. 判定前移

- [x] 1.1 在 `backend/apps/ai_assistant/services/assistant_threads.py` 提取纯函数 `is_safe_report_id(report_id: str) -> bool`，
  规则与现有 `resolve_thread_report()` 一致（`Path(id).name == id` 且不是 `.`/`..`），并让 `resolve_thread_report()` **复用它**，不留第二套判定。
  - 验证：`python -m pytest -c tests/pytest.ini tests/ai_assistant/unit -q -k thread` 不回归
- [x] 1.2 `AssistantThreadLogFileView.get()` 中把 `is_safe_report_id()` 判定**前移到 `consume_log_ticket()` 之前**：非法 id 直接 `404`，且不进入换票流程。
  - 验证：`python -m pytest -c tests/pytest.ini tests/ai_assistant/api/test_assistant_thread_logs.py -q` 中 `test_unknown_report_is_404` 转绿
- [x] 1.3 补一条用例：非法 `report_id` 请求后，同一张有效 ticket **仍然可用**（证明没被烧掉）。
  - 验证：新用例通过；反向验证（把 1.2 的顺序改回去）该用例会失败
- [x] 1.4 语义回归：合法 id 的三条既有行为不许变 —— 无票 401、过期/已用票 401、票有效但报告不存在 404。
  - 验证：`tests/ai_assistant/api/test_assistant_thread_logs.py` 全组通过

## 2. 关单

- [x] 2.1 `python -m pytest -c tests/pytest.ini tests/ai_assistant -q` 全组通过
  - 2026-11-26 实跑 75 passed（原先 15 条红在 `test_roles.py` / `test_role_kinds.py`，与本变更无关，
    已由 `fix-role-graybox-contract-drift` 修掉；本变更自身相关 `test_assistant_thread_logs.py` 全程 5/5 绿）。
- [x] 2.2 `python -m ruff check backend/apps/ai_assistant tests/ai_assistant` + `ruff format --check` 通过
- [x] 2.3 `python utils/gen_arch_stats.py --check-boundaries` 退出码 0
- [x] 2.4 `npx openspec validate fix-assistant-log-report-id-404` 通过
