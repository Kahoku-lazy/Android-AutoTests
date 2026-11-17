# 设备管理表格：结构借用 + 表纸去影

## Why

设备表当前是 7 列纯文本 + 操作列三个等权按钮，一屏之内看不出「哪台设备、什么状态、下一步该点哪个」。需求方提供了参考图，希望借它**列头图标 + 首列身份单元 + 主操作胶囊**的结构，同时明确要求**表格不要阴影**。

## What Changes

- 七列表头各加一个图标（emoji）；列名保持纯文字，不把图标塞进 `title`。
- 首列由纯文本改为设备身份单元：圆形设备图标 + 在线状态点 + 型号 / `序列号 · 地址` 双行。
- 操作列由「锁定·强制释放·删除」三个等权按钮收敛为 **主操作胶囊 + `⋯` 次操作菜单**；USB 行仍无操作。
- 设备页表纸**去掉模块色位移硬影**，描边与圆角保持共享令牌不变；其它页面的表纸皮肤零改动。
- 不新增设计令牌；`AppTable`、`tokens.css`、共享表纸皮肤 `workbench-theme.css` 均不改。

## Capabilities

### New Capabilities

- `device-pool-table`：设备管理表格的列结构、首列身份单元与操作列收敛的契约。

### Modified Capabilities

- `frontend-doodle-sketch-table`：设备页表纸改为「无影变体」——保留共享描边、不绘制模块色硬影；并把该变体的作用域与登记要求写进需求。

## Impact

- 前端 `device-pool` 模块：`constants.ts`、`index.vue`、新增 `components/DeviceIdentityCell.vue`、`components/DeviceActionsCell.vue`、`DevicePoolView.style.css`。
- 共享类型：`shared/types/device.ts` 的 `ColumnConfig` 增加可选 `icon` 字段（向后兼容）。
- 不改后端、不改接口、不改列语义与筛选/分页逻辑；卡片视图与设备检查器不在本次范围。
