## 1. 后端：平台口径

- [x] 1.1 `backend/apps/dashboard/ai_usage.py`：`_hourly_qs()` 改为全表（不再接收 agent_ids）；`ai_usage_stats`、`ai_daily_series`、`ai_today_usage_slots` 改用全平台口径；`_agent_usage` 单独按可见智能体过滤。验证：`manage.py check`。**验证结果**：`System check identified no issues (0 silenced)`。
- [x] 1.2 更新模块与函数注释：说明平台合计不随可见性变化、`agent_id = 0` 也计入。验证：ruff。**验证结果**：`ruff check` 通过、`ruff format --check` 2 files already formatted。
- [x] 1.3 新增 `tests/graybox/unit/test_dashboard_platform_usage.py`：不可见智能体与 `agent_id = 0` 的用量进入今日/累计/按日序列；`agents` 仍只列可见智能体。验证：pytest。**验证结果**：新增 3 用例 + 既有 dashboard 用例共 9 passed。

## 2. 前端：静默自动刷新

- [x] 2.1 `useDashboardStats` 新增 `refreshSilently()`：刷新数据但不置 `loading` / `refreshing`。验证：单测断言标志不变、数据更新。**验证结果**：`useDashboardStats.spec.ts` 14 passed（含静默成功、静默失败保留旧数据）。
- [x] 2.2 新增 `composables/useDashboardAutoRefresh.ts`：30 秒轮询；`document.hidden` 时跳过；`visibilitychange` 回到可见时立即刷新；卸载清理。在 `DashboardView.logic.ts` 接线。验证：typecheck。**验证结果**：`vue-tsc --noEmit` 无输出（通过）。
- [x] 2.3 新增 `frontend/tests/dashboard/p1/dashboardAutoRefresh.spec.ts`：到点刷新、隐藏不刷、可见立即刷、卸载停止。验证：vitest。**验证结果**：4 passed。

## 3. 验证与门禁

- [x] 3.1 相关测试：后端新增用例 + `tests/api/test_dashboard_agent_usage.py` + 前端 dashboard 套件全绿。验证：pytest / vitest 输出。**验证结果**：后端 9 passed；前端 dashboard 26 passed。
- [x] 3.2 真实环境：`/api/dashboard/stats/` 的 `today_usage.current` 与 `ai_usage.deepseek_cost.today` 含 Agent-02 的 flash 费用；打开仪表盘 30 秒后图表自动出现当日点。验证：接口输出 + 截图。**验证结果**：接口 `current={hour:16.94, tokens:1097428, cost:7.63835324}`；Playwright 打开页面后 36 秒内统计接口请求 2 次（首次 + 30 秒轮询）；截图 `temps/dashboard-today-usage-final.png` 显示 16:00 后出现 1.2M / 8.00 元的当日点。
- [x] 3.3 `python run.py check` 与 `openspec validate platform-wide-usage-cost --strict`。验证：退出码 0。**验证结果**：门禁 22/22 阻塞项通过；变更校验 valid。
- [x] 3.4 归档变更：delta 合入 `openspec/specs/dashboard-ai-usage` 与 `dashboard-trend-charts`。**验证结果**：已归档到 `openspec/changes/archive/2026-10-27-platform-wide-usage-cost/`，主规格 Purpose 同步为平台口径。
