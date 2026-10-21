## 1. 看板去外框

- [x] 1.1 `index.vue` 移除 `.doc-section.duty-section` 包裹与区块标题行（平台小助手 / Assistant / N 个助手），把 `ErrorState` 与 `.route-card-grid` 直接放到 `.doc-body`。验证：页面 DOM 中看板不再有 `.doc-section`，也不出现「Assistant」「个助手」文案；浏览器打开 `/ai-assistant/agents` 卡片直接贴页面背景。
- [x] 1.2 删除 `index.style.css` 中失去消费者的 `.duty-section`、`.filter-count` 规则，保留 `.ai-workbench .doc-section__header` 供任务清单页使用。验证：`rg "duty-section|filter-count" frontend/src` 无匹配（AGENTS 文档除外）；任务清单页区块样式正常。

## 2. 卡片尺寸

- [x] 2.1 `AgentRouteCard.vue` 的 `.route-card` 宽度改为 `300px`、`max-width: 100%`；`index.vue` 的 `.route-card-grid` 列宽改为 `minmax(min(100%, 300px), max-content)`。验证：桌面卡片宽度约 300px，窄屏收缩且无横向溢出。
- [x] 2.2 更新 `ai-assistant/AGENTS.md` 的看板布局说明（去外框、无区块标题、卡片约 300px）。验证：文档不再写 `.duty-section` 区块标题带。

## 3. 验证与关单

- [x] 3.1 相关单测通过：`npx vitest run tests/ai-assistant/p0/AgentRouteCard.spec.ts tests/ai-assistant/p0/task-list-route.spec.ts tests/shared/p0/sidebarNavConfig.spec.ts`。
- [x] 3.2 前端类型检查与构建通过：`npm run build:check`。
- [x] 3.3 运行前端门禁 `vue-frontend-check`；浏览器验证 `/ai-assistant/agents` 在 1600/1100/640 三档无外框、无横向溢出，任务清单页不受影响。
- [x] 3.4 确认 `openspec validate "2026-10-21-assistant-card-on-page" --strict` 通过后归档。
