## Why

对话页现在看不出「这句话是什么时候说的」：消息表有 `created_at`，但接口没返回，气泡自然没有时刻。运行日志则是一个平面列表，和参考图（手绘虚线卡 + 顶部胶带）差得远。需求方要求：日志按「一轮一张卡」做成参考图的样式（不要倾斜），日志卡与对话气泡都要有时间戳。

## What Changes

- 对话轮询接口的每条消息增加 `created_at`（本地时间 ISO 8601，带 `+08:00`）。日志列表的 `created_at` 同样统一成本地 ISO 字符串。
- 对话气泡下方显示该条消息的时刻（`HH:mm`，次级色，与气泡同侧对齐）。
- 运行日志从「一个面板里的行列表」改为「一轮一张虚线卡」：卡片顶部居中一条胶带、外框 `1.5px` 虚线（该助手笔色）、硬偏移阴影、**不倾斜**；卡内首行是时间戳 + 右侧「查看 / 还在写」，第二行是一句话结果。
- 日志卡移到**左栏、对话栏下面**（与「这一栏」同列）：展开时左栏 `240px → clamp(320px, 30%, 420px)`、对话列等量收窄，收起回 240px；日志不再把消息往下顶，也不再占对话区里那块用不上的空白。
- 虚线准入清单增加 `ThreadLogPanel.vue`（第三个虚线落点），并同步模块 AGENTS、doodle-craft 技能与 `check-dashed-whitelist.mjs` 的 OWNERS。
- 面板不再自己描边：有边界的实体是卡，面板只做分区与标题。

## 关联文档

- 规格：`openspec/specs/ai-assistant-test-chat`、`assistant-thread-log`。
- 视觉：`.agents/skills/doodle-craft/references/components/assistant-marker-card.md` §5 / §5.2。
- 前置变更：`assistant-thread-logs`（日志接口与入口已落地）。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- `ai-assistant-test-chat`: 每条消息带时间，气泡显示时刻。
- `assistant-thread-log`: 日志列表的每一轮给出时间；日志卡按参考图呈现，进行中的一轮没有时间。

## Impact

- 后端：`backend/apps/ai_assistant/services/assistant_threads.py`（消息与日志行都出本地 ISO 时间）、`views_drf.py`（消息列表改走 service 的行整理）。
- 前端：`modules/ai-assistant` 的 `chat.vue`（气泡时间）、`components/ThreadLogPanel.vue`（一轮一卡 + 胶带 + 时间）、`helpers/time-label.ts`（时间格式）、`types.ts`。
- 门禁：`frontend/tests/check-dashed-whitelist.mjs` 的 OWNERS 增加一个文件。
- 测试：接口断言消息带时间、日志行带时间；前端断言气泡与日志卡都渲染时间、日志卡带虚线外框与胶带。
