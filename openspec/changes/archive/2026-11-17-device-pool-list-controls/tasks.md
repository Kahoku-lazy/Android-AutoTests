# 任务：设备页控制区收拢到一行

## 1. 删除卡片视图链路

- [x] 1.1 `index.vue` 移除「表格 / 卡片」切换、卡片网格、`DeviceCard` 引用与 `sketchToneAt/sketchTiltAt`，`npx vue-tsc --noEmit` 通过
- [x] 1.2 `DevicePoolView.logic.ts` 移除 `viewMode` / `switchViewMode` / `groupedDevices` / `CARD_GROUPS` 及其接口字段
- [x] 1.3 `constants.ts` 删除 `CARD_GROUPS`；`shared/types/device.ts` 删除 `DeviceViewMode`
- [x] 1.4 删除 `components/DeviceCard.vue` 与 `DevicePoolView.style.css` 的卡片分组样式；全仓检索无残留引用

## 2. 固定每页 7 行

- [x] 2.1 `constants.ts`：`PAGE_SIZE_OPTIONS = [7]`、`DEFAULT_PAGE_SIZE = 7`
- [x] 2.2 `index.vue` 删除「显示行数」控件与 `setPageSize` 绑定；实测每页呈现 7 行

## 3. 常驻分页条

- [x] 3.1 控制条重排为一行：左侧「第 X / Y 页 · 共 N 台」+ 筛选 + 搜索，右侧「上一页 / 下一页」
- [x] 3.2 分页条常驻（含 1 页与 0 台）；实测 20 台 3 页 → 首页「上一页」禁用、末页「下一页」禁用；搜索后只剩 1 页时两键同时禁用且仍可见
- [x] 3.3 删除顶部重复的计数 chip

## 4. 下拉筛选与名称搜索

- [x] 4.1 状态筛选改为 `el-select`，选项来自 `filterTabs`（标签带计数：全部设备 · 20 / 在线 · 16 / 使用中 · 4），位置在分页文案右侧
- [x] 4.2 新增搜索框（可清空、带搜索图标），位置在筛选右侧
- [x] 4.3 `logic.ts` 增加 `searchKey` 与 `matchSearch`：品牌+型号 / 序列号 / 连接地址，不区分大小写包含匹配，并与 `activeFilter` 取交集
- [x] 4.4 `activeFilter` 或 `searchKey` 变化时回到第 1 页（`watch([activeFilter, searchKey])`）
- [x] 4.5 空态按 `hasNarrowing` 分支：有筛选或搜索时报「没有匹配的设备」+「换个关键字，或清空搜索条件。」；无设备时报「还没有可用设备」

## 5. 样式与皮肤

- [x] 5.1 筛选下拉与搜索框套本页硬边几何：实测 `border 2px solid`、`border-radius 2px`、`box-shadow 2px 2px 0 0 rgb(30,30,36)`；两者不套二态底色
- [x] 5.2 `npm run lint:styles`：device-pool 零告警（全仓仍因 `modules/task-list/**` 既有 21 条 G5 悬空引用为红，与本变更无关）

## 6. 测试与验收

- [x] 6.1 `tests/device-pool/p1/DevicePoolView.logic.spec.ts` 移除 `groupedDevices` 用例，页码用例按每页 7 行重算
- [x] 6.2 补用例：搜索按型号 / 序列号 / 地址命中、搜索与筛选取交集、搜索变化重置页码与清空恢复、默认每页 7 行；`node tests/run.mjs module device-pool` 9 文件 / 48 用例全绿
- [x] 6.3 `npx vue-tsc --noEmit`、`npm run lint`（0 error）、`npm run lint:lines`、`npx prettier --check src/modules/device-pool` 全部通过
- [x] 6.4 真实前端目视验收并截图：`temps/shot-controls-page1.png`（7 行 / 3 页）、`shot-controls-page2.png`、`shot-controls-search.png`（搜索命中 1 台、两键禁用）、`shot-controls-filter.png`（在线 16 台）
