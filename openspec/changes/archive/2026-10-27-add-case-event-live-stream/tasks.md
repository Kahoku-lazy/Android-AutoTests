## 1. 后端

- [x] 1.1 `event_sink.flush_sink` + `AgentEventsShow.show(flush=)` + `show_event(flush=)`：用例编写逐条事件落库。验证：`test_sop_event_stream.py` 13 项通过；任务 150 运行中 12 条事件可见。
- [x] 1.2 `CaseAuthoringWorkflow` 调用 `show_event(..., flush=True)`；设备流程保持默认。验证：用例编写任务运行中 `task_events` 持续增长。
- [x] 1.3 `AgentTaskRerunAPIView` 允许 `interrupted` 重跑。验证：任务 149（interrupted）重跑生成任务 150。

## 2. 前端

- [x] 2.1 `TaskDetailPage` 对运行中的 case_authoring 任务每 3 秒刷新报告，终态停止。验证：任务 150 页面显示 3 条事件与「运行中，自动刷新…」。
- [x] 2.2 运行中暂无事件显示等待提示；事件流区块始终渲染。验证：截图确认。
- [x] 2.3 `TaskBoard` 对 `interrupted` 任务显示「重新执行」。验证：类型检查通过。

## 3. 验证

- [x] 3.1 后端测试：`tests/graybox/unit/test_sop_event_stream.py`、`tests/graybox/unit/test_case_authoring_task_runner.py`。验证：全部通过。
- [x] 3.2 `python run.py check`：阻塞项 22/22 通过。
- [x] 3.3 OpenAPI 基线同步；`openspec validate add-case-event-live-stream --strict` 通过并归档。
