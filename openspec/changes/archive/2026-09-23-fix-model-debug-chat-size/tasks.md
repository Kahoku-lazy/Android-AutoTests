## 1. 尺寸回退（P0）

- [x] 1.1 `ModelDebugPage.style.css`：`.md-split` 恢复为 `minmax(0, 1fr) minmax(0, 2fr)`（对话栏 2/3），注释同步改回。验证：样式源断言通过，且新增「不再出现 `minmax(0, 2fr) minmax(0, 1fr)`」的负向断言。
- [x] 1.2 同文件：`.md-chat-body` 固定高度由 `132vh` 改为 `66vh`（保留 `overflow-y: auto`）。验证：样式源断言通过，且新增「不再出现 `height: 132vh`」的负向断言。

## 2. 测试

- [x] 2.1 改测 `frontend/tests/ai-assistant/p0/useModelDebug.spec.ts`：describe 名改回「对话栏占正文三分之二」、分栏断言改回 `1fr : 2fr`；高度断言改为 `66vh` 固定高并加两条负向断言。验证：`npx vitest run tests/ai-assistant/p0/useModelDebug.spec.ts` 通过（29 用例全绿）。

## 3. 门禁与复验

- [x] 3.1 只跑与改动相关的最小集：`npx vitest run tests/ai-assistant/p0/useModelDebug.spec.ts`。验证：全绿，未发起全量回归。
- [ ] 3.2 用户侧目视复验：刷新验收模型调试页，确认对话区高度回到约 2/3 屏（上一版的一半）、宽度为正文 2/3。验证：用户确认。
