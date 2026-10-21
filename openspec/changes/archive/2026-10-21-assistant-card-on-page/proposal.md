## Why

平台小助手页的看板当前套了一层全宽 `.doc-section` 白底外框，内部只有一张紧凑线路卡，右侧留下大片白色空白；区块标题「平台小助手 / Assistant / N 个助手」又与页面页头重复。产品要求去掉这层外框与重复标题，让线路卡直接贴在页面背景上，并适当放大卡片。

## What Changes

- 移除平台小助手看板的 `.doc-section` 白底、描边、阴影与内边距，线路卡直接置于页面背景。
- 移除区块标题行「平台小助手 / Assistant」与右侧「N 个助手」计数；页面页头「平台小助手」保留。
- 线路卡宽度由自适应内容放宽到约 300px（窄屏收缩到容器宽度），不再被全宽外框包围。
- 任务清单页已有的 `.doc-section` 区块不受影响。

## 关联文档

- PRD-08 AI 助手（平台小助手看板布局）

## Capabilities

### New Capabilities

- `ai-assistant/assistant-board-layout`: 平台小助手线路卡直接贴页面背景的布局与卡片宽度

### Modified Capabilities

## Impact

- `frontend/src/modules/ai-assistant/index.vue`：移除 section/标题行，卡片网格直接放在 `.doc-body`
- `frontend/src/modules/ai-assistant/index.style.css`：删除 `duty-section`、`filter-count`，调整卡片网格
- `frontend/src/modules/ai-assistant/components/AgentRouteCard.vue`：卡片宽度
- `frontend/src/modules/ai-assistant/AGENTS.md`：布局说明同步
- `frontend/tests/`：按需补充布局/路由单测
- 接口、路由、任务卡片功能均不变
