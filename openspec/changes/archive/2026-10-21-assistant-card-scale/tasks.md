## 1. 卡片与头像放大

- [x] 1.1 `AgentRouteCard.vue` 的 `.route-card` 宽度改为 600px，内边距 24px，身份区 gap 16px；`index.vue` 网格列宽同步到 600px。验证：桌面卡片宽度约 600px，窄屏仍收缩。
- [x] 1.2 名称/职责字号放大一倍、行高 1.4、文字间距 12px；头像边框 3px、emoji 占位字号 2 倍；配置按钮在 `.route-card` 作用域内放大到 48px 高、24px 横向内边距、2 倍字号。验证：浏览器实测头像约 96px，名称/职责/按钮明显放大且不溢出。

## 2. 验证与关单

- [x] 2.1 相关单测通过：`npx vitest run tests/ai-assistant/p0/AgentRouteCard.spec.ts tests/ai-assistant/p0/task-list-route.spec.ts tests/shared/p0/sidebarNavConfig.spec.ts`。
- [x] 2.2 前端类型检查与构建通过：`npm run build:check`。
- [x] 2.3 运行前端门禁 `vue-frontend-check`；浏览器验证 1600/1100/640 三档卡片宽度、头像尺寸与无横向溢出，任务清单页不受影响。
- [x] 2.4 更新 `ai-assistant/AGENTS.md` 的卡片尺寸说明，确认 `openspec validate "2026-10-21-assistant-card-scale" --strict` 通过后归档。
