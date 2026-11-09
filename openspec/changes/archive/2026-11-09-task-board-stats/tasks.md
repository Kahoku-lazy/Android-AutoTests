## 1. 后端统计接口

- [x] 1.1 `task_list/api.py` 增加 `task_stats(tasks)`：一次 `values("status").annotate(Count("id"))` 聚合，返回 `{total, running, pending, success, failed, interrupted, cancelled, finished, success_rate}`；验证：`tests/api/test_task_stats.py` 6 条全绿（口径 / 历史 success / 运行中不算已结束 / 空库 / 可见范围 / 查询数不随行数增长）。
- [x] 1.2 `task_list/views.py` 增加 `AgentTaskStatsAPIView`，按当前用户可见智能体过滤；`urls.py` 注册 `GET /api/tasks/stats/`；验证：越权用例断言他人任务不计入（total 2 而非 7），空库返回全 0。
- [x] 1.3 更新 OpenAPI 基线；验证：`python run.py check` 的 `openapi-schema` 与 `openapi-coverage` 通过。

## 2. 前端任务概览

- [x] 2.1 `shared/types/ai.ts` 增加 `TaskStats` / `TaskStatsResponse`，`task-list/api/tasks.ts` 增加 `getTaskStats()`；验证：`vue-tsc --noEmit` 通过。
- [x] 2.2 `useTaskList` 增加 `stats` 与 `loadStats()`：列表加载成功后顺带取统计，删除 / 清空后重取，失败静默保留旧值，不新增定时器；验证：`tests/task-list/p0/task-stats.spec.ts` 断言「删除后统计刷新」「统计失败不进错误态」。
- [x] 2.3 新增 `TaskStatsStrip.vue`（三个 `KpiCard`：总任务 / 成功率 / 执行中，微倾 -0.8° / 0.6° / -0.5°，加载中没有旧值时用 `SkeletonCard`），接入 `TaskBoard.vue` 顶部「任务概览」分区；验证：`vue-tsc`、`vite build`、`prettier --check` 通过。
- [x] 2.4 新增 `TaskOutcomeDonut.vue`（`AppCard` + ECharts 环形图 + 图例计数与占比），四类固定顺序，零值不画扇区但保留图例，四类全 0 走 `EmptyState`；验证：真实页面截图核对（成功 14 / 失败 10 / 中断 4 / 取消 3 → 45.2% / 32.3% / 12.9% / 9.7%）。

## 3. 柱状图（数量 + 分智能体）

- [x] 3.1 `task_stats_by_agent(tasks, agents)`：一次 `GROUP BY agent_id, status` 聚合，覆盖全部可见智能体（没任务的给全 0），名字取线路名回退助手名；`/api/tasks/stats/` 响应增加 `agents` 数组；验证：`tests/api/test_task_stats.py` 覆盖「每个可见智能体一项」「分状态计数」「线路名」「他人私有智能体不出现」。
- [x] 3.2 `resultBarCards(stats)` 纯函数：第一张总体「结果数量」，之后每个智能体一张（标题=智能体名，副标题含总数/执行中/成功率）；验证：`tests/task-list/p0/task-stats.spec.ts` 断言新增智能体自动多一张、无任务智能体为全 0。
- [x] 3.3 新增 `TaskCountBars.vue`（单张柱状图卡：四根柱 + 柱顶数值 + 同色）与 `TaskShareCharts.vue`（网格按智能体数量自增），接入「任务结果占比」右侧；验证：`vue-tsc`、`vite build`、`prettier --check` 通过。
- [x] 3.4 版式定稿：图例置顶横向排（只有颜色与类别名，不显示「14 条」与百分比）、占比回到环上标签、四张卡按行等高（`.task-share` 用 `align-items: stretch`，环图与柱图高度自适应）；验证：1600px 与 1280px 实跑截图，四卡上下边界对齐、环上百分比无截断。

## 4. 测试与收口

- [x] 4.1 前端用例：`tests/task-list/p0/task-stats.spec.ts` 12 条（成功率文案含「—」、四类占比、零值保留、空数据、柱状图卡片序列、新增智能体自动多图、统计随列表刷新、统计失败保留旧值）；验证：`npx vitest run tests/task-list` 全绿。
- [x] 4.2 门禁：`python run.py check` 阻塞项 **23/23 通过**；`python -m pytest -c tests/pytest.ini tests/api/test_task_stats.py -q` 10 条全绿；`npm run lint:styles` 对新增文件无违规（task-list 存量 40 条 G6 越界借用为既有欠账，未新增）。
