## MODIFIED Requirements

### Requirement: Chapter headers expose hierarchy with doodle cues

每个章节头 SHALL 包含：模块色方标（或等价图标块）与中文标题（可用 marker 高亮）。章节头 MUST NOT 出现英文 eyebrow（如 `Platform Ops`），MUST NOT 出现描述行（副标题）。MUST NOT 仅依赖灰色圆角 pill 作为主层级信号。

#### Scenario: Chapter head is scannable

- **WHEN** 用户浏览任一章节头
- **THEN** 可见彩色方标与中文标题，且不存在英文 eyebrow 与描述行
- **AND** 章节容器带实线描边与硬色偏移阴影（钉板语义）

### Requirement: Chapter headers omit summary chips

仪表盘章节头 MUST NOT 再呈现 chip 摘要行。「平台运营」章节头 MUST NOT 展示设备、智能体、任务、工作流汇总 chip；「AI 用量」章节头 MUST NOT 展示「角色·累计」「角色·今日」或语义等价的分角色 Token 摘要 chip。章节层级 MUST 由模块色方标与中文标题表达，MUST NOT 依赖灰色圆角 pill。`ai_usage.by_role` 仍可保留在统计接口中，但 MUST NOT 用于章节头 chip。「测试资产」章节头右侧的用例数 chip 不受本条约束。

#### Scenario: 平台运营章节头不再有汇总 chip

- **WHEN** 用户打开仪表盘并查看「平台运营」章节头
- **THEN** 章节头只有模块色方标与中文标题，不存在英文 eyebrow、描述行，也不存在设备、智能体、任务或工作流数量的 chip

#### Scenario: AI 用量章节头不再有角色 chip

- **WHEN** 用户打开仪表盘并查看「AI 用量」章节头
- **THEN** 页面不存在「角色·累计」「角色·今日」或语义等价的分角色 Token 摘要 chip

#### Scenario: 测试资产用例 chip 保留

- **WHEN** 用户查看「测试资产」章节头右侧
- **THEN** 用例数量 chip 仍然可见
