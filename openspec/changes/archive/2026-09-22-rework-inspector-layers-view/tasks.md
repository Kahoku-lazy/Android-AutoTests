## 1. 常量与状态

- [x] 1.1 在模块 `constants.ts` 登记五个分组（key / 显示名 / 层级 / 固定顺序 / 分组色）与新的列宽集合，验证：`npm run lint:styles` 通过，且组件内不再出现分组名与色值字面量
- [x] 1.2 改造 `store.ts`：退役 `filterMode` / `searchText` / `filteredAnalysisElements` / `analysis`，新增 `layers` / `layerSource` / `activeGroup` / `groupElements`；`capture()` 与 `viewSnapshot()` 改为拉取分层数据并默认选中第一个非空分组，验证：重写后的 `tests/device-inspector/p0/store.spec.ts` 全绿
- [x] 1.3 在 `api.ts` 增加分层请求并把 `analyzeSnapshot` 移出调用链（后端端点保留），验证：P0 用例断言请求路径与参数，且不再发出分区请求

## 2. 页面与组件

- [x] 2.1 删除 `index.vue` 的筛选栏整块（`:93-102`）、其死样式与 `FilterTabs` import，左栏改为分组选择，验证：`npx vite build` 通过，且页面在已载入与未载入快照两种状态下都不出现筛选标签栏与搜索框
- [x] 2.2 改造 `StructureAnalysisPanel.vue`：props 改为分组与当前分组元素，表格列集合覆盖序号/缩略图/名称/类名/标识/文本/描述/坐标与尺寸/层级/父内序号/七项标志/细类/保留标记/主定位；**删除页面自带的 `XPATH_PRIORITY` 与 `bestXPath()`，XPath 列改读分层数据的 `primary.xpath`**；保留勾选列与内联重命名，验证：元素表格 P0/P1 用例通过，横向滚动与首列冻结可用，无缩略图的行显示占位，且检索 `XPATH_PRIORITY` 在模块内无命中
- [x] 2.3 改造 `ScreenshotView.vue`：按当前分组全量元素画框（保留实线、被裁虚线、分组色），并改为**两层画布**——离屏层缓存当前分组框、可见层只画 hover 与选中；同时删掉现有「无身份元素直接跳过」的过滤（否则布局容器组整组画不出来），保留双击红色选中高亮与选中滚动，验证：手工走查「切分组只换框集合」，且同一分组内移动鼠标时可见层重画的矩形数不随分组规模增长（加打点计数确认）
- [x] 2.4 冻结「已保存页面」入口：触发键禁用并给出可读原因，`viewSavedPage` 去掉伪造分区逻辑后保留代码路径，验证：点击该入口不发起任何请求、页面分组与表格不变化（网络面板 + 用例断言）

## 3. 门禁与验收

- [x] 3.1 前端门禁全量执行：`npm run lint:styles`、`npx vite build`、`npx vitest run`、`npx vue-tsc --noEmit`，验证：全部通过（vue-tsc 不得新增错误）
- [x] 3.2 真机数据验收（替代浏览器点击走查）：对真实设备采一页后走分层接口，核对五分组计数、被裁元素出现在结果里、响应体大小与元素条目字段；**浏览器内点击走查未执行**（本会话无浏览器控制能力），静态与单测侧由 `lint:styles` + `vite build` + `vue-tsc` + `vitest` 覆盖，组件行为另按「离屏层/可见层职责分离 + `visibleRectCalls` 自检计数」验证。验证：`python temps/accept_layers.py`（快照 #347：78 元素 / 五分组 / 43 个被裁元素 / 响应 53.8 KB / 源 index）