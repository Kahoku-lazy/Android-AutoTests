## Context

- 页面现状：`index.vue:93-102` 是筛选栏（`FilterTabs` + 关键词输入框），其样式在 `:176-188` 与 `:190`，`FilterTabs` 的 import 在 `:13`；左栏分区筹码由 `StructureAnalysisPanel.vue` 的 `activeRole`（按 `e.role` 过滤）承担。
- `StructureAnalysisPanel.vue` 以 props `sections / elements / isWebview / selected` 驱动，`usePagination` 固定每页 7 行，列宽与最小宽登记在 `constants.ts`（`ELEMENT_COLUMN_WIDTHS` / `TABLE_MIN_WIDTH_PX`），选择列写 `store.checkedIds`（键 `d<下标>`），内联重命名写 `store.nameOverrides`。
- `ScreenshotView.vue:211-265` 已有 canvas 绘制：按 `props.elements` 画框、选中描红填充、hover 高亮；`:137-141` 已有选中联动滚动；`drawOverlay` 已是「按坐标画框」的现成实现。
- `store.ts` 现有 `filterMode / searchText / analysis / filteredAnalysisElements`；`capture()` 与 `viewSnapshot()` 在拿到快照后调用 `analyzeSnapshot()` 取 6 层分区。
- 分层端点由前置变更交付（含筛减参数与降级来源标记）；6 层分区端点保留但本页不再消费。已保存页面存量数据作废，入口冻结。
- 需求来源见 proposal.md - Why；条款见 specs/device-inspector-page。

## Goals / Non-Goals

**Goals:**

- 左栏固定五个分组；表格展示当前分组的全量元素；一张截图按当前分组圈选。
- 删除筛选栏（控件 + 死样式 + import），并把退役的筛选状态从 store 中摘除。
- 保留「勾选保存到元素定位」与「表格内联重命名」两条既有能力，行为不变。

**Non-Goals:**

- 不改后端端点与算法层（前置变更已交付）。
- 不改设备选择控件、页面骨架、快照抽屉与元素定位侧任何内容。
- 不重命名组件文件，也不为「页面分区 → 分组」的纯命名变更制造 spec delta。
- 不为已保存页面修复数据（冻结而非修复）。

## Decisions

**D1 capture 后一次拉全量分层，切分组纯前端切换。** 服务端筛减参数作为深链接与大页面的兜底，不参与常规切换路径。备选：每次切分组发请求 → 否决（切分组会抖动，且分组数固定为 5）。

**D2 store 状态形状：`layers`（分组摘要）、`layerSource`（完整/降级来源标记）、`activeGroup`（五选一，默认第一个非空分组）、`groupElements`（当前分组全量，顺序由后端给定）。** 退役 `filterMode` / `searchText` / `filteredAnalysisElements` 与 `analysis`；`analyzeSnapshot()` 从前端调用链移除（端点保留在后端）。

**D3 表格列集合按「有多少信息显示多少信息」铺满全字段**（序号、缩略图、元素名称、类名、资源标识、文本、内容描述、坐标与尺寸、层级、父内序号、七项交互标志、细类、保留标记、主定位）。列宽仍集中登记在 `constants.ts`。缩略图只对可交互子集存在，无图与失效一律占位（复用既有 `brokenThumbs` 机制），不出现破图。**XPath 列改为直接显示分层数据里的主定位**，并删除页面自带的挑选规则（同文件内的 `XPATH_PRIORITY`（`:188`）与 `bestXPath()`（`:190-197`））——该规则与算法层口径不一致（`text` 与 `content-desc` 顺序相反、`class` 排在 `combined` 之前），且会把位置型候选当作最佳返回（位置型候选的匹配数恒为 1，会通过它的唯一性过滤），属于必须消除的第二处真相源。

**D4 一图多圈由现有 canvas 实现承接，并采用两层画布。** 底层为离屏画布，缓存「当前分组的全部元素框」，只在切换分组或换快照时重画一次；上层为可见画布，每次只画 hover 高亮与选中红框 1~2 个矩形。理由：现有 `drawOverlay()` 的触发源包含 `mousemove`（hover 一变就整层重画），而改造后单帧要画的矩形从「仅可交互子集」涨到「整组」（示例页布局容器组 74 个且含虚线），单层实现会在 hover 时做无谓的 O(n) 重画。分组色与实线/虚线规则登记在 `constants.ts`，与后端报告同色系；`kept_in_snapshot` 决定实线（保留）与虚线（被裁）。备选：单层直接画（改动更小）→ 本单不采用；若后续实测无感可退回单层。

**D5 已保存页面入口冻结的实现方式：触发键禁用 + 原因提示；`viewSavedPage` 路径保留但去掉「伪造分区」逻辑**（否则会引用已退役的 `analysis`）。解冻时只需补数据来源，不需恢复逻辑。

**D6 保留「页面分区」这一结构名（左栏），语义改为分组选择。** 纯命名变更不产生 spec delta；需求条款以分组语义为准。

**D7 空态文案沿用同一句**（`EMPTY_TEXT`）——现有「任何无数据情形同一句」的条款已覆盖新增的「分组无元素」情形，不需要改 spec。

## 模块防火墙自检

- **前端 HTTP 出口**：仅经 `modules/device-inspector/api.ts` → `shared/api-client`；不新增 axios 直连或裸 fetch。
- **共享件**：`FilterTabs.vue` 与 `useFilterTabs.ts` 在 device-pool 与 ai-assistant 仍在用，本变更 MUST NOT 修改它们，只移除本页 import。
- **组件职责**：分组与细类判定全部来自后端响应，组件内 MUST NOT 重写分类规则（前后端判据同源在算法层）。
- **写操作**：本变更无新增写操作；「保存到元素定位」沿用既有端点。
- **数据库**：前端不直连数据库。

## Risks / Trade-offs

- [store 形状改造会让现有 P0 用例变红] → 同一变更内重写 `tests/device-inspector/p0/store.spec.ts`，以新状态形状为准。
- [列集合从 8 列扩到约 18 列，窄屏横向滚动压力上升] → 沿用既有横向滚动 + 前 3 列冻结 + `TABLE_MIN_WIDTH_PX` 集中登记；缩略图与元素名称保持在冻结列内。
- [移除搜索后，大分组内定位单个元素变难] → 本轮明确的取舍（用户要求删筛选栏）；分组已把范围缩小到同类元素，后续如需可在分组内加定位手段，本单不加回搜索。
- [历史快照降级集会让用户误以为元素变少] → 页面按 `layerSource` 明示当前为降级集、不含被裁元素。
- [冻结入口仍占工具条位置] → 保留可见是有意为之（用户要求入口保留），以禁用态与提示表达不可用。

## Migration Plan

- 前端一次性切换：store 形状与组件 props 同步改，同一变更内完成，无灰度需求。
- 后端无需配合发版（分层端点已在前置变更上线）；6 层分区端点保留，回滚时前端可退回旧消费路径。
- 回滚：回退前端产物即可；无数据库迁移需要回滚。

## Open Questions

- 18 列是否全部默认展示，还是需要「列可见性」设置——本单全部展示，若实际过宽再议。
- 分组内是否需要二次排序（如按可点击过滤式排序）——用户明确要求按坐标顺序，本单不做。