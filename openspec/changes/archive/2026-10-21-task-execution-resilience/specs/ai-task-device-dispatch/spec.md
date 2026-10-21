## REMOVED Requirements

### Requirement: 进程重启后恢复排队
**Reason**: 把服务重启打断的 running 任务记为 `failed`，会让基础设施问题伪装成用例失败，污染测试报告的通过率。
**Migration**: 由新增需求「重启后遗留任务记为中断并恢复排队」替代；已落库的历史 `failed` 行保持原样，不回填。

## ADDED Requirements

### Requirement: 重启后遗留任务记为中断并恢复排队
系统 SHALL 在服务进程启动时把遗留的 running 任务标记为 `interrupted`（已中断），MUST NOT 标记为 `failed`；恢复 MUST 写入中断说明与 `finished_at`，MUST 用该任务的模型调用事件合计回写 `cost_total`，然后按设备尝试启动各设备上最早的 pending 任务。

#### Scenario: 重启后遗留 running 变为已中断并拉起 pending
- **WHEN** 服务重启时某设备存在一条遗留 running 与一条 pending
- **THEN** 遗留 running 落 interrupted，`result` 说明服务重启导致中断
- **AND** 该 pending 可被调度为 running
