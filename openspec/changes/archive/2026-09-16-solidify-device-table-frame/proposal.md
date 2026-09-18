## Why

设备管理页（`/devices`）表纸的外框是全平台表纸令牌 `--comp-sheet-border` 的 `2.5px dashed`（**虚线**），
用户在浏览器定位到表体首列单元格后提出两点：「表格设计的线条采用实线」与「去掉该单元格的 `::before` 设计」。

现状（读码核实）：

| 线 / 装饰 | 现状 | 位置 |
| --- | --- | --- |
| 表纸外框 | `2.5px dashed var(--ink)` —— 虚线 | `tokens.css:281` `--comp-sheet-border` → `workbench-theme.css:165` `.wb-shell .sketch-sheet` |
| 表头底线 | `2px solid var(--ink)` —— 已是实线，本变更不动 | `style.css:104` |
| 行分隔线 / 列分隔线 | 1px `transparent` 占位，**不绘制**，本变更维持 | `style.css:110`、`workbench-theme.css:142` |
| 首列状态色条 | `td:first-child::before` 4px 纯色块（在线绿 / 使用中黄） | `DevicePoolView.style.css:336-351` |

状态色条是**冗余的第二状态载体**：同一行的「状态」列已由 `DeviceStatusCell` 渲染文字标签（在线 / 使用中 / 离线·不可用）+ 三态配色。
这与归档变更 `unify-card-surfaces` 移除 `DeviceCard` 左侧 4px 色条的口径一致（同一判断）。

## What Changes

- **设备管理页表纸外框改为实线**：页面作用域覆写 `border-style: solid`，**只改线型**；描边宽度与颜色仍取共享令牌 `--comp-sheet-border`（`2.5px` 墨色），共享令牌本身与其它页面表纸（`/reports`、`/elements`）**不动**。
- **移除首列 `::before` 状态色条**：删除 `DevicePoolView.style.css` 中该装饰的 3 条规则。
- **连带清理死机制**：色条是 `row-online` / `row-busy` 行类名的唯一消费方；移除后 `deviceRowClassName`、`AppTable` 的 `row-class-name` 传参与 `DevicePoolViewState` 的对应成员成为无消费方的死代码，一并删除。
- **内部网格线维持不绘制**：`frontend-l4-data-surface` 的「Tables draw no visible grid lines」在本变更中**不变**。

## 关联文档

- `dev_docs/文档编号对照表.md` **不存在**，故不引用 PRD/ARCH 编号。
- 依据报告：`dev_docs/DEV_TEST/设备管理页面设计元素清单-2026-09.md`（§2.6 状态色条、§2.11 表格）
- 相关 spec：`frontend-doodle-sketch-table`（表纸皮肤，本变更修改）、`frontend-l4-data-surface`（无网格线，本变更不动）
- 同口径先例：归档变更 `2026-09-16-unify-card-surfaces`（移除 `DeviceCard` 左侧 4px 色条）

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `frontend-doodle-sketch-table`: 「Sketch table is AppTable paper skin」需要把表纸描边的**线型**由单口径「虚线」改为按页登记（设备管理页实线 / 报告列表虚线）；并新增一条「设备表行状态不用首列色条」的要求。

## Impact

- 前端页面：`/devices`（`frontend/src/modules/device-pool/`）
- 改动文件：`DevicePoolView.style.css`、`DevicePoolView.logic.ts`、`index.vue`
- 共享件 / 令牌 / 其它页面：**不改**（`tokens.css`、`workbench-theme.css`、`style.css`、`AppTable.vue` 均不动）
- 无后端、无 API 契约、无依赖、无路由变更
- **有意的视觉变更**：设备表与 `/reports`、`/elements` 的表纸线型不同（用户明确选择"仅设备管理页"）
