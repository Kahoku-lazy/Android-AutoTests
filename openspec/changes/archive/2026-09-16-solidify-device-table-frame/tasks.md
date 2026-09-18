## 1. 表纸外框改实线

- [x] 1.1 在 `DevicePoolView.style.css` 的表格段落加页面作用域覆写 `.device-workbench :deep(.sketch-sheet) { border-style: solid; }` 并写明"只改线型、宽/色仍取 `--comp-sheet-border`"
- [x] 1.2 核实未动共享令牌与其它页面：`tokens.css`、`workbench-theme.css`、`style.css`、`AppTable.vue` 在本变更中 diff 为空

## 2. 移除首列状态色条

- [x] 2.1 删除 `DevicePoolView.style.css` 中 `td.el-table__cell:first-child::before` 的 3 条规则（几何 + online 底色 + busy 底色）
- [x] 2.2 删除连带死代码：`DevicePoolView.logic.ts` 的 `deviceRowClassName` 函数、`DevicePoolViewState` 的对应成员与返回值；`index.vue` 的解构与 `:row-class-name` 传参
- [x] 2.3 核实内部网格线未变：`style.css:110` 与 `workbench-theme.css:142` 的 `1px transparent` 占位保持原样，`frontend-l4-data-surface` 无 delta

## 3. 同步 spec 与文档

- [x] 3.1 直接更新主 spec `openspec/specs/frontend-doodle-sketch-table/spec.md` 的 `## Purpose`（delta 的 Purpose 对既有能力不生效），去掉"外框为虚线"的单口径表述

## 4. 验证

- [x] 4.1 `cd frontend && npm run lint:styles` 退出码 0
- [x] 4.2 `cd frontend && npx vite build --mode development` 退出码 0
- [x] 4.3 Chromium 断言（含改动前反证）：`/devices` 表纸 `border-style` 为 `solid`、宽度仍 `2.5px`、颜色仍为墨色、模块色硬阴影仍在；首列 `::before` 的 `content` 为 `none`；`td` 行线仍为透明占位
- [x] 4.4 Chromium 断言：非设备作用域的表纸仍为 `dashed`，且行渲染/斑马纹/选中态未受影响
- [x] 4.5 `npx openspec validate solidify-device-table-frame --strict` 通过

## 5. 归档关单

- [x] 5.1 `npx openspec archive solidify-device-table-frame -y` 成功
- [x] 5.2 `npx openspec validate --all` 无新增失败项
