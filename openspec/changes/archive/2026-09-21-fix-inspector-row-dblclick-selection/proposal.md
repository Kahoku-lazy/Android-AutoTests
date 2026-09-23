## Why

**规格要求的行为在真实产品里完全失效**：`device-inspector-page`「双击标识才在手机画面画红框」要求左键双击数据格在手机截图上画框；实测双击任何数据格都**不产生选中**，该要求当前 0 通过。

根因不在检查器本身，而在共享拖拽件：`shared/composables/useTableDragScroll.ts:103-107` 在 `pointerdown` 就 `el.setPointerCapture(e.pointerId)`（捕获元素 = el-table 自身的横向滚动容器 `.el-scrollbar__wrap`）。按 Pointer Events 语义，指针被捕获后随后的兼容鼠标事件（`click` / `dblclick`）会被**重定向到捕获元素**，于是 Element Plus 挂在 `tr` 上的 `onDblclick`（`element-plus/es/components/table/src/table-body/render-helper.mjs:41`）永不触发，「双击」这一手势在数据格上彻底不可用。

受控实验（`temps/dbg-capture-hypothesis.mjs`）：

| 条件 | dblclick 目标 | 选中行数 | `onRowDblClick` 是否触发 |
|---|---|---|---|
| 现状（捕获生效） | `el-scrollbar__wrap` | 0 | 否 |
| 页面级禁用 `setPointerCapture` | `sap-label-hit` | 1 | 是 |

补充事实：单击「元素名称」仍能进改名，是因为该格自己写了 `@pointerdown.stop`，让 composable 根本没机会捕获 —— 这反过来印证了捕获就是元凶。

本变更是**修代码**：规格已有该要求且不需要改动，故 `.openspec.yaml` 置 `skip_specs: true`。

## What Changes

- `useTableDragScroll.ts`：把 `setPointerCapture` 从 `onTablePointerDown` 延后到 `activatePan`（即拖拽真正激活时：长按 180ms 或横向移动 6px），激活前不再捕获指针
- 拖拽平移行为保持不变：移动监听原本就挂在 `window` 上，捕获只用于「指针离开窗口仍跟手」，延后不影响平移本身
- **BREAKING**：无

## 明确移出本变更范围

- 不改数据格的双击判定（`ROW_DBLCLICK_SKIP`）与红框绘制
- 不把数据格加进 composable 的 `INTERACTIVE` 排除清单（那会让表格主体区域无法拖拽平移）
- 不给 `useTableDragScroll` 补单测（该共享件当前无测试设施；以两页真机走查验收）
- 已保存页面截图坐标基准（`fix-saved-page-shot-basis` 负责）

## 关联文档

- 需求编号：`PRD-03-设备检查器`
- 既有要求（被违反、本次修复）：`device-inspector-page`「双击标识才在手机画面画红框」
- 共享件使用方：`device-pool`（`DevicePoolView.logic.ts`）与 `device-inspector`（`StructureAnalysisPanel.vue`）

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

（无 —— 规格已要求该行为且不变，`.openspec.yaml` 置 `skip_specs: true`）

## Impact

- `frontend/src/shared/composables/useTableDragScroll.ts`（共享件，1 处位置调整）
- 观感/行为变化：`/inspector` 双击数据格恢复选中与红框（修复）；`/devices` 拖拽平移不得回归（验收项）
- 后端 / 端点 / 路由 / 迁移：零改动
- 恢复方式：`git revert` 单文件；无数据迁移