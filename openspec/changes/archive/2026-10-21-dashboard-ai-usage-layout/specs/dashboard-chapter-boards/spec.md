## ADDED Requirements

### Requirement: Platform ops chapter includes task count card

仪表盘「平台运营」章节 SHALL 按顺序展示在线设备、活跃智能体、运行中任务、任务数量、工作流五张 KPI 卡。任务数量卡的数据 MUST 取自当前用户可见任务的累计数量，MUST 保留整卡点击进入智能体页，MUST NOT 渲染独立「进入」按钮。该卡 MUST 同时展示今日任务数作为副标题。

#### Scenario: 平台运营五卡顺序

- **WHEN** 用户打开仪表盘并查看「平台运营」章节
- **THEN** 章节内按顺序出现「在线设备」「活跃智能体」「运行中任务」「任务数量」「工作流」五张卡，且「任务数量」不再出现在「AI 用量」章节

#### Scenario: 任务数量卡无独立进入按钮

- **WHEN** 用户查看「任务数量」卡
- **THEN** 卡内不存在「进入」按钮，点击整卡仍可进入智能体页
