## 1. 引擎收尾：中断也落报告

- [x] 1.1 在 `engines/backend_bridge/workflow/bound_sop.py` 的 `_SopCapture` 上记录 `start()` 拿到的 recorder 与起始时刻，新增 `abort(exc) -> Path | None`：调用 `recorder.finish(cost_s)` 补齐收尾汇总、`raw.end()/close()`、`aligned.set_steps([])`、`aligned.end()`，写入 `document["run"]["运行中断"]` 后用 `AlignedReportRenderer` 渲染并返回 `record.html_path`；验证：`temps/` 下临时脚本构造假 recorder 与临时目录，断言目录出现 HTML 且正文含「运行中断」，跑完删除脚本
- [x] 1.2 在 `run_bound_sop` 中把 `await run_sop(...)` 包进 `try/except`：`RunCancelled` 与 `BudgetExceeded` 原样抛出；其余异常先 `capture.abort(exc)`，再调用新增的 `on_abort(path, exc)` 回调，最后 `raise` 原异常；验证：临时脚本注入异常，断言回调恰好收到一次路径、异常类型不变，取消异常时回调未被调用
- [x] 1.3 `abort()` 内部兜底：渲染或收尾再抛异常时只写 `agent_event_log` 警告，不覆盖原异常；验证：临时脚本让渲染器抛错，断言原异常仍抛出且日志有记录

## 2. 任务侧接入

- [x] 2.1 `backend/apps/task_list/task_runner.py` 的 `_failure_payload` 增加 `report_path` 参数并合并 `_report_locator(report_path)`；验证：临时脚本断言失败 payload 含 `report_run` / `report_name`，空路径时不新增字段
- [x] 2.2 `run_task_async` 建一个可变 holder，`_run_assistant_sop` 把 `on_abort` 闭包写成 `holder["report_path"] = path`，异常分支读取 holder 并传给 `_failure_payload`；验证：由 2.3 的灰盒用例覆盖
- [x] 2.3 新增灰盒用例 `tests/task/integration/test_task_failure_report.py`（含 `tests/task/integration/__init__.py`）：monkeypatch `engines.backend_bridge.workflow.bound_sop.run_bound_sop`，让它在调用 `on_abort` 之后抛异常，调用 `run_task_async`，用 ORM 读回任务并断言 `status=failed`、`Task.result` 的 `report_run` / `report_name` 非空；验证：`python -m pytest -c tests/pytest.ini tests/task/integration/test_task_failure_report.py`

## 3. 契约守护与回归

- [x] 3.1 在 `tests/arch/unit/test_sop_report_contract.py` 增加契约守护：`bound_sop.py` 含 `on_abort` 与 `abort(`，`task_runner.py` 的异常分支引用 `_report_locator`；验证：`python -m pytest -c tests/pytest.ini tests/arch/unit/test_sop_report_contract.py`
- [x] 3.2 在 `tests/report/integration/` 补一条灰盒断言：沿用既有鉴权夹具，ORM 造一条 `failed` 且 `result` 带报告定位的任务，请求 `GET /api/reports/`，断言该行入列、`source=sop` 且带同一定位；验证：`python -m pytest -c tests/pytest.ini tests/report/integration/`
- [x] 3.3 跑门禁：`python manage.py check`、`ruff check engines/backend_bridge/workflow/bound_sop.py backend/apps/task_list/task_runner.py`、`python -m pytest -c tests/pytest.ini tests/task tests/report tests/arch/unit`、`python utils/gen_arch_stats.py --check-boundaries`（本变更相关用例全绿；8 条失败为改动前既有，涉及 ai_assistant / 前端路径 / engines/agents 退役，见交付说明）

## 4. 文档与边界

- [x] 4.1 更新 `.agents/docs/apps/task_list/task_list_task_lifecycle.md`（失败终态的报告口径）与 `.agents/docs/engines/backend_bridge/backend_bridge_role_assembly.md`（报告渲染时机增加“异常中断”）；验证：人工核对两处描述与 1.1/2.1 的实现一致
- [x] 4.2 确认改动边界：本次会话只改 `bound_sop.py`、`task_runner.py` 与测试/文档；`engines/ae_harness` 无本次改动（按文件 mtime 均早于会话开始校验，工作树里既有的 ae_harness 差异不是本次引入）、无新迁移、无新增自定义异常类；验证：mtime 过滤为空且 `python manage.py makemigrations --check` 通过

## 5. 端到端验收

- [ ] **skipped（2026-11-27 需求方决定：真机验证不做）** 5.1 提交一条会触发模型拒绝的任务（如临时使用无效模型名或密钥），确认任务进入 `failed`、行内出现「报告」、打开后概览含「运行中断」，且 `/reports` 出现该行；验证：人工按步骤操作并截图留痕
- [ ] **skipped（2026-11-27 需求方决定：真机验证不做）** 5.2 回归正常路径：一条完成任务与一条验收不通过任务仍各有一份报告；一条取消任务与一条中断任务仍不显示「报告」入口；验证：人工核对任务清单与 `/reports`
