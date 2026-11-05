## 1. 前端：轮询去重与节流

- [x] 1.1 `frontend/src/modules/dashboard/index.vue`：删除重复的 `useDashboardAutoRefresh` 导入与调用（保留 `DashboardView.logic.ts` 里的那一处）。
- [x] 1.2 `composables/useDashboardAutoRefresh.ts`：`DASHBOARD_REFRESH_MS` 改为 30 秒；`tick()` 增加在途守卫（上一轮未完成直接跳过），可见性回调同样受守卫约束；更新注释与常量一致。
- [x] 1.3 `composables/useDashboardStats.ts`：`refreshSilently` 增加 `silentInFlight` 守卫，重复触发直接返回。
- [x] 1.4 `frontend/tests/dashboard/p1/dashboardAutoRefresh.spec.ts`：断言间隔 ≥15s、上一轮未完成时跳过、隐藏暂停与卸载清理保持。 实测：`npx vitest run dashboard` 61 passed（7 文件）。

## 2. 后端：智能体只取一次、不读头像

- [x] 2.1 `backend/apps/dashboard/ai_usage.py`：新增 `load_visible_agents(user_id)`，用 `AIAgent.objects.only(...)` 排除 `avatar`/`tags`/`description`；`_task_qs` 与五个统计函数接受可选 `agents`，缺省自行装载。
- [x] 2.2 `backend/apps/dashboard/views.py`：统计视图装载一次 `agents`，传给 `ai_usage_stats` / `ai_task_daily_execution` / `ai_task_execution_summary` / `ai_recent_tasks` / `platform_activities`；`agents.total/active` 用同一次装载的列表计算；设备统计合并为一次聚合。
- [x] 2.3 `platform_activities` 复用同一份 `agents`，不再单独整行读取。

## 3. 后端：用量汇总单次聚合

- [x] 3.1 `backend/apps/usage_ledger/api.py`：`usage_summary` 改为「一次 category+provider 分组 + 内存拼装」，去掉分类级 N+1，输出结构不变。
- [x] 3.2 同文件新增 `usage_dashboard()`：一次产出 today / total / voice_today / voice_total / recent，供仪表盘一次调用。
- [x] 3.3 `backend/apps/dashboard/views.py`：`usage_ledger` 段改用 `usage_dashboard()`。

## 4. 测试

- [x] 4.1 `tests/graybox/unit/test_dashboard_load_budget.py`：断言 `/api/dashboard/stats/` 不超过 25 条 SQL、`ai_agents` 恰好查询 1 次且不含 avatar、响应顶层字段与用量账本五口径齐全。 实测：3 passed。
- [x] 4.2 `tests/graybox/unit/test_usage_ledger.py`：补 `usage_dashboard()` 与 `usage_summary()` 输出一致性（total / categories / providers 与排序），并断言批量产出恰好 5 条查询。 实测：8 passed。
- [x] 4.3 后端目标测试全绿：`tests/graybox/unit/test_dashboard_*.py`、`test_usage_ledger.py`、`tests/api/test_dashboard_agent_usage.py`。 实测：21 passed。

## 5. 验收

- [x] 5.1 重新测量：`temps/dashboard_request_profile.py`（进程内 SQL 与耗时）与 `temps/dashboard_http_probe.py`（HTTP 顺序/并发）。
- [x] 5.2 目标达成：统计接口 **52 → 25 条 SQL**、进程内 **2518 → 271 ms**；HTTP 单请求 **1938/3545 → 989/688 ms**；3 并发每个 **≈4900 → ≈1200–1300 ms**；活动接口进程内 **775 → 296 ms / 5 条 SQL**。响应体 10,676 bytes，字段结构不变。
- [ ] 5.3 `python run.py check` 阻塞项全绿；`openspec validate optimize-dashboard-load --strict` 通过。 现状：`openspec validate --strict` 通过；门禁的 `vitest` 受工作区并行进行中的登录页改名（`LoginView.hero.spec.ts` 仍断言「AI 自动化测试平台」）与默认并发下 vitest worker 启动超时影响，未能全绿——与本变更文件无关，详见变更说明。
