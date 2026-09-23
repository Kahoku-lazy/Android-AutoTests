## Why

历史快照目前无限增长：真机库里已有 **314 条**（用户 `'1'` 独占 276 条，最早到 id=2），列表按 100 条一页拉取，用户既看不到头也删不干净。媒体侧同样堆积：`inspector/shots` 1341 个文件、`inspector/thumbs` 32117 个文件（317 个目录）。

本次把历史快照收敛为「每个用户最多近十条」的滚动窗口，并提供一键清空入口；存量按用户确认一次性清空。

## What Changes

- **保留上限 10 条/用户**：采集成功落库后，系统自动删除该用户创建时间最早的多余记录（第十一条出现 → 淘汰最早一条）。
- **列表最多十条**：历史快照列表最多返回 10 条，无论请求的条数；`total` 仍为该用户的真实总数。
- **淘汰与清空复用媒体保全判定**：被元素定位引用的截图 / 缩略图 MUST 保留（沿用既有「删除不得破坏仍被引用的媒体」规则）。
- **新增一键清空端点**：`DELETE /api/inspector/snapshots/clear/` → 删除当前调用者自己的全部快照，返回删除条数；无快照时成功返回 0。**BREAKING（端点集合）**：设备检查器从 8 个端点变为 9 个。
- **前端一键清空入口**：抽屉内新增「一键清空」按键，二次确认后调用清空端点，并把列表、元素表格与手机屏幕一起置为无快照空态；无快照时按键不可用。
- **存量一次性清空**：按用户确认，对既有 314 条记录执行一次性清空（含未被引用的媒体文件）。

## 关联文档

- PRD-03（设备检查器）

## Capabilities

### Modified Capabilities

- `device-inspector-snapshots`: 新增「按用户保留近十条」与「一键清空本人历史快照」两条要求（含媒体保全与归属隔离）。
- `device-inspector-page`: 抽屉删除的二次确认扩展到一键清空；「快照列表如实反映总量」中依赖 100 条截断的场景已不可达，改为「总数与保留上限一致」。

## Impact

- 后端：`apps/device_inspector/api.py`（保留上限与淘汰、清空、列表封顶、媒体安全删除的共用实现）、`apps/device_inspector/views.py`、`apps/device_inspector/urls.py`
- 前端：`frontend/src/modules/device-inspector/api.ts`、`store.ts`、`components/SnapshotListDrawer.vue`
- 数据：一次性清空既有 314 条快照（不可逆）；被元素定位引用的媒体文件保留
- 测试：`tests/graybox/integration/`（保留淘汰、清空、归属隔离、媒体保全）、`frontend/tests/device-inspector/p0/`
- 文档：`dev_docs/DEV_TEST/接口文档/API-设备检查器.md` 端点总览 8 → 9，补清空小节与列表上限
- 不涉及：引擎层、算法层、元素定位
