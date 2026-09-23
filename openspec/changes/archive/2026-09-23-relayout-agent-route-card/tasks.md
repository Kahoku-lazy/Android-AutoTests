## 1. 卡片信息架构

- [x] 1.1 调整 `AgentRouteCard.vue`：去掉 `#header` 功能标题；身份区改为左头像 + 右三行（名称 /「职责：UI自动化」/ 连通状态）；头像正方形且 `aspect-ratio: 1`、高度随三行 stretch，去掉固定 48px。验证：卡片内无独立「控制设备」标题，三行选择器可定位
- [x] 1.2 收敛入口 `index.vue` 对 `label` 的传递（删除无用 prop 或改为职责常量），保持 `edit`/`test` 与 `can-manage` 行为不变。验证：`rg label AgentRouteCard` 与入口调用一致，无死 prop
- [x] 1.3 更新 `frontend/src/modules/ai-assistant/AGENTS.md` 看板卡片信息架构（头像+三行+底栏按键，职责文案）。验证：与实现一致且无独立标题带描述残留

## 2. 测试与门禁

- [x] 2.1 扩展 `frontend/tests/ai-assistant/p0/AgentRouteCard.spec.ts`：断言三行文案、无「控制设备」标题、`canManage` 时底栏有校验/配置、`canManage=false` 时无按键；保留连通三态用例。验证：`cd frontend && npx vitest run tests/ai-assistant/p0/AgentRouteCard.spec.ts`
- [x] 2.2 跑前端类型检查。验证：`cd frontend && npm run typecheck`
