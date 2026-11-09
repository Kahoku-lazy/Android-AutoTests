## 1. 卡片皮肤

- [x] 1.1 模板：Agent 卡加 `:pin="false"` 与 `:style="{ '--agent-accent': agentCardAccent(index) }"`，标题上方加编号 `{{ String(index + 1).padStart(2, "0") }}`。验证：`vue-tsc` 通过。**验证结果**：tsc 0。
- [x] 1.2 脚本：新增 `AGENT_CARD_ACCENTS` 与 `agentCardAccent()`（模块色轮转）。验证：类型检查通过。**验证结果**：tsc 0。
- [x] 1.3 样式：`.agent-usage-card` 改 2px 墨线、2px 圆角、无阴影、无倾斜、`overflow: hidden`；`::before` 顶边 6px 色条；`::after` 右上角 52px 黄色四分之一圆；编号与标题字号 12/18。验证：`npm run build:check` 通过。**验证结果**：build 20.7s。

## 2. 验证

- [x] 2.1 `npx vue-tsc --noEmit`、`npm run build:check`、`npx vitest run tests/dashboard`、`npm run lint:styles`、`npm run lint:lines`。验证：全绿。**验证结果**：tsc 0；build 20.7s；2 文件 62 passed；批 2 通过；虚线 0 处。
- [ ] 2.2 目视：AI 用量右侧两张 Agent 卡的色条、黄圆、编号与数据两列。验证：用户确认。
