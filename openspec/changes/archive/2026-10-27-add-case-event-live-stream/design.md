# 设计：用例编写模型事件流实时可见

## Context

`TaskEventSink` 按 50 条或 close 时批量写库；`TaskDetailPage` 只在挂载时请求一次报告。003 任务单轮编写约 10 分钟，运行中报告为空。

## Decisions

### D1 在 show_event 的接收方线程里 flush

`AgentEventsShow.show` 增加 `flush` 参数；`show_event(..., flush=True)` 将 `flush` 透传给 `database_sync_to_async` 的接收方，在同一个工作线程里写库，避免事件循环被同步 DB 阻塞。只有 `CaseAuthoringWorkflow` 传 `flush=True`，设备执行不传。

### D2 只对 case_authoring 轮询

`TaskDetailPage` 每 3 秒重新请求报告，但仅当 `task_kind=case_authoring` 且状态为 `running` / `pending`；设备任务保持一次性加载，避免放大事件流请求。

### D3 运行中显示占位而不是空白

事件流区块在运行中始终渲染，暂无事件时显示「模型正在运行，事件写入后会自动出现…」；有事件后替换为时间线。

### D4 中断任务允许重跑

`AgentTaskRerunAPIView` 接受 `failed` 与 `interrupted`；前端任务卡对两种状态都显示「重新执行」。解决后端重启导致 003 被标中断后无法从 UI 重跑的问题。

## Risks / Trade-offs

- [逐条 flush 增加 DB 写次数] → 只对用例编写任务（约几十条事件）开启；设备任务不受影响。
- [3 秒轮询增加报告查询] → 只限运行中的用例编写任务，终态即停。
- [思考块很大] → 报告仍按事件返回全文，前端折叠 + 展开全文。

## Migration Plan

纯增量：无需迁移；重启后端后新任务生效，旧任务报告仍可读。
