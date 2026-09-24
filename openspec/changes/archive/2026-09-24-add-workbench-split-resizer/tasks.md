## 1. 共享件

- [x] 1.1 新增 `frontend/src/shared/components/SplitHandle.vue`：`v-model` 宽度 + `commit` 事件；鼠标拖动（window 上的 mousemove/mouseup）、键盘（←/→ ±16，Shift ±48，Home/End 到两端）、双击复位；`role="separator"` + `aria-orientation="vertical"` + `aria-valuenow|min|max` + `tabindex="0"`；拖动中 `body` 光标 `col-resize` 且正文不可选。验证：`npx vue-tsc --noEmit` 零错误、`npx eslint src/shared src/modules` 无新增
- [x] 1.2 宽度夹取：下限 220、上限 `min(560, 容器宽 − 360)`，并在挂载时对已存值夹取一次。验证：断言拖到最左停在 220、上限 `aria-valuemax` 报 560
- [x] 1.3 样式：8px 命中区 + 常态暖灰分隔线（可发现）+ hover / 拖动转墨色 + 聚焦焦点环 + `touch-action: none`。验证：`npm run lint:styles` 批 2 通过

## 2. 两个工作台接入

- [x] 2.1 `element-locator/ProjectWorkspace.vue`：栅格改 `var(--locator-tree-pane-w) auto minmax(0,1fr)`、移除左栏 `border-right`（避免两条线）、持有宽度状态（初值读 CSS 令牌 `--locator-tree-pane-w`）、`commit` 写 `app-split-locator-tree-w`。验证：拖动 +120 → 280→404px，刷新后仍 404px
- [x] 2.2 `case-manager/ProjectWorkspace.vue`：同上，token `--case-tree-pane-w`、key `app-split-case-tree-w`。验证：数值与元素定位逐项相同
- [x] 2.3 窄屏不渲染手柄（`v-if="isWide"`）。验证：1024px 视口下 `.split-handle` 不存在，栅格为单列 `716px`

## 3. 验证与关单

- [x] 3.1 模块门禁：`npx vue-tsc --noEmit` 零错误 · `npx eslint`（`ProjectTree.vue` 既有 1 条 warning，基线不增）· `npm run lint:styles` 批 1–4 全绿 · `npx vite build --mode development` 通过 · `npx vitest run tests/element-locator/p0` 30 用例全绿
- [x] 3.2 Chromium 断言（两页各跑一遍，结果逐项相同）：手柄存在且 `role=separator` / `aria-orientation=vertical` / `aria-valuenow=280` / `min=220` / `max=560` / `tabindex=0`；拖动 +120 → 404px（右栏 904→780）；刷新后仍 404px；拖到最左停在 220px 且右栏 964px ≠ 0；Home → 220、`→`×2 → 252（+32）且 `aria-valuenow` 同步；双击复位 280px；1024px 下无手柄；拖动期间 `body` 光标 `col-resize`；localStorage 两键各自记 280；0 控制台错误。证据：`temps/split-resizer-assert.json` + `temps/split-locator.png` / `temps/split-case.png`
- [x] 3.3 边界检查：`python tools/gen_arch_stats.py --check-boundaries` → ✅ 零违规
- [x] 3.4 文档同步：`doodle-craft` 的 `references/page-layout.md` §4.7.1 的「版式」行补上「左栏宽度可拖动（220–min(560, 容器宽−360)，键盘可达，双击复位，按模块记忆）」
