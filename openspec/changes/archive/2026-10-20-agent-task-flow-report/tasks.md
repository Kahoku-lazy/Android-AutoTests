## 1. 只读流程

- [x] 1.1 `GET /api/reports/task/{id}` 返回可见任务的 `{status, task, rounds}`，不可见返回 404。验证：`python -m pytest tests/api/test_task_event_flow.py -q` 通过。
- [x] 1.2 连续同类增量合并为一条并写 `count`，阶段变化才新开一块。验证：同上测试中的分块与 `count == 3`。

## 2. 页面入口与时间

- [x] 2.1 测试报告列表点击一行进入 `/reports/task/:taskId`；任务卡「详情」进入同一路径，不再进入 `/ai-assistant/tasks/:taskId`。验证：`index.vue` 的行点击与 `TaskBoard.vue` 的 `openDetail` 都指向该路径。
- [x] 2.2 报告页起止与事件时间为 `YYYY-MM-DD HH:mm:ss`，起止旁显示整次执行耗时。验证：阅读 `TaskReport.vue` 的 `formatDateTime` 与 `formatElapsed`。

## 3. 用例步骤与结论

- [x] 3.1 按步骤序号倒退切开用例，并给出 PASS、FAIL、未完成、未执行。验证：`python -m pytest tests/api/test_task_event_flow.py -q` 中两条用例的结果。
- [x] 3.2 验收轮带上该步结论，执行轮带上交付原文。验证：同上测试中的 `verdict.message` 与 `handover`。
