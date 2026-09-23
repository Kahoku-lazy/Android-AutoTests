## 1. 首屏约束（P0）

- [x] 1.1 `ModelDebugPage.style.css`：`.md-chat` 增加 `max-height: calc(100vh - var(--app-topbar-h, 96px) - 72px)`（面板整块不超首屏）。验证：样式源断言通过。
- [x] 1.2 同文件：`.md-chat-body` 保留 `height: 66vh`，增加 `flex: 0 1 auto; min-height: 0`（可被压缩）；`.md-chat > .md-section-title / .md-note / .md-chat-input` 设为 `flex: none`（不被压扁）。验证：样式源断言通过。
- [x] 1.3 宽度、断点、工具折叠与消息区滚动规则不变。验证：原有版式与折叠用例继续通过。

## 2. 测试

- [x] 2.1 改测 `frontend/tests/ai-assistant/p0/useModelDebug.spec.ts`：新增「对话栏整体不超出首屏，且只允许消息区被压缩」用例（面板 `max-height` 表达式、消息区 `min-height: 0`、输入区与标题 `flex: none`）。验证：命令通过（30 用例）。
- [x] 2.2 既有断言（宽度 1fr : 2fr、断点 1200px、消息区 66vh + 内部滚动、旧值 420px/132vh 不出现）全部保留。验证：同一命令通过。

## 3. 门禁与复验

- [x] 3.1 只跑与改动相关的最小集：`npx vitest run tests/ai-assistant/p0/useModelDebug.spec.ts`（30 用例全绿）+ `npx prettier --check` 被改样式文件（通过）。未发起全量回归。
- [ ] 3.2 用户侧目视复验：刷新验收模型调试页，确认不滚动即可看到输入框与「发送」，且窗口拉矮后仍不出首屏。验证：用户确认。
