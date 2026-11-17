# BUG 页控制区改用手稿皮肤 + 留白与字号优化

## Why

BUG 列表现在把「分类 Tab / 搜索 / 状态 / 同步」摊成两行，右侧还挂一句「共 57 张 BUG 单」与表头重复计数；控件是主线实线皮肤，与需求方给的 Sketched UI Kit 参考不一致。表格本身也偏挤：单元格用 Element Plus 默认内边距、表格左右贴到分区边缘，正文与首列字号偏小。

## What Changes

- 分类 Tab（全部 BUG / UI 自动化 / 测试用例编写）移到搜索框左侧，与搜索、状态、同步键同一行。
- 搜索框与状态下拉改用手稿皮肤（`.sketch-kit`：虚线边框、无影、带字段标题），复用已登记的 `Sketched UI Kit`，不新写一套控件样式。
- 「同步历史错误」用 kit 的填充态（黄底 + 墨边 + 硬影）；「上一页 / 下一页」换成 kit 的描边态（虚线 + 无影，禁用态更淡）。
- 删除「共 57 张 BUG 单」提示（与表头/分页的计数重复）。
- 表格留白与字号：单元格内边距加到 16px、表头 12×16，表格四周留出分区内边距，首列编号升到 16px、时间 14px。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- `bug-ticket-management`：新增「控制区排布与控件皮肤」与「表格留白与可读字号」两条要求。

## Impact

- 前端 `bug-manager`：`index.vue`（控制区重排、换成 DoodleBtn）、`index.style.css`（留白/字号/清理旧样式）、`components/BugIdentityCell.vue`（字号）。
- 复用共享 `shared/styles/sketched-kit.css` 与 `DoodleBtn`，不改共享件与令牌。
- 不改接口、筛选逻辑、分页逻辑与详情抽屉。
