## 1. 标签与字体

- [x] 1.1 `index.vue`：`.report-status-tabs` 覆盖共享 `filter-tab`（30px 高、墨框、选中加 `--c-report` 淡投影）。验证：`lint:styles` 批 2 通过。**验证结果**：批 2 通过。
- [x] 1.2 `index.vue`：`.badge` 统一 22px 高、2px 墨框、2px 圆角；表格单元格字号统一 `--app-size-sm`，时间/耗时改次要色 + `tabular-nums`。验证：build 通过。**验证结果**：build 19.4s。
- [x] 1.3 `index.vue`：工具条 gap 收敛到 `--app-space-sm`，页码/翻页保持右侧。验证：目视原型一致。**验证结果**：与原型一致。

## 2. 状态文案

- [x] 2.1 `api.ts` / `constants.ts`：`STATUS_LABEL_MAP` 两份都补 `cancelled: "已取消"`；`statusBadgeClass` 增加 `cancelled → badge-stopped`。验证：页面不再出现英文 `cancelled`。**验证结果**：映射已补。

## 3. 门禁

- [x] 3.1 `npx vue-tsc --noEmit`、`npm run build:check`、`npx vitest run tests/report-generator tests/task-list`、`npm run lint:styles`、`npm run lint:lines`。验证：全绿。**验证结果**：tsc 0；build 19.4s；19 文件 152 passed；批 2 通过；虚线 0 处。
- [ ] 3.2 目视：过滤标签、状态标签、行高在真实数据下的观感。验证：用户确认。

## 4. 布局对齐原型

- [x] 4.1 去掉分区头里的「测试报告 Reports」标题（表格左上角不再重复页面标题），筛选标签留在原头行左侧。验证：build 24.7s、161 用例通过、虚线 0 处。**验证结果**：通过。
- [x] 4.2 原型同步去掉标题行，标签 → 工具条 → 表格 的顺序与线上一致。验证：截图与实现结构对齐。**验证结果**：已对齐。

- [x] 4.3 工具条上下等距：.table-toolbar padding space-sm / space-md / 0 → space-xs / space-md（上下各 4px），两组控件整体上移。验证：build 20.0s。**验证结果**：通过。
- [x] 4.4 筛选项淡色底：FilterTabs 增加 data-key，报告页按状态给淡色填充（全部=report 8%、已完成=success-bg、失败=danger-bg、已中断=warning-bg、已停止=ink 6%）。验证：共享+报告 51 用例通过、批 2 通过、虚线 0 处。**验证结果**：通过。

- [x] 4.5 表头加大 + 淡色底：.report-table .el-table__header th 字号 xs(12) → sm(14)、背景由 --app-bg-subtle 改为 --c-report 16% 混白、字距 0.04 → 0.03em。验证：build 19.7s、虚线 0 处。**验证结果**：通过。

- [x] 4.6 表格薄荷绿淡底：.table-card、.el-table、	r、	d 背景改为 --c-device 8% 混白；表头 16%；hover 15%。验证：build 25.4s、批 2 通过、虚线 0 处。**验证结果**：通过。

- [x] 4.7 薄荷底优先级加固：选择器提升为 .report-workbench .report-table :deep(.el-table__cell)（10%）与表头 	h.el-table__cell（20%），hover 18%；编译产物确认选择器为 (0,4,1) + !important，高于全局 .el-table td 的 (0,1,1)。验证：dist 于 16:58 重新构建。**验证结果**：by build。

- [x] 4.8 定位到真实原因：AppTable 把 
eport-table 类合并到内层 el-table，而该元素不带页面 scope 属性，.report-table[data-v] 选择器永远不匹配（td 仍是全局白色）。改用 .report-workbench :deep(...)（scope 属性在页面根上），并用 CDP 实测 	d 背景 = srgb(0.94,0.98,0.95) 薄荷绿。验证：真实页面截图（temps/report-live.png）确认表头/表体薄荷底生效。**验证结果**：通过。

- [x] 4.9 表底换柠檬黄：.table-card / 表体 / 悬停由 --c-device 改为 --c-dashboard（12% / 22% / 20%）。验证：真实页面 CDP 截图（temps/report-live.png）确认柠檬淡底生效；build 18.1s。**验证结果**：通过。
