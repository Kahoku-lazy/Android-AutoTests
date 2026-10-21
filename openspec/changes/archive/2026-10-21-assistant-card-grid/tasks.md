## 1. 卡片结构

- [x] 1.1 `AgentRouteCard.vue` 把「配置」按钮从 `#actions` 槽移入 `.route-identity-text`，作为名称、职责之后的第三行；去掉 `#actions` 模板。验证：卡片 DOM 中配置按钮位于右列内，不再有底部整行操作区。
- [x] 1.2 右列固定 144×176px、`space-between`；名称 18px、职责 15px、配置按钮占满右列宽度；头像随右列高度为 176px。验证：浏览器实测头像约 176px，三行自上而下为名称/职责/配置。
- [x] 1.3 卡片宽度 368px、内边距 16px；`index.vue` 网格列宽同步到 368px；≤720px 时右列降档 120px、名称 15px、职责 13px。验证：1600/1100/640 三档无横向溢出，640 宽头像约 120px。

## 2. 验证与关单

- [x] 2.1 相关单测通过：`npx vitest run tests/ai-assistant/p0/AgentRouteCard.spec.ts tests/ai-assistant/p0/task-list-route.spec.ts tests/shared/p0/sidebarNavConfig.spec.ts`。
- [x] 2.2 前端类型检查与构建通过：`npm run build:check`。
- [x] 2.3 运行前端门禁 `vue-frontend-check`；浏览器验证 1600/1100/640 三档布局、头像尺寸与无横向溢出，任务清单页不受影响。
- [x] 2.4 更新 `ai-assistant/AGENTS.md` 的布局说明，确认 `openspec validate "2026-10-21-assistant-card-grid" --strict` 通过后归档。
