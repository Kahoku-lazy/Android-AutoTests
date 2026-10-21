## Why

上一版把线路卡放大到 600px、头像 101px，名称/职责在左上、配置按钮在底部右侧，与标注的布局不一致。标注要求改为「左侧大方形头像 + 右侧三行（名称 / 职责 / 配置）」的紧凑卡片，整体尺寸也要收回到约 360px 宽。

## What Changes

- 线路卡改为左头像、右三行的固定网格：头像约 176px 正方形；右侧列约 144px 宽，名称、职责、配置按钮三行纵向均匀分布。
- 「配置」按钮从 `DoodleNote` 底部操作区移入右侧第三行，不再占满卡片底部。
- 卡片整体约 368px 宽、208px 高；名称/职责字号收敛到能放进右列（约 18px / 15px）。
- 窄屏（≤720px）头像与右列降档到约 120px，避免内容溢出。
- 不改身份数据、配置按钮行为、页面其它区块与接口。

## 关联文档

- PRD-08 AI 助手（平台小助手看板布局）

## Capabilities

### New Capabilities

### Modified Capabilities

- `ai-assistant/assistant-board-layout`: 线路卡从「600px 宽、底部配置」改为「约 368px 宽、左头像 + 右三行（名称/职责/配置）」

## Impact

- `frontend/src/modules/ai-assistant/components/AgentRouteCard.vue`：模板结构与卡片尺寸/排版
- `frontend/src/modules/ai-assistant/index.vue`：卡片网格列宽同步
- `frontend/src/modules/ai-assistant/AGENTS.md`：布局说明同步
- `frontend/tests/`：按需补充布局断言
- 接口、路由、任务卡片功能不变
