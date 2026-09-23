## Why

元素定位 Android 页面叶子的文件详情页刚改成全宽表格，但控件仍是 Element Plus 默认：删除键是 `el-button danger plain`，元素表未开 SketchTable 表纸。同一平台里侧栏「退出」与设备管理表纸已经是硬边涂鸦语言，该页观感脱节。本次只改这一页的按键与表格皮肤，对齐已登记的硬边几何与 `AppTable` 表纸。

## What Changes

- 文件详情页（`.locator-workbench.file-view`）把「需要硬边外观」的按键（至少包含「删除」）改成与侧栏「退出」同一套几何：2px 墨色实边、2px 近直角、`2px 2px 0 0 var(--ink)` 硬阴影，hover 左上 1px、阴影增至 3px。删除键底色走危险红令牌，浅色文字，对比度 ≥ 4.5:1。
- 面包屑「返回目录」芯片保持现有 `WorkbenchCrumbs` 硬边回退，不另造第二套返回键。
- 页面元素表启用共享 `AppTable` 的 SketchTable 皮肤（`accent="var(--c-element)"`），外框墨色**实线**表纸 + `--c-element` 硬阴影，与设备管理页同语言、仅模块强调色不同。
- 将 `.locator-workbench.file-view` 登记为硬边按键皮肤的新承载页；共享件 `DoodleBtn` / `FilterTabs` / `ErrorState` 与全局 `tokens.css` / `style.css` / `workbench-theme.css` 默认皮肤 MUST NOT 被改写。
- 列集合、行内别名/测试点编辑、无截图无筛选等既有工作台行为不变。

**BREAKING**：无。

## 关联文档

- 需求编号：`PRD-04-元素定位`

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `element-locator-page-workbench`: 文件详情工作台的按键与表格必须呈现硬边涂鸦皮肤与 SketchTable 表纸。
- `frontend-doodle-button`: 硬边按键承载页清单增加元素定位文件详情页。
- `frontend-doodle-sketch-table`: 登记 `/elements` 页面叶子表为实线表纸、`--c-element` 强调色。

## Impact

- 前端：`LocatorFileView.vue` / `LocatorFilePanel.vue` / `PageElementsWorkbench.vue`（及必要时模块 scoped CSS）；不改后端、不改设备管理与设备检查器实现。
- 侧栏退出键本身不改，只作为几何参照。
- 测试：`npm run typecheck`、`npm run lint:styles`、`vue-frontend-check` 针对改动文件。
- 恢复：`git revert`。
