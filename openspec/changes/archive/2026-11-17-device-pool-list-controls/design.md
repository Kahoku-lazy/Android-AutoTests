# 设计：设备页控制区收拢到一行

## Context

现状（`/devices`）：顶部一行是 `FilterTabs`（三个 Tab + 计数角标）+「表格 / 卡片」两个切换键 + 计数 chip + 开发调试开关 + 局域网 / 刷新；表格上方还有一行「显示行数 [5]」与「第 X / Y 页 · 共 N 台」（仅多页时出现翻页键）。数据侧：`usePagination` 已提供 `currentPage / totalPages / pagedItems / goPage / setPageSize`，`filteredDevices` 由 `activeFilter` 单条件过滤。

约束：

- `frontend-l4-data-surface`：分页必须走共享 `usePagination`，选项集与默认值来自模块 `constants.ts`，不得自算 `totalPages`。
- `frontend-doodle-button`：设备页按键必须共用一套硬边几何；共享件 `FilterTabs` 若不再使用，不得改动其皮肤。
- 卡片视图只有 `index.vue` 一个消费方，删除不会牵连其它模块。

## Goals / Non-Goals

**Goals**：一个视图、一个控制行、固定行数、筛选与搜索并存、分页常驻。

**Non-Goals**：不改列结构（上一单已完成）、不改行点击与操作语义、不改后端接口、不动共享 `FilterTabs` / `usePagination` 的实现。

## Decisions

### D1 筛选用 `el-select`，选项仍由 `FILTER_TABS` + 运行时计数驱动

`filterTabs` 计算属性已经把 `{ key, label, count }` 备好，下拉直接消费它，标签渲染为「在线 · 3」。这样选项集合的真相源仍是模块 `constants.ts`，不新开一份。

*替代方案*：保留 `FilterTabs` 只改样式。与需求「做成下拉按键」不符。

### D2 搜索匹配「品牌 + 型号 / 序列号 / 连接地址」，不区分大小写

三者都是用户在界面上看得到的设备标识：名称用于认设备，序列号与地址用于粘贴定位。匹配用 `includes`（不区分大小写），不用正则，避免特殊字符。

*替代方案*：只匹配 `displayModel`。实测最常用的粘贴值是序列号，范围过窄。

### D3 控制条放在表格上方的一行：左「第 X / Y 页 · 共 N 台」+ 筛选 + 搜索，右「上一页 / 下一页」

沿用现有「表格上方控制条」的位置，只重排组内顺序，避免整页高度跳动。分页文案与翻页键同一行两端分布，符合需求描述的左右关系。

### D4 每页 7 行：`PAGE_SIZE_OPTIONS = [7]`、`DEFAULT_PAGE_SIZE = 7`，不渲染行数控件

`usePagination` 仍按 `options` 单值工作，符合 `frontend-l4-data-surface` 的「固定每页行数仍来自模块 constants」。`TABLE_ROW_HEIGHT_PX × pageSize` 的表格最小高度会自动从 5 行变 7 行，无需额外处理。

### D5 删除卡片视图的整条链路

`viewMode` / `switchViewMode` / `groupedDevices` / `CARD_GROUPS` / `DeviceCard.vue` / `.card-grid-grouped` 等卡片样式 / `DeviceViewMode` 类型一并删除。理由：只保留表格视图后它们没有消费方，留着就是死代码。`sketchToneAt` / `sketchTiltAt` 的引用随之移除。

### D6 分页条常驻：`disabled` 由 `currentPage` 与 `totalPages` 决定

不再用 `v-if="totalPages > 1"` 隐藏翻页键；置灰复用页面既有的 `.el-button.is-disabled` 皮肤（`opacity: .5` + 撤影）。

### D7 顶部计数 chip 删除

「共 N 台」已在新控制条里，保留顶部 chip 会与它重复且两个数字可能同时变化，读起来像两个口径。

## Risks / Trade-offs

- [习惯卡片视图的人失去入口] → 需求方明确要求删除；组件与样式已随代码移除，回退需还原 `DeviceCard.vue`（git 历史可查）。
- [下拉筛选少了「一眼看到三个计数」] → 选项标签仍带计数，展开即可看到；收起时只显示当前项计数。
- [搜索与筛选叠加后的空态容易误判为「没设备」] → 空态文案按「有筛选/搜索」分支走「没有匹配的设备」并提示清空条件。
- [7 行固定后，小屏一屏放不下] → 表格区域本来就在 `.doc-body` 内滚动，行高与最小高度不变，只是列表更长。

## Migration Plan

纯前端。上线即生效；回退按 D5 的反向还原（`git revert` 单次提交即可，改动集中在 device-pool 模块）。

## Open Questions

无。
