## 1. 分栏比例（P0）

- [x] 1.1 `ModelDebugPage.style.css`：`.md-split` 由 `minmax(0, 1fr) minmax(0, 2fr)` 改为 `minmax(0, 2fr) minmax(0, 1fr)`，对话栏占正文 1/3、配置区 2/3；同步更新注释。验证：样式源断言通过。
- [x] 1.2 高度与断点不动：`.md-chat-body` 仍为 `132vh` + 内部滚动，`@media (max-width: 1200px)` 单列回退保留。验证：同一份版式用例的其余断言继续通过。

## 2. 测试

- [x] 2.1 改测 `frontend/tests/ai-assistant/p0/useModelDebug.spec.ts`：describe 名称改为「对话栏占正文三分之一」，分栏断言改为 `minmax(0, 2fr) minmax(0, 1fr)`，并加一条「旧的 1fr : 2fr 不得再出现」的负向断言。验证：命令通过。
- [x] 2.2 高度断言保持不变（`132vh` + `overflow-y`、旧 `66vh` 不出现）。验证：同一命令通过（29 用例全绿）。

## 3. 门禁与复验

- [x] 3.1 只跑与改动相关的最小集：`npx vitest run tests/ai-assistant/p0/useModelDebug.spec.ts`。验证：全绿，未发起全量回归。
- [ ] 3.2 用户侧目视复验：刷新验收模型调试页，确认对话栏宽度约为上一版的一半（正文 1/3），高度与工具折叠不变。验证：用户确认。
