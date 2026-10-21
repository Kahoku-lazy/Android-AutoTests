## 1. 头像 120px

- [x] 1.1 `AgentRouteCard.vue` 右侧列高度 176px → 120px，卡片宽度 368px → 312px；`index.vue` 网格列宽同步 312px。验证：浏览器实测头像约 120px、卡片约 312px。
- [x] 1.2 更新 `ai-assistant/AGENTS.md` 的尺寸说明为「卡片约 312px、头像约 120px」。验证：文档与实测一致。

## 2. 验证与关单

- [x] 2.1 相关单测通过：`npx vitest run tests/ai-assistant/p0/AgentRouteCard.spec.ts tests/ai-assistant/p0/task-list-route.spec.ts tests/shared/p0/sidebarNavConfig.spec.ts`。
- [x] 2.2 前端类型检查与构建通过：`npm run build:check`。
- [x] 2.3 运行前端门禁 `vue-frontend-check`；浏览器验证 1600/1100/640 三档头像 120px、无横向溢出，任务清单页不受影响。
- [x] 2.4 确认 `openspec validate "2026-10-21-assistant-avatar-120" --strict` 通过后归档。
