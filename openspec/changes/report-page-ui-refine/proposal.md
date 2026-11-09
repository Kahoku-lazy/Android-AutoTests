## Why

测试报告页的字体与图标表达不统一：表头、正文、任务 ID 字重接近，状态标签混着中文与 `cancelled` 英文，过滤标签是胶囊而表格是纸片，整页层级读不出来；工具条与行距也偏挤。需要在不改数据与交互的前提下把这一页的视觉收敛成一套。

## What Changes

- **过滤标签**：胶囊底改为「墨框小卡片」，选中项加模块色淡投影；高度统一 30px。
- **状态标签**：统一 22px 高、2px 墨框、2px 圆角；`cancelled` 中文化为「已取消」，并归入灰色「已停止」类。
- **表格字体**：单元格统一 14px（`--app-size-sm`）；时间与耗时改次要色 + 等宽数字；任务 ID 保持等宽小字。
- **工具条**：间距收敛到 `--app-space-sm`，页码与翻页留在右侧。
- 页头、过滤项数量、数据与跳转行为不变。

## 关联文档

- 原型：`temps/report-redesign-proto.html`（已确认）。

## Capabilities

### New Capabilities

无（纯视觉与文案收敛，不改查询/分页/跳转契约）。

### Modified Capabilities

无。

## Impact

- 前端：`modules/report-generator/{index.vue,api.ts,constants.ts}`。
- 后端 / 接口：无改动。
