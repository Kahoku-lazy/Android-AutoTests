## 1. 行皮肤与结构对齐

- [x] 1.1 `ProjectTree.vue` 行由 grid 改 flex，逐属性对齐 `.locator-row`：`border: 2px solid transparent`、透明底、`border-radius: var(--app-radius-md)`、`padding: var(--app-space-xs) var(--app-space-sm)`、悬停底色、选中 `border-color + --app-shadow-sm + 底色`。验证：对比断言两页同值 —— 默认描边 `rgba(0, 0, 0, 0)`、圆角 `6px`、内边距 `4px 8px`、行高 `34px`、选中 `2px` 墨框 + `rgba(0,0,0,0.04) 2px 2px 0 0`
- [x] 1.2 进入指示从行尾移到名称右侧（`.explorer-row__enter`，「进入 ›」），删除行尾 `▾` / `→` 与 `.explorer-row__hint` 规则。验证：行文本为「📄 临时用例表 进入 › 09-24 11:10」，与元素定位的「📄 … 进入 ›」同构
- [x] 1.3 目录计数改同口径：0 显示「空」，否则显示数量（新增 `childCountLabel`）。验证：空目录行文本为「📂 临时空组 空」，与元素定位「📂 测试目录 空」一致

## 2. 层级与树容器对齐

- [x] 2.1 恢复 el-tree 原生展开箭头（删除两条 `display: none` 规则），子层容器左边界补引导线。验证：两页 `border-left-style = dotted` / `2px` / `rgb(216, 210, 196)` 完全一致
- [x] 2.2 树容器内边距与行距对齐：`.explorer-body` 取 `var(--app-space-sm)`、节点内容下内边距取 `var(--app-space-xs)`。验证：行高与元素定位同为 34px

## 3. 工具栏对齐

- [x] 3.1 去掉常驻静态「项目根 / 全部」面包屑（批量模式的「已选 N 个文件」保留）、去掉工具栏浅色底、内边距改取令牌。验证：工具栏文本为「+ 新建目录 + 新建文件 选择」，不含「项目根」
- [x] 3.2 `.ex-btn` 补齐 hover 左上位移、`:disabled` 半透明 + 不位移、危险态红底 + 浅色字，并加 `prefers-reduced-motion` 降级。验证：两页按钮 hover `transform` 均为 `matrix(1, 0, 0, 1, -1, -1)`

## 4. 验证与关单

- [x] 4.1 模块门禁：`npx vue-tsc --noEmit` 零错误 · `npx eslint src/modules/case-manager` 仅剩既有 1 条 warning · `npm run lint` 基线不增 · `npm run lint:styles` 批 1–4 全绿 · `npx vite build --mode development` 通过
- [x] 4.2 Chromium 对比断言（临时项目「临时-对齐断言」，含 1 个有子项目录 + 1 个空目录 + 1 个文件；跑完即删，`DELETE` 200）：两页在默认描边、描边宽度、圆角、内边距、行高、引导线（样式 / 宽度 / 颜色）、选中态、按钮 hover 位移、空目录文案九项上**逐值相同**；悬停底色与选中底色为模块色差异（预期）；工具栏文案为业务动作差异（预期）。证据：`temps/align-workbench-assert.json` + `temps/align-locator.png` / `temps/align-case.png`
- [x] 4.3 边界检查：`python tools/gen_arch_stats.py --check-boundaries` → ✅ 零违规
- [x] 4.4 文档同步：`doodle-craft` 的 `references/page-layout.md` §4.7.1 新增「两模块逐项同源」规格行与「登记的数据差异」行
