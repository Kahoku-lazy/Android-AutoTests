## 1. 2a · 等值令牌替换（57 文件 / 316 处）

- [x] 1.1 建等价映射（与 tokens.css 实际值逐条核对）：`4/8/16/24/32/48px → --app-space-{xs,sm,md,lg,xl,2xl}`；圆角 `4px 8px / 6px 10px / 8px 14px / 4px 10px 6px 8px` 也备好映射（实测 0 命中，跳过）
- [x] 1.2 写一次性脚本 `temps/tokenize-spacing.mjs`（dry-run 默认；跳过 tokens.css / 注释行 / 含引号行；只替换**逐字符等值**的项）
- [x] 1.3 dry-run 计数 → 落盘 → 复跑 dry-run **0 命中**（证明无残留候选）
  - 过程修正：脚本首版漏调 `writeFileSync`，复跑仍报 316 处 → 该复跑检查正是发现手段；补上落盘后复跑为 0
- [x] 1.4 抽样核对替换结果形态（`padding: var(--app-space-xs) 10px` 这类**部分替换**同样等值，正确）

## 2. 2b · 滚动策略显式化

- [x] 2.1 `style.css` 的页面布局一节补声明：① 页面整体滚动（`.doc-page`）② 视口固定 + 内层滚动（`.doc-page.wb-shell + .doc-body`），**二选一禁止混用**
- [x] 2.2 `#app` 增加 `overflow: auto` 兜底并注释说明生效条件（`.app-shell` 恰好 100vh 时不触发）
- [x] 2.3 明确**不做**逐页迁移，并产出迁移工作清单（见 3.3）

## 3. 门禁验证

- [x] 3.1 postcss 全量解析 `frontend/src` 的 95 个样式块 → **0 语法错误**（证明 316 处替换未破坏任何样式）
- [x] 3.2 Vite dev server（5173 运行中）返回改动样式：`DevicePoolView.style.css` / `ToolboxPanel.style.css` / `ReportDetail.vue?vue&type=style` / `style.css` → 全部 **200** 且含 `var(--app-space…)`
- [x] 3.3 产出迁移工作清单：`.doc-page` 13 处（wb-shell 8 / detail-page 3 / plain 1 / workflow-workbench 1）+ 内层滚动 39 处 / 30 文件；并登记"case-manager、element-locator 页面根本未用 `.doc-page`"
- [x] 3.4 `node node_modules/vue-tsc/bin/vue-tsc.js --noEmit` → 35 条既有错误**不变**
- [x] 3.5 `node tests/check-style-gates.mjs` → 通过
- [x] 3.6 等价性说明：替换只发生在与令牌值**完全相等**的字面量上，因此"改前=改后"是按构造成立的；工具链验证（postcss/浏览器/类型检查）用于排除**语法破坏**这一类风险
