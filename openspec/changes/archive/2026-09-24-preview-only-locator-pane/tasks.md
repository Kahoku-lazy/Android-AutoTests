## 1. 只读预览组件

- [x] 1.1 新增 `frontend/src/modules/element-locator/components/LocatorPagePreview.vue`：props `file`、emit `open`；只消费 `usePageElements` 的读状态，渲染七列只读表 + 页脚「预览前 6 条 · 共 N 条」+「进入页面编辑」入口。验证：`npx vue-tsc --noEmit` 零错误、`npm run lint:styles` 批 1–4 通过
- [x] 1.2 预览三态用共享件：加载 `SkeletonCard`、失败 `ErrorState`（可重试）、该页无元素 `EmptyState`（带进入编辑按钮）。验证：`npx vite build --mode development` 通过
- [x] 1.3 组件不导入任何写函数与 `EditableCell`。验证：Chromium 断言预览期间写请求为 `[]`（空数组）

## 2. 工作台右栏切换为预览

- [x] 2.1 `ProjectWorkspace.vue` 右栏由 `LocatorFilePanel` 换成 `LocatorPagePreview`，接 `open` 事件跳 `/elements/projects/:code/files/:fileId`。验证：右栏无「删除」键；断言入口跳转到 `/elements/projects/android/files/58`
- [x] 2.2 目录树右键删除保持可用（`@delete-file` 仍走 `removeFile`）。验证：`LocatorTree.vue` 的 `deleteFile` 事件链未变，`ProjectWorkspace` 的 `onDeleteFile` 仍在绑定
- [x] 2.3 右栏保留 `.element-detail-pane` 作用域，入口按键几何与详情页一致。验证：断言 `border-width: 2px` / `border-style: solid` / `border-radius: 2px` / `box-shadow: rgb(30, 30, 36) 2px 2px 0 0`

## 3. 验证与关单

- [x] 3.1 模块门禁：`npx vue-tsc --noEmit` 零错误 · `npm run lint:styles` 通过 · `npx eslint src/modules/element-locator` 零输出 · `npx vite build --mode development` 通过 · `npx vitest run tests/element-locator/p0` 4 文件 30 用例全绿
- [x] 3.2 Chromium 断言只读：双击单元格不出现输入框与编辑态 · 勾选框 0 / 开关 0 / 输入框 0 / 工作台工具条按键 0 · 预览期间写请求 `[]` · 页脚「预览前 6 条 · 共 13 条（还有 7 条未显示）」· 入口跳详情页后可编辑（21 个输入框、10 个测试点开关、新增/删除按键齐备）· 0 控制台错误
- [x] 3.3 边界检查：`python tools/gen_arch_stats.py --check-boundaries` → ✅ 零违规
- [x] 3.4 文档同步：`doodle-craft` 的 `references/page-layout.md` §4.7.1「右栏表格」行补上「只读预览，编辑在叶子整页」
