## Context

动机见 `proposal.md` - Why。行为契约见 `specs/element-locator-page-workbench/spec.md`。

当前实现集中在 `PageElementsWorkbench.vue`：工具栏 `el-radio-group` 绑定 `elementFilter`，`watch([pageId, elementFilter])` 调 `apiPageItems(pageId, filter, 500)`；主体为 CSS grid 左右分栏，左栏挂唯一消费者 `PageScreenshotOverlay.vue`（`.shot-pane`），右栏 `AppTable`。截图点击通过 `selectElement(..., 'shot')` 滚到表格行。`PageScreenshotOverlay` 全仓仅此一处引用。后端 `views_page_elements.page_elements` 仍支持 `filter=all|clickable|text|testpoint` 并返回 `screenshot_path`。

约束：不改后端契约；表格继续走共享 `AppTable`（`frontend-l4-data-surface`）；空/错/加载继续用既有 `EmptyState` / `ErrorState` / `SkeletonCard`。

## Goals / Non-Goals

**Goals:**

- 工作台布局从双栏改为单一表格容器，表格占满文件面板剩余高度。
- 去掉筛选状态与截图联动代码路径，避免留下死 props / 死 CSS。
- 列表请求固定未筛选，列与行内编辑保持现口径。

**Non-Goals:**

- 不删后端 `filter` 参数与 `screenshot_path` 字段。
- 不改设备检查器截图、筛选栏、保存到元素对话框。
- 不改表格列集合、别名输入、测试点开关、更新接口。
- 不改 `helpers/element-bounds.ts` 的算法本身：该文件当前仅被 overlay 引用，删除 overlay 后 MUST 一并删除该 helper，避免零引用残留。

## Decisions

### D1 删除 overlay 组件，而不是 `v-if` 隐藏

备选：保留 `PageScreenshotOverlay` 用开关关掉 —— 否决，用户要求去掉功能，组件全仓无第二消费者，隐藏只会留下死代码。

做法：工作台去掉 import 与左栏；删除 `PageScreenshotOverlay.vue` 与仅被其引用的 `helpers/element-bounds.ts`。

### D2 前端固定 `filter=all`，不改 `apiPageItems` 签名（除非签名因此无用）

备选：从 `api.ts` 去掉 `filter` 参数 —— 可做但非必须；后端仍认该 query。为减小 diff，保留函数签名，调用处传入 `'all'` 或省略时依赖后端默认 `'all'`。优先省略或常量化 `'all'`，去掉 `elementFilter` ref 与 `watch` 对 filter 的依赖，仅 watch `pageId`。

### D3 去掉截图联动后简化选中逻辑

截图源的 `scrollRowIntoView` / `onShotSelect` / `selectElement` 的 `source` 参数不再有第二调用方。备选：保留行点击 `is-selected` 高亮 —— 采纳保留 `highlight-current-row` + `rowClassName`，作为表格自身当前行标识，不新增交互。删除仅为截图滚动服务的 DOM `querySelector` 滚动。

### D4 布局：取消 grid 分栏

`.page-workbench__split` 改为单列弹性容器包表格；删除 `__shot`、窄屏「上截图下表格」media query。工具栏仅保留「共 N 个元素」（无右侧 radio 后用 `justify-content: flex-start` 即可）。

## 模块防火墙自检

- 跨 App import：不涉及。仅改 `frontend/src/modules/element-locator/` 私有组件。
- 禁止跨 App import service/runner/consumer/state_machine：不涉及。
- INSERT/UPDATE/DELETE 收敛：不新增写库；别名/测试点仍走既有 `PUT /elements/items/{id}/`。
- 前端不直连数据库：仍经 `api.ts` → `/api`。
- 无新跨模块依赖。

## Risks / Trade-offs

- [用户曾依赖截图圈选对照 bounds] → 设备检查器仍承担实时截图/圈选；本页只读已入库定位字段。空态文案若仍写「可从设备检查器导入快照」可保留。
- [后端 filter 成为仅后端/其它客户端能力] → 明确登记为本次不删；避免只清前端却误改 API 测试。
- [`frontend-l0-design-tokens` 场景举例仍写「`/elements` 的页面元素表筛选器」] → 举例过时但不改变需求；`el-radio-button` 仍存在于保存到元素对话框。本次不改该 spec，避免无关 delta。

## Migration Plan

纯前端部署。回滚：`git revert` 本变更。无数据迁移。
