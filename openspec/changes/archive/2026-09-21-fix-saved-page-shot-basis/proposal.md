## Why

已保存页面回看时，手机屏幕上的元素框与截图**对不齐**，截图还可能被拉伸。

原因是坐标基准是猜的：元素定位的 `Page` 表没有屏幕尺寸字段（`apps/element_locator/models.py:93-107`），`get_page_full` 也不返回 `screen_w/screen_h`，于是 `index.vue:117-118` 兜底 `1440×3040`；而 `ScreenshotView.vue:202` 用 `s = img.clientWidth / props.screenW` 换算元素框、`fitBox`（`:135-137`）又按该比例定图片盒尺寸。实测本机设备是 **1080×2340**（`R5CT62RH88F` / SM-S9010）——宽度差 **33%**，元素框必然偏小，且 `width/height: 100%` 会把截图拉成 1440:3040 的比例。

截图本身就是全屏图，它的真实像素尺寸就是屏幕尺寸。本变更改用 `naturalWidth/naturalHeight` 作为唯一基准（`screenW/H` 降级为加载前的兜底），既修好对齐与宽高比，也不需要给 `Page` 加字段做迁移。

## What Changes

- `ScreenshotView.vue`：`fitBox` 与 `drawOverlay` 的尺寸基准改为已加载截图的 `naturalWidth/naturalHeight`；`screenW/screenH` props 仅作截图未就绪时的兜底；截图 MUST 保持原始宽高比（不拉伸）
- `index.vue`：去掉 `|| 1440` / `|| 3040` 的假兜底（它会掩盖「这条数据本来就没有」这一事实）
- `ScreenshotView.vue`：把两处同源 `watch(() => props.selected, …)` 合并为一处（**由 `purge-inspector-dead-code` 移入**：该文件同时被两单触及，且合并的语义验证与本次真机走查是同一次）
- **BREAKING**：无

## 明确移出本变更范围

- 给 `Page` 增加屏幕尺寸字段（要迁移；本次方案零数据依赖，无此必要）
- 悬空媒体 404（④，另单）
- 已保存页面回看的 `alias` 与只读改名（单 3）
- 快照抽屉总数、错误净化、删除后状态复位（单 1）

## 关联文档

- 需求编号：`PRD-03-设备检查器`
- 相关既有要求：`device-inspector-page`「双击标识才在手机画面画红框」（框坐标的来源）、「三栏布局顺序」（手机屏幕栏）

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `device-inspector-page`: 新增「手机屏幕按截图真实尺寸换算」要求（含宽高比不变形）

## Impact

- `frontend/src/modules/device-inspector/components/ScreenshotView.vue`（尺寸基准 + watcher 合并）
- `frontend/src/modules/device-inspector/index.vue`（去掉假兜底传值）
- 后端 / 端点 / 模型 / 迁移：零改动
- 规格：`device-inspector-page` 1 份 delta（1 增）
- 验收依赖：设备 `R5CT62RH88F`（1080×2340，当前在线空闲）抓一张新快照并保存为页面，用于修前/修后对比