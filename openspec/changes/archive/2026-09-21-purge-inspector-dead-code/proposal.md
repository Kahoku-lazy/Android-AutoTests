## Why

设备检查器模块（`frontend/src/modules/device-inspector/`）残留一批**零消费死代码**与**无效设计代码**：零引用常量、只写不读的 store 状态、逐条死 CSS、对 SVG 无效的 CSS 声明、不可达兜底分支、名实不符的多余导出。它们不影响运行，但会让静态检索（「这个常量谁在用」）持续给出假信号，也让后续的样式/令牌检索无法区分「有意登记项」与「历史残留」。本变更不改变任何可观察行为，属纯清退，故 `.openspec.yaml` 置 `skip_specs: true`。

## What Changes

- 删除 `constants.ts` 两个零引用导出：`TABLE_HEADER_HEIGHT_PX` / `TABLE_ROW_HEIGHT_PX`（模块内 0 消费；设备管理页用的是自己 `device-pool/constants.ts` 的同名常量）
- 删除 `store.ts` 的 `analyzing`（声明 / `analyzeSnapshot` 内置位 / `return` 暴露，全仓无读点）
- `store.ts`：从 `return` 中移除 `devices` 的对外暴露（ref 本体保留，`availableDevices` 依赖它）
- `store.ts`：`KEY_DISABLED_MESSAGE` 去掉 `export`（注释称「index.vue 与 CaptureForm.vue 共用」，实际两处都走 `notifyKeyUnavailable()`，无人 import；常量本体与文案唯一真相源保留）
- `store.ts`：删除 `toggleCheck` 中不可达的 `row.__uid` 兜底（全仓仅此 1 处出现，无任何产出方）
- 删除两条逐条死 CSS：`ScreenshotView.css` 的 `.no-signal--error .no-signal__title`、`SaveToElementsDialog.vue` 的 `.save-hint`
- 删除 `ScreenshotView.css` 中 `.no-signal__icon` 的无效声明 `font-size: var(--app-size-2xl)`（该处图标是 `<IconDevice :size="32" />`，SVG 由 `width/height` 属性定尺，字号不参与；`opacity` 保留）
- **BREAKING**：无

## 本变更范围的两处调整（评审后）

- **`snapshotTotal` 移出清退范围**：它不是纯死状态，而是「快照总数」这一真实信息的载体（dev 库 309 条、抽屉只展示 100 条且无提示）。改由并行变更 `fix-inspector-state-fidelity` 消费（显示「共 N 条 · 已显示最近 M 条」），本变更不再删除它。
- **`ScreenshotView.vue` 的 watcher 合并移出本变更**：该文件同时被 `fix-saved-page-shot-basis` 触及（尺寸基准），且合并的语义（选中→重绘+滚动 / 清空→重绘）与那张单的真机走查是同一次；为免两单同文件交叉与重复走查，watcher 合并移入该单。本变更因此**不再触及 `ScreenshotView.vue`**，只留 `ScreenshotView.css`。

## 明确移出本变更范围

- 已由 `align-inspector-spec-drift`（已归档 2026-09-21）收敛的设计漂移：每页行数（8→7）、设备选择触发键底色（白底）、行选中手势（双击数据格）、横向滚动承载者（元素表自身滚动容器）、间距按 T0 刻度分层 —— 均已在 live 规格与代码两侧对齐，本变更无需再动
- 行为缺陷：已保存页面回看的 `alias` 显示与只读改名（`fix-inspector-saved-page-alias`）、错误原因呈现与重试（`fix-inspector-state-fidelity`）、截图坐标基准（`fix-saved-page-shot-basis`）、悬空媒体 404（待决策）
- **`options: PAGE_SIZE_OPTIONS` 惰性传参：经评审保留**。该参数确无运行时作用（调用方不消费 `PAGE_SIZE_OPTIONS` / `setPageSize`），但 live 要求 `PAGE_SIZE_OPTIONS` **仍须声明在 `constants.ts`**；若去掉这次传递，该常量将变成「规格要求存在、代码零消费」的导出，未来死代码扫描会再次误判并可能被误删。保留这一处传递即「登记项 → 唯一分页实现」的显式接线
- `StructureAnalysisPanel.vue` 行数超出 500 行拆分红线（拆分需动结构层，另开）
- `SavedPagePicker.vue` 读失败仅 `console.error`（已由 `fix-inspector-state-fidelity` 的错误净化口径覆盖到读路径，本变更不重复处理）

## 关联文档

- 需求编号：`PRD-03-设备检查器`（本次为纯死代码清退，无需求变更）
- 须保持成立的既有能力：`device-inspector-page`、`frontend-l4-data-surface`（本次不修改任何 spec delta；已逐条检索确认删除项未被任何 live spec 引用）
- **依据的既有要求**：`frontend-l2-page-region`「No L2 declaration without a consumer」——「模块常量不得存在零 import 的导出」。本次删除的两常量（零 import）与去掉 `export` 的 `KEY_DISABLED_MESSAGE`（零 import）正属该条；删除后 `constants.ts` 的其余导出仍全部被 import。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

（无 —— 无 spec 级行为变化，`.openspec.yaml` 置 `skip_specs: true`）

## Impact

- 前端 4 个文件（逐项见 What Changes）：
  - `modules/device-inspector/constants.ts`（删 2 个零引用常量）
  - `modules/device-inspector/store.ts`（删 `analyzing`、`devices` 暴露、`KEY_DISABLED_MESSAGE` 的 `export`、`__uid` 兜底）
  - `modules/device-inspector/components/ScreenshotView.css`（删 1 条死规则 + 1 条无效声明）
  - `modules/device-inspector/components/SaveToElementsDialog.vue`（删 1 条死规则）
- 后端 / 接口 / 路由 / 依赖 / 迁移：零改动
- 观感变化：无（删除项均不在任何渲染路径上）
- 同文件协作：`store.ts` 同时被 `fix-inspector-state-fidelity`（错误分支 / `deleteSnapshot` / `viewSavedPage`）触及，改动点与本次不同行；应用顺序不影响结果
- 测试范围：该模块当前 0 单测，故以静态零引用复核 + `lint:styles` + `vite build` + `typecheck` + 真机空态/弹窗渲染核查验收
- 恢复方式：全部为删除，`git revert` 或 `git show HEAD:<path>` 即回滚；无数据迁移