## ADDED Requirements

### Requirement: Chapter headers omit summary chips

仪表盘章节头 MUST NOT 再呈现 chip 摘要行。「平台运营」章节头 MUST NOT 展示设备、智能体、任务、工作流汇总 chip；「AI 用量」章节头 MUST NOT 展示「角色·累计」「角色·今日」或语义等价的分角色 Token 摘要 chip。章节层级 MUST 由模块色方标、英文 eyebrow 与中文标题表达，MUST NOT 依赖灰色圆角 pill。`ai_usage.by_role` 仍可保留在统计接口中，但 MUST NOT 用于章节头 chip。「测试资产」章节头右侧的用例数 chip 不受本条约束。

#### Scenario: 平台运营章节头不再有汇总 chip

- **WHEN** 用户打开仪表盘并查看「平台运营」章节头
- **THEN** 章节头只有模块色方标、英文 eyebrow、中文标题与描述，不存在设备、智能体、任务或工作流数量的 chip

#### Scenario: AI 用量章节头不再有角色 chip

- **WHEN** 用户打开仪表盘并查看「AI 用量」章节头
- **THEN** 页面不存在「角色·累计」「角色·今日」或语义等价的分角色 Token 摘要 chip

#### Scenario: 测试资产用例 chip 保留

- **WHEN** 用户查看「测试资产」章节头右侧
- **THEN** 用例数量 chip 仍然可见

## REMOVED Requirements

### Requirement: Section summaries use chips instead of raw gray meta lines

**Reason**: 平台运营汇总 chip 与 AI 分角色 Token chip 同下方 KPI 卡和数据重复，产品要求删除这两条章节头摘要行。

**Migration**: 平台运营汇总改看下方 KPI 卡；分角色 Token 数据仍保留在 `ai_usage.by_role` 接口字段中，但不再在章节头以 chip 展示。测试资产章节的用例 chip 保留。
