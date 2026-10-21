## Why

平台小助手线路卡当前约 300px 宽、头像约 48px，放在页面背景上偏小。产品要求卡片宽度与头像大小各放大一倍，并让名称、职责、配置按钮、内边距等元素跟随头像一起放大。

## What Changes

- 线路卡宽度由 300px 调整到约 600px（窄屏仍收缩到容器宽度）。
- 头像由约 48px 放大到约 96px（仍按右侧文字区自然高度测量）。
- 名称、职责字号、文字行距、身份区间距、卡片内边距、配置按钮高度/字号/内边距同步放大，视觉比例跟随头像。
- 不改卡片身份结构、配置按钮行为、页面其它区块与接口。

## 关联文档

- PRD-08 AI 助手（平台小助手看板布局）

## Capabilities

### New Capabilities

### Modified Capabilities

- `ai-assistant/assistant-board-layout`: 线路卡宽度从 280–320px 改为约 560–620px，并约定头像与内部元素同步放大

## Impact

- `frontend/src/modules/ai-assistant/components/AgentRouteCard.vue`：卡片宽度、头像边框/占位字号、名称/职责字号与行距、内边距、配置按钮尺寸
- `frontend/src/modules/ai-assistant/index.vue`：卡片网格列宽同步到 600px
- `frontend/src/modules/ai-assistant/AGENTS.md`：布局说明同步
- `frontend/tests/`：按需补充尺寸/布局断言
- 接口、路由、任务卡片功能不变
