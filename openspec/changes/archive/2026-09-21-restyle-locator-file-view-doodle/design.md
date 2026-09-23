## Context

动机见 `proposal.md` - Why。行为见本变更 specs。

现状：`LocatorFileView`（`.locator-workbench.file-view`）内 `WorkbenchCrumbs` 已是硬边返回芯片；`LocatorFilePanel`「删除」为 `el-button type="danger" plain`；`PageElementsWorkbench` 的 `AppTable` **未传 `accent`**，因此没有 `.sketch-sheet`。设备管理页对照：`accent="var(--c-device)"` + `.device-workbench :deep(.sketch-sheet) { border-style: solid }`。硬边按键对照：侧栏 `.logout-btn` 与 `.inspector-workbench :deep(.el-button:not(.is-text):not(.is-link))`。`frontend-doodle-button` 禁止改 `DoodleBtn` / `ErrorState` / 全局主题来迁就新页。

## Goals / Non-Goals

**Goals:**

- 仅文件详情页：删除键硬边化；元素表开 SketchTable 实线表纸。
- 皮肤写在页面/模块作用域，不改共享默认。

**Non-Goals:**

- 不改项目列表、目录树、新建目录弹窗按键。
- 不改列、筛选、截图（已去掉）、删除确认流程、后端。
- 不把 `DoodleBtn` 几何改成与 logout 完全一致（它不是本页删除键的实现路径）。
- 不发明第二套表格组件。

## Decisions

### D1 删除键用页面作用域覆写 `el-button`，不换 `DoodleBtn`

备选：换成 `DoodleBtn tone="danger"` —— 否决。其边框 2.5px、阴影 3px，与 logout 的 2px / `2px 2px 0 0` 不一致，且会改共享件消费面。设备检查器已证明：在 `.file-view` 上 `:deep(.el-button:not(.is-text):not(.is-link))` 即可对齐几何。删除底色用已登记危险红（如 `--sidebar-red` / `--app-marker-red` / `--el-color-danger` 中与 logout 同源的令牌），文字用 `--app-bg-card` 一类浅色。保留 `ElMessageBox.confirm`。

### D2 表纸只传 `accent` + 覆写 `border-style`

`PageElementsWorkbench` 的 `AppTable` 增加 `accent="var(--c-element)"`。在 `.locator-workbench.file-view`（或工作台根）`:deep(.sketch-sheet) { border-style: solid }`，不改 `--comp-sheet-border`，避免报告列表虚线被带跑。行 hover 若需要，用 `color-mix(..., var(--c-element) ...)` 仿设备表，不得写 hex。

### D3 承载选择器收窄到 `.file-view`

`.locator-workbench` 还挂在项目列表与目录工作台上。硬边与实线表纸只挂 `.locator-workbench.file-view`，避免列表页被误伤。

### D4 返回芯片不重做

`WorkbenchCrumbs` 已是硬边回退；用户点名的是退出键几何，删除键才缺这一套。返回键继续共享件。

## 模块防火墙自检

- 跨 App import：不涉及。
- 写库：删除仍走既有 `deleteFile` → API，不新增写路径。
- 前端不直连数据库。
- 无新跨模块依赖。

## Risks / Trade-offs

- [`:deep(.el-button)` 可能误伤确认弹窗内按钮] → 弹窗若 teleport 到 body 则不受本页作用域影响，保持 EP 默认；若在页内，与检查器一样接受弹窗键也硬边化，危险确认仍用浅字深红底。
- [项目列表同模块被误套皮肤] → D3 选择器带 `.file-view`。
- [表内 `el-input` / `el-switch` 仍是 EP 默认] → 用户参照的是表纸外壳；单元格控件本次不扩 scope。
