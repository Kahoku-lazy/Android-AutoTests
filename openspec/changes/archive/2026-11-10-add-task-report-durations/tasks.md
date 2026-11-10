## 1. 后端：耗时取数

- [x] 1.1 `backend/apps/task_list/task_reports.py`：`started_at` / `ended_at` 加入 `_DETAIL_COLUMNS`（只随代表行取，瘦列 `_SLIM_COLUMNS` 不动），`_EventRow` 增加两个字段并在 `_load_events()` 的明细回填里赋值。验证：`python -m pytest -c tests/pytest.ini tests/api/test_task_event_flow.py` 14 passed（既有分组断言不回归）。
- [x] 1.2 `_rounds()` 返回 `(轮次列表, 轮次编号→跨度)`：跨度由 `_fold_round_time()` 累加 `start` / `end` / `model_ms` / `has_end`，折叠增量的尾巴用 `started_at + duration_ms` 兜住。验证：新增单测断言单轮 `model_ms` 只含模型调用（12000，而该轮墙钟 30000）。

## 2. 后端：四层字段

- [x] 2.1 `_annotate()` 把私有键转成对外字段并剥离：`model_ms`（该轮没有模型事件时回退为轮次墙钟）、`running`（缺少 `ended_at` 为 true），同时删掉 `_start` / `_end` / `_model_ms`。验证：`python -m pytest -c tests/pytest.ini tests/api/test_task_event_flow.py` 通过，且响应里不出现下划线开头的键。
- [x] 2.2 `_flow_cases()` 给 `steps[]` 与 `cases[]` 补 `duration_ms`（墙钟跨度，按用例内该步骤的轮次求 min/max）与 `running`（该步/该用例有未结束轮次则为 true）。验证：新增单测——两步用例的最早/最晚事件跨度等于用例 `duration_ms`，且步骤之和不超过用例。

## 3. 后端测试

- [x] 3.1 `tests/api/test_task_event_flow.py`：`_event()` 支持 `started_at` / `ended_at` / `duration_ms` 入参；新增四条用例对应 spec 场景——步骤耗时覆盖执行与验收、用例耗时覆盖全部步骤、运行中轮次不带数字、存量事件缺时间戳返回 0。验证：`python -m pytest -c tests/pytest.ini tests/api/test_task_event_flow.py -q` 全绿。

## 4. 前端：类型与格式化

- [x] 4.1 `frontend/src/shared/types/ai.ts`：`TaskReportRound` 加 `model_ms?: number` / `running?: boolean`；`TaskReportStep` 与 `TaskReportCase` 加 `duration_ms?: number` / `running?: boolean`。验证：`npm run typecheck` 通过。
- [x] 4.2 `frontend/src/modules/task-list/helpers/report-steps.ts`：新增 `formatDurationMs(ms)` 纯函数（`42s` / `3m12s` / `1h02m`，0 或负数返回空串），并把 `durationMs` / `running` 透传进 `StepView`。验证：新增 `frontend/tests/task-list/p0/report-durations.spec.ts` 覆盖三档格式与 0/负数。

## 5. 前端：三处展示

- [x] 5.1 `CaseStepList.vue`：步骤行结果徽标**之前**显示青色时间片耗时（缺失不渲染），未结束显示「进行中」。验证：`npx vitest run tests/task-list` 通过，新增用例断言 `3m12s` 与「进行中」。
- [x] 5.2 `RoundProcess.vue`：执行/验收块头在模型名之后显示 `模型 38s`（`running` 时显示「进行中」，0/缺失不渲染）。验证：同上单测断言块头文案。
- [x] 5.3 `TaskDetailPage.vue`：用例标题行结果徽标**之前**显示青色时间片耗时（缺失不渲染）。验证：页面级单测断言标题行含 `3m12s`，且缺字段时不含 `0s`。

## 6. 门禁

- [x] 6.1 后端：`python manage.py check`、`ruff check backend/apps/task_list`、`ruff format --check backend/apps/task_list`、`python -m pytest -c tests/pytest.ini tests/api/test_task_event_flow.py` 全绿。
- [x] 6.2 前端：`npx vitest run tests/task-list`、`npm run typecheck`、`npm run build:check` 全绿；`npx eslint src/modules/task-list src/shared/types` 0 error。
- [x] 6.3 真数据抽查：用一个真实任务打开详情页，确认四层耗时数量级合理（步骤耗时不小于其执行/验收轮墙钟、用例耗时覆盖全部步骤），并把抽查结论记到变更说明。 实测：5 个真实任务（含 1,048 事件的任务 180）全量对拍 0 违例——各用例步骤耗时之和 ≤ 用例耗时、各轮 model_ms ≤ 所属步骤耗时；任务 180 用例 623.0s，四步 75.9s/234.4s/99.5s/188.0s。
