## 1. 事件流记录（引擎折叠层）

- [x] 1.1 让 `SOP_STEP_STARTED` 交出一条「开始/`sop_step`」记录与一行「步骤开始」日志，角色与模型留空；`SOP_STEP_ENDED` 仍不落行。验证：`pytest -c tests/pytest.ini tests/graybox/unit/test_sop_event_stream.py -k "sop_step"` 通过
- [x] 1.2 让 `HintBlockEvent` 与 `ExceedMaxItersEvent` 各交出一条记录（提醒全文入载荷，不截断），复用本轮角色与模型。验证：`pytest -c tests/pytest.ini tests/graybox/unit/test_sop_event_stream.py -k "hint or exceed"` 通过
- [x] 1.3 抽出「一条记录 + 一行日志」的公共装配，去掉三处重复样板。验证：`ruff check engines/agents/messaging/fold.py` 通过，且 1.1/1.2 用例仍全绿
- [x] 1.4 把步骤号匹配集合从「running / awaiting」扩到含「pending」，使步骤起点行挂得到正确步骤。验证：`ruff check engines/agents/workflow/ui_auto_workflow.py` 通过；真机跑一条多步 SOP，报告里步骤起点行的 `step_seq` 非空

## 2. 用例名与运行预算（运行上下文与工作流）

- [x] 2.1 新增 `set_case_title`，与既有 `set_step_context` 对称；未绑定运行上下文时静默。验证：`pytest -c tests/pytest.ini tests/graybox/unit/test_sop_event_stream.py -k "case_title"` 通过
- [x] 2.2 两条驱动路径（真实与替身）在每条用例开始时刷新用例名并清空上一条用例的步骤号。验证：`ruff check engines/agents/workflow/platform_run.py` 通过；同一任务跑两条用例后，事件表两段行的 `case_title` 不同且第二段 `step_seq` 从 1 开始
- [x] 2.3 运行上下文增加调用次数、起点与预算标志；新增 `count_model_call` / `budget_exceeded`，上限可由 `SOP_MAX_MODEL_CALLS` / `SOP_MAX_RUN_SECONDS` 覆盖，0 表示不限制。验证：`pytest -c tests/pytest.ini tests/graybox/unit/test_sop_event_stream.py -k "budget"` 通过
- [x] 2.4 事件展示层在每次模型调用结束时累加，超限抛出运行错误，使调用方能收束本轮。验证：`pytest -c tests/pytest.ini tests/graybox/unit/test_sop_event_stream.py -k "show_raises"` 通过
- [x] 2.5 超预算时停止整轮（不启动后续用例），已完成用例保留、原因可读。验证：`pytest -c tests/pytest.ini tests/graybox/unit/test_sop_event_stream.py` 通过；把上限设为 3 跑一次真任务，任务状态为失败且原因含「运行预算超限」
- [x] 2.6 执行与验收角色改为每条用例新建，落实「后一条用例不得复用前一条对话」。验证：真机跑两条用例，第二条的输入 token 不随第一条增长（相对此前同任务）

## 3. 写库加固（接收方）

- [x] 3.1 批量写入前先把行摘出缓冲；整批失败降级逐行，坏行只记警告并丢弃，不再反复重试到收尾。验证：`pytest -c tests/pytest.ini tests/graybox/unit/test_event_store_resilience.py -k "row_by_row"` 通过
- [x] 3.2 按累计字节上限提前写入，上限显著小于数据库单次语句允许的包长。验证：`pytest -c tests/pytest.ini tests/graybox/unit/test_event_store_resilience.py -k "bytes"` 通过
- [x] 3.3 截图编码失败时在行载荷上写编码失败标记，并留下含任务号、序号与角色名的警告。验证：`pytest -c tests/pytest.ini tests/graybox/unit/test_event_store_resilience.py -k "undecodable"` 通过

## 4. 报告展示

- [x] 4.1 为三类新事件补可读标题与明细（步骤名 + 第几次尝试、提醒全文、推理轮次用尽说明）。验证：`pytest -c tests/pytest.ini tests/graybox/unit/test_sop_event_stream.py -k "detail"` 通过
- [x] 4.2 步骤起点也作为一轮的起点，不再并入上一步骤的最后一轮。验证：真机跑一条多步 SOP，报告中每条用例的轮次数量随步骤起点增加，且步骤起点位于新轮内

## 5. 门禁与回归

- [x] 5.1 静态检查：`python manage.py check`、`ruff check`、`ruff format --check` 对 7 个改动文件与 2 个新测试文件全部通过
- [x] 5.2 架构门禁：`python utils/gen_arch_stats.py --check-boundaries` 零违规（引擎侧未引入 `apps.*` / `django.*`）
- [x] 5.3 单元回归：`pytest -c tests/pytest.ini tests/engines/agents -q` 无新增失败（本机 98 passed；7 failed + 12 errors 为真机不可达与临时目录被 ACL 拒绝的既有环境问题）
- [x] 5.4 待补跑：`pytest -c tests/pytest.ini tests/api/test_task_event_store.py` —— 本机 fixture 依赖临时目录、被 ACL 拒绝而无法执行，需在正常环境复跑确认 3.1/3.3 与既有断言一致
