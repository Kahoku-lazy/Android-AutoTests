# 浮层规格 — 弹窗 / 抽屉 / 确认框

**以代码为准**：`frontend/src/style.css`（皮肤只声明在这里，模块不得各补私有皮肤）。令牌值见 [../tokens.md](../tokens.md)。

> **读法**：标「未覆盖」= 走 Element Plus 出厂值。

## 1. Dialog / Drawer 弹窗与抽屉

| 维度 | 实际规格 |
|------|----------|
| 圆角 | `--comp-dialog-radius`（`6px 10px 6px 10px`）|
| 描边 | `--comp-dialog-border`（`2.5px dashed var(--ink)`）|
| 背景 | `--comp-dialog-bg`（白）|
| 阴影 | `--comp-dialog-shadow`（`4px 4px 0 0 var(--ink)`）|
| 标题排版 / 内边距 | **未覆盖**（走 EP 默认；字族由 `--el-font-family` 统一）|

两者**同源同值**（皮肤只声明在 `style.css`）。约定：

- 含可编辑输入的弹层必须 `:close-on-click-modal="false"`；纯预览保持默认。
- 持本地状态且每次打开要重置的用 `destroy-on-close`。
- 挂载点在带 `transform` 的容器内时（如登录页便签卡）必须 `append-to-body`，否则遮罩会被困在局部容器。
- 弹窗内容**不设内部滚动**；表单弹窗单列、宽度 ≤ 520px。
- 禁自建遮罩；禁浏览器原生弹窗（`window.confirm` / `alert`）。

## 2. 确认框（ElMessageBox）

删除、清空一类不可逆操作统一走 `ElMessageBox`（`type` 默认 `warning`），或包成共享的 `ConfirmButton`（`doodle=true` 时渲染成 `DoodleBtn tone="danger"`，见 [general.md](general.md)）。

- 确认文案必须写清**影响面**（删什么、是否可撤销、进行中的任务是否受影响）。
- 危险动作的按钮用 `--app-marker-red` / `--app-status-danger-*`，不用 primary。
- **禁止** `window.confirm`。
