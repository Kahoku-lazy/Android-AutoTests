## Why

任务详情右侧「尝试」卡片已有 Executor / Verifier 过程与执行结果，但全部塞进多层折叠，标题与正文挤成一串，验收结论还要展开才能看到。用户需要先看结论、再按需看过程。

## What Changes

- 每轮尝试的「执行结果」（执行/验收结论、验证截图）改为常显区块，不再放进折叠。
- 尝试卡片区分标题与正文：区块标题独立成行；执行与验收拆成两行；Agent 过程仍可折叠，但展开后标题与内容层级清晰。
- 不改任务详情 API、轮询、步骤清单与底栏最终结果。

## 关联文档

- ARCH：`dev_docs/03-设计与架构/ARCH-00-平台总体架构.md`（`ai_assistant` 任务详情职责）
- 接口：`dev_docs/05-开发与测试/接口文档/API-AI助手.md`（本变更不改接口契约）
- UI：前端 Doodle Craft（`doodle-craft` skill / `tokens.css`）；本变更不改主题令牌
- PRD：无独立「任务详情尝试区」PRD；需求以对话确认的排版与常显规则为准

## Capabilities

### New Capabilities

- （无）

### Modified Capabilities

- `ai-task-publishing`: 补充任务详情逐步尝试区的展示规则（执行结果常显、过程可折叠、标题与正文可区分）

## Impact

- 前端：`frontend/src/modules/ai-assistant/TaskDetailPage.vue`（必要时拆出尝试卡片组件以控制文件体积）
- 测试：`frontend/tests/ai-assistant/` 中与任务详情展示相关的用例
- 后端 / API：无
