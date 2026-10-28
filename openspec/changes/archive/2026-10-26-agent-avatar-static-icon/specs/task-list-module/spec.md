## MODIFIED Requirements

### Requirement: AI assistant keeps only assistant and route configuration

`apps.ai_assistant` MUST 只保留 `AIAgent`、线路/身份配置页、`/api/ai/agents/*`、内置固定头像与配对引擎配置。它 MUST NOT 再提供任务列表、任务详情、任务创建、调度、重跑、关闭、删除、清空、任务费用或任务用量接口/页面，也 MUST NOT 再提供头像上传接口。

#### Scenario: Assistant page only configures routes

- **WHEN** 用户打开平台小助手页
- **THEN** 页面只展示助手与线路/身份配置，不出现任务列表、任务详情或新建任务入口
