## 1. 共享皮肤与工作台分栏骨架

- [x] 1.1 新增 `frontend/src/modules/element-locator/components/elementDetailSkin.css`：把 `LocatorFileView.vue` 现有的硬边按键皮肤与 `.sketch-sheet` 实线线型抽到该文件，作用域根类改为 `.element-detail-pane`。验证：`npm run lint:styles` 通过（批 1–4 全绿）
- [x] 1.2 `LocatorFileView.vue` 改为引用 1.1 的样式文件（主体挂 `.element-detail-pane`，删除组件内已抽出的规则），页面观感与行为不变。验证：`npx vite build --mode development` 通过；窄屏断言跑到该路由，删除键仍为 2px 实边 + 2px 圆角硬阴影
- [x] 1.3 `ProjectWorkspace.vue` 主体改为左右两栏：左栏挂 `LocatorTree`，右栏挂 `.element-detail-pane` 容器。验证：构建通过；1500px 视口下计算样式 `grid-template-columns: 320px 872px`
- [x] 1.4 右栏在未选中页面时渲染引导空态（共享 `EmptyState`），选中时渲染 `LocatorFilePanel`。验证：进入工作台右栏显示「从左侧选择一个页面」；点页面后右栏出现元素表（13 条 / 第 1 / 2 页）

## 2. 目录树紧凑呈现与落点时机

- [x] 2.1 `LocatorTree.style.css`：行默认去描边（`2px solid transparent` 占位，不出行高跳动），悬停给底色，选中行给 2px 墨框 + 硬阴影 + 底色。验证：行默认 `border-top-color` 计算为 `rgba(0, 0, 0, 0)`
- [x] 2.2 层级表达：`indent` 提升到 18px，`.el-tree-node__children` 左边界 `2px dotted var(--color-orange-76)` 引导线。验证：子层容器计算 `border-left-style: dotted` / `width: 2px`
- [x] 2.3 目录行尾随直接子项数，子项为 0 时显示「空」；页面行的进入指示紧贴名称。验证：「测试目录」行文本为「📂 测试目录 空」；进入指示与名称右边缘距离 = 8px（< 24px）
- [x] 2.4 项目根落点区改为按需出现：仅在批量选择模式、触摸拖拽态或拖拽起手后渲染（新增 `dragging` 状态），落点判定函数与端点不动。验证：默认 0 个落点区元素 → 进入批量模式 1 个 → 退出后 0 个

## 3. 工作台页头概况与窄屏退化

- [x] 3.1 `ProjectWorkspace.vue` 页头副标题改为内容概况。验证：页头显示「2 个目录 · 13 个页面」
- [x] 3.2 窄屏退化：以 `matchMedia("(min-width: 1280px)")` 判定，宽屏写本地选中态、窄屏 `router.push` 到 `/files/:fileId`，并监听视口变化。验证：1024px 下工作台单栏且无右栏元素表（`grid-template-columns: 716px`）；点页面后地址变为 `/elements/projects/android/files/54`
- [x] 3.3 切换选中页面不重建目录树。验证：`window.__treeEl` 同一性为 true；切换前后各节点 `aria-expanded` 序列一致

## 4. 验证与关单

- [x] 4.1 模块门禁：`npx vue-tsc --noEmit` 零错误 · `npm run lint:styles` 批 1–4 通过 · `npx eslint src/modules/element-locator` 零输出 · `npx vite build --mode development` 通过 · `npx vitest run tests/element-locator/p0` 4 文件 30 用例全绿
- [x] 4.2 Chromium 断言四项新要求：并置可点（URL 不变、右栏换内容、面包屑三节）· 行默认无描边 · 目录计数与「空」· 落点按需出现；0 控制台错误。证据：`temps/locator-relayout-assert.json` + 三张截图
- [x] 4.3 边界检查：`python tools/gen_arch_stats.py --check-boundaries` → ✅ 零违规
- [x] 4.4 文档同步：把树栏规格登记回 `doodle-craft` 的 `references/page-layout.md`（新增 §4.7.1，并修正 §4.6 已过时的「截图 + 元素树并排」措辞）。验证：手册出现 §4.7.1 全表
