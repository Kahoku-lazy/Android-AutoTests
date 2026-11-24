# ai-assistant · 样式与红线

> 归属模块：`frontend/src/modules/ai-assistant` ｜ 类型：模块功能开发说明
> 代码真相源：`frontend/src/modules/ai-assistant/tokens.css`、`helpers/marker.ts`、`frontend/src/shared/styles/tokens.css`、`frontend/tests/check-dashed-whitelist.mjs`
> 上级约束：根 `AGENTS.md`、`frontend/AGENTS.md` ｜ 模块索引：`frontend/AGENTS.md`

## 样式

- 虚线只允许四个落点：`AssistantCard.vue`（助手颜料片外框 2.5px、卡内动作 1.5px；工作流便签卡外框 1.5px 浅墨）、`AssistantLanePanel.vue`（面板框与两栏分隔，1.5px 浅墨）、`ThreadLogPanel.vue`（日志卡 1.5px，笔色 70%）、`shared/components/SectionDivider.vue`（页面分区横线，1.5px 浅墨，**现在 `index.vue` 里用它分隔助手区与工作流区**）。四者都已登记在 `check-dashed-whitelist.mjs` 的 OWNERS 里；配置弹窗、气泡、输入框、按钮一律实线。
- 笔色色值只在 `tokens.css`；`helpers/marker.ts` 只映射变量名。深到浅的浅底 / 渐变由消费它的组件用 `color-mix` 现算，**不要**在 `.ai-assistant-page` 上预置（不会随卡片笔色重算）。
- 规格与反模式见 `.agents/skills/doodle-craft/references/components/assistant-marker-card.md`。

## 红线

- **禁止**把虚线或笔色渐变扩散到其它模块、弹窗、表格。
- **禁止**在卡片上补工具清单、模型名、编号、状态角标——卡片只放名称、头像或笔色圆、Agent 配置名。
- **禁止**用 `--c-ai` 冒充笔色（模块色只给侧栏与页头默认图标）。
- 智能体看板、对话工作流、配置页已随重设计下线，不再有 `/ai-assistant/agents` 与 `/ai-assistant/agent/:id`。
- `api/agents.ts` 在任务清单侧**已无引用**（`task-list` 零 `ai-assistant` import、`frontend/src` 内 `TASK_KIND_` 命中 0），删它或清它不必再先改 `task-list`；其死函数已随退役清扫删除。助手名片与测试对话走 `api/assistants.ts`，不要塞回 `agents.ts`。

## 快速验证

```bash
cd frontend
npx vitest run tests/ai-assistant
npx vue-tsc --noEmit
node tests/check-style-gates.mjs
```
