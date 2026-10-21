## MODIFIED Requirements

### Requirement: Dashboard execution chart uses agent task cards

系统 MUST 用当前用户可见智能体下的 `AITask` 填充仪表盘 `charts.execution`。近 7 个自然日 MUST 以 `created_at` 分桶；成功桶 MUST 计入 `status` 为 `completed` 或 `success` 的卡片，失败桶 MUST 计入 `status` 为 `failed` 的卡片。MUST NOT 再返回执行引擎下线后的恒零序列作为该图的业务含义。

#### Scenario: Two successful cards appear on create day

- **WHEN** 用户在某日新建两张状态为成功的助手任务卡并打开仪表盘
- **THEN** 该日成功柱为 2、失败柱为 0
- **AND** 其它日期无对应卡片时为 0
