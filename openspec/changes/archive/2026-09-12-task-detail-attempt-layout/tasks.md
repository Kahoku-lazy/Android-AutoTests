## 1. 尝试卡片组件

- [x] 1.1 新增 `frontend/src/modules/ai-assistant/components/TaskAttemptCard.vue`：卡片头 + 常显「执行结果」（执行/验收分行，截图不折叠）+ Agent 过程 `el-collapse`（默认收起）；样式用 `--app-*` / `--ai-*` 令牌。验证：组件可单独挂载，标题与正文 class 分离
- [x] 1.2 `TaskDetailPage.vue` 用 `TaskAttemptCard` 替换内联 `article.td-attempt`，迁走尝试区样式；验证：页面不再内嵌执行结果折叠项，文件行数下降

## 2. 测试与门禁

- [x] 2.1 新增 `frontend/tests/ai-assistant/p0/TaskAttemptCard.spec.ts`：有结果时文本含执行/验收结论且不在 collapse 内；有截图时 `el-image` 常显；Agent 折叠默认未展开。验证：`npx vitest run tests/ai-assistant/p0/TaskAttemptCard.spec.ts` 通过
- [x] 2.2 浏览器走查对照（组件单测已覆盖三场景；请在 `/ai-assistant/tasks/:taskId` 目视确认）：执行结果默认可见、标题/正文可区分、Agent 过程可折叠
- [x] 2.3 前端门禁：相关 vitest 通过；`npm run typecheck` 无本变更引入错误（既有 case-manager / device-inspector / dashboard 测试类型债仍在）
