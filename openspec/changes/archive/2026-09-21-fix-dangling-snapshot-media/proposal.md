## Why

**已保存页面的媒体资产挂在检查器快照的生命周期上，且回看时零兜底。**

1. 导入时元素定位**照抄**检查器的媒体相对路径（`Page.screenshot_path`、`Element.thumbnail_path`）。
2. 删除快照会**连同截图与缩略图目录一起删**（`apps/device_inspector/api.py` 的 `delete_snapshot` → `service.delete_snapshot_files` 的 `unlink` + `rmtree`）。
3. 于是删一份快照 = 别人的已保存页面图全碎。**实测（dev 库）**：16/32 个元素、2/5 个页面的媒体文件已不存在；打开这类页面时手机屏幕一片空白（`screenshot_path` 非空 → 走「有截图」分支，图片 404 后为 0 尺寸）、缩略图列是浏览器破图图标，控制台 6 条 404。
4. 且这些文件**无法找回**（快照已删，缩略图只能重连设备重抓）。

本变更做两件事：**删除快照时保全仍被引用的媒体**（止住继续丢），以及**失效媒体的降级显示**（让已经丢的那批不再表现为空白/破图）。

## What Changes

- `apps/device_inspector/api.py` 的 `delete_snapshot`：删除文件前先判定该批媒体是否仍被元素定位引用（页面的 `screenshot_path` / 元素的 `thumbnail_path`）；**被引用则保留文件**，未被引用则照旧清理；判定在删除任何文件之前完成（判定异常 → 不删任何文件）
- 快照记录本身照常删除、列表照常刷新（用户语义不变）
- `ScreenshotView.vue`：截图 `<img>` 加 `@error` → 降级为**失效空态**（标题「截图已失效」+ 说明），MUST NOT 留空白
- `StructureAnalysisPanel.vue`：元素缩略图 `<img>` 加 `@error` → 回落既有的 `—` 占位；放大预览的图片失效时显示占位提示，其余字段照常显示
- **BREAKING**：无（删除快照的可见行为不变，只是不再破坏他人资产）

## 明确移出本变更范围

- **C 方案：导入时把媒体复制到元素定位自有目录**（彻底解耦生命周期）——改动最大、需迁移存量并占双份磁盘，登记为后续项；本变更先用「引用判定」以最小代价止住继续丢（design D2 写明取舍）
- 已丢失的 16 张缩略图 / 2 张截图**不做恢复**（快照已删，无法重建；只能重连设备重抓）
- 不回填历史页面的 `screenshot_path` / `thumbnail_path`
- 不改 `delete_snapshot_files` 的清理语义（它仍负责「真删」），只改「何时调用」
- e2e 选择器缺口（`save-folder-cascader`）与 store 对外裸露：并入另一张轻量单

## 关联文档

- 需求编号：`PRD-03-设备检查器`
- 相关既有要求：`device-inspector-page`「快照删除需二次确认」（删除的确认语义不变）

## Capabilities

### New Capabilities

- `device-inspector-snapshots`: 检查器快照及其媒体文件（整屏截图 / 元素缩略图）的生命周期契约——删除快照不得破坏其它模块仍在引用的媒体

### Modified Capabilities

- `device-inspector-page`: 新增「失效媒体降级显示」要求（截图失效 → 空态；缩略图失效 → 占位）

## Impact

- 后端 1 文件：`apps/device_inspector/api.py`（`delete_snapshot` + 新增引用判定私有函数）
- 前端 2 文件：`components/ScreenshotView.vue`、`components/StructureAnalysisPanel.vue`
- 测试：新增 `tests/graybox/integration/test_inspector_snapshot_media.py`（引用判定 + 保留/清理两条路径）
- 规格：新增 1 个 capability（`device-inspector-snapshots`）+ `device-inspector-page` 1 条新增要求
- 数据迁移：无（不改模型、不回填）
- 数据库/媒体：dev 库中已被引用的存量文件将不再被后续删除动作清理；未被引用的照旧释放