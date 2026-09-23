## 1. 版式调整（P0）

- [x] 1.1 `ModelDebugPage.style.css`：`.md-split` 第二轨由 `minmax(320px, 420px)` 改为 `minmax(0, 2fr)`（第一轨保持 `minmax(0, 1fr)`），对话栏即占正文宽度 2/3。验证：`node tests/check-style-gates.mjs` 四批通过，且文件内不再出现 420px 上限。
- [x] 1.2 同文件：分栏堆叠媒体查询断点由 960px 上调至 1200px，低于该宽度改为上下单列、对话栏占满正文宽度。验证：样式源内 `.md-split` 的单列回退出现在 `max-width: 1200px` 块内。
- [x] 1.3 对话栏内部结构零改动：消息区 `max-height` + 独立滚动、输入框与清空 / 发送、思考过程默认展开逐条可折叠均保持原样。验证：现有 `useModelDebug.spec.ts` 的对话与折叠用例全部继续通过。
- [x] 1.4 同文件：消息滚动区 `.md-msgs` 高度上限由 `52vh` 抬到 `66vh`（屏幕高度 2/3），超出仍在该区内独立滚动、不撑长整页。验证：样式源断言 + 用户侧目视确认长对话仍只在消息区内滚动。

## 2. 测试

- [x] 2.1 `frontend/tests/ai-assistant/p0/useModelDebug.spec.ts` 新增版式用例：读样式源断言第二轨为第一轨 2 倍（`minmax(0, 1fr) minmax(0, 2fr)`）且不存在 420px 上限。验证：`npx vitest run tests/ai-assistant/p0/useModelDebug.spec.ts` 通过（26 用例）。
- [x] 2.2 同一用例断言窄屏单列回退位于 `max-width: 1200px`。验证：同上命令通过。
- [x] 2.3 再断言消息区 `max-height: 66vh` 且仍 `overflow-y: auto`、旧值 `52vh` 已消失。验证：`npx vitest run tests/ai-assistant/p0/useModelDebug.spec.ts` 通过（27 用例）。

## 3. 门禁与复验

- [x] 3.1 前端门禁：`node tests/check-style-gates.mjs` 四批通过；`npx vitest run`（全量 61 文件 / 352 用例）通过；`npm run typecheck` 无新增错误（存量 3 处 ProjectTree 报错属另一变更 `fix-frontend-type-errors` 范围）。验证：命令输出留档。
- [x] 3.2 零后端改动确认：`git status` 仅 `ModelDebugPage.style.css`、`useModelDebug.spec.ts` 与本变更目录；`apps/`、`engines/` 无改动；`openspec validate widen-model-debug-chat-panel --strict` 通过。
- [ ] 3.3 浏览器复验（真实前后端，用户侧）：前端 dev server 已在 5173 运行，HMR 已加载新样式；刷新验收模型调试页确认对话栏占正文 2/3。验证：用户目视确认。
