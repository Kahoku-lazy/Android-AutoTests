## Why

线路卡头像当前约 178px，产品要求改为 120px；右列高度随之从 176px 收到 120px，卡片宽度同步收窄，保持「左头像 + 右三行」的紧凑比例。

## What Changes

- 头像由约 178px 改为约 120px（仍由右侧列高度驱动）。
- 右侧列高度 176px → 120px，宽度保持 144px；名称/职责/配置三行继续纵向均匀分布。
- 卡片宽度由 368px 收到约 312px，网格列宽同步。
- 窄屏仍为 120px 头像与 120px 右列，字号 15/13px，卡片占满容器。
- 不改身份结构、配置按钮行为、页面其它区块与接口。

## 关联文档

- PRD-08 AI 助手（平台小助手看板布局）

## Capabilities

### New Capabilities

### Modified Capabilities

- `ai-assistant/assistant-board-layout`: 头像从约 176px 改为约 120px，卡片宽度同步收到约 300–320px

## Impact

- `frontend/src/modules/ai-assistant/components/AgentRouteCard.vue`：右列高度、卡片宽度
- `frontend/src/modules/ai-assistant/index.vue`：卡片网格列宽
- `frontend/src/modules/ai-assistant/AGENTS.md`：尺寸说明
- 接口、路由、任务卡片功能不变
