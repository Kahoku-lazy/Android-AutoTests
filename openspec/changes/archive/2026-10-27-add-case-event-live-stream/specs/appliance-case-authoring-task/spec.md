## ADDED Requirements

### Requirement: 用例编写过程在运行中可见

用例编写流程 MUST 在每条事件交给接收方后立即 flush，使运行中的任务报告能读到已发生的 SOP 步骤、思考块、工具调用与模型调用事件。设备执行任务 MUST 保持原有的批量落库行为。

任务详情页对 `task_kind=case_authoring` 且状态为 `running` / `pending` 的任务 MUST 自动刷新报告（约 3 秒一次），显示「运行中，自动刷新…」；进入 `completed` / `failed` / `cancelled` / `interrupted` 后 MUST 停止轮询。运行中暂无事件时 MUST 显示等待提示，不得呈现空白区块。

`POST /api/tasks/{id}/rerun/` MUST 允许 `failed` 与 `interrupted` 两种终态任务重跑；重跑生成的新任务沿用原 `task_kind` 与附件。

#### Scenario: 运行中打开报告

- **WHEN** 用户打开一个正在执行的 Agent-02 任务报告
- **THEN** 页面显示「运行中，自动刷新…」，事件流随任务推进自动出现新事件
- **AND** 任务结束后停止刷新，保留完整事件流

#### Scenario: 中断任务可重跑

- **WHEN** 任务因后端重启被标记为 `interrupted`
- **THEN** 任务卡提供「重新执行」，点击后克隆附件并重新进入执行
