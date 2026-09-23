## 1. 由规格收敛导出的代码修正（唯一代码改动）

- [x] 1.1 `frontend/src/modules/device-inspector/components/StructureAnalysisPanel.vue` 的 `.sap-label-hit` 与 `.sap-name-cell` 内 `padding: 0 8px` 改为 `padding: 0 var(--app-space-sm)`；验证：该文件 `padding: 0 8px` 命中 0（改前 2 处），`var(--app-space-sm)` 现 6 处（含 `.sap-sections` / `.sap-chip` 等既有 4 处未被改动）
- [x] 1.2 改前确认该文件无在途未保存编辑；验证：基线记录 `StructureAnalysisPanel.vue` mtime `2026/9/21 14:58:13`、`SavedPagePicker.vue` mtime `2026/9/21 15:13:38`；`git diff --stat` 该目录 8 文件 / +503 −458 行
- [x] 1.3 真机确认等值；验证：Playwright（系统 Edge 通道）登录 admin → `/inspector` → 「已保存页面」载入含 5 行的页面，读数 `.sap-label-hit` = `0 / 8px / 0 / 8px`、`.sap-name-cell` = `0 / 8px / 0 / 8px`（与改前 `0 8px` 逐一相等）；截图 `temps/inspector-padding-check.png`、脚本 `temps/inspector-padding-check.mjs`。附注：该次走查另有 6 条 404，均为该历史页面引用的旧截图/缩略图文件已不存在（既有数据条件，与本改动无关，另行登记）

## 2. 门禁

- [x] 2.1 `openspec validate align-inspector-spec-drift --strict`；验证：输出 `Change 'align-inspector-spec-drift' is valid`，`specs/` 下恰有 3 个 delta（`device-inspector-page` / `frontend-doodle-button` / `frontend-l4-data-surface`）
- [x] 2.2 **防复发·跨规格一致性检索**（归档写回后执行）：在 `openspec/specs/`（live 规格）逐个检索 `每页 8 行`、`PAGE_SIZE_OPTIONS=[8]`、`固定 8 行`、`外层容器横向滚动`、`工具条与设备选择触发键的底色 SHALL 按可用性分配`、`唯一视图）点击一行`，命中必须为 0；`openspec/changes/`（在途变更自述）与 `openspec/changes/archive/`（历史记录）中的命中不参与判定，但须逐条说明归属；验证：归档写回后实测 6 项在 `openspec/specs/` 命中全为 0（`每页 8 行` / `PAGE_SIZE_OPTIONS=[8]` / `固定 8 行` / `外层容器横向滚动` / `工具条与设备选择触发键的底色 SHALL 按可用性分配` / `唯一视图）点击一行`）；同名声明在归档与在途变更文档中的命中已逐条归属为历史记录或本变更自述
- [x] 2.3 **前置条件**：`frontend/src/modules/device-inspector/components/SavedPagePicker.vue` 的 `border-radius: 999px` 改为 `var(--app-radius-pill)`（违反 `frontend-l0-design-tokens`「可见盒子的圆角取自不对称规格令牌」）；验证：`frontend/src` 内 `999px` 命中 0；`npm run lint:styles` 批 4 由红灯转为「通过」；真机读数该胶囊计算圆角 `4px 10px 6px 8px`（= `--radius-pill`，与 l0 的「可见盒子不对称」场景一致）
- [x] 2.4 `npm run lint:styles`；验证：`LINT_EXIT=0`，批 1 / 1b / 2 / 3 / 4 全通过
- [x] 2.5 `npx vite build`；验证：退出码 0，`✓ built in 1m 12s`。附注：该命令在 workspace-write 沙箱下因 esbuild 子进程管道 stdio 被拒（`spawn EPERM`）失败一次，经放宽沙箱后原样重跑通过；此后会话文件策略已放宽为 full-access

## 3. 归档前准备

- [x] 3.1 合并（已实际写回 3 份主规格）：把 3 份 delta 分别并入对应主规格，逐份核对（1）无重复 `### Requirement` 名、（2）被 MODIFIED 的 requirement 旧文已整段替换（尤其 `:46-49` / `:93-97` / `:85` / `:297` / `:316` 五处）、（3）新增场景 `Select trigger is not part of the availability tone` 已落入 `frontend-doodle-button`；验证：6 条合并结果各命中 1 处（`该 capability 不钉具体行数` / `本 capability 不约定手势` / `元素表自身的横向滚动容器承载` / `落在 T0 刻度上的取值` / 新增场景 `Select trigger is not part of the availability tone` / `设备选择触发键不适用这套可用性配色`）；三份主规格 requirement 数 8 / 15 / 5，重复名 0
- [x] 3.2 与并行变更划界；验证：`align-inspector-spec-drift` 动 3 份规格 + `StructureAnalysisPanel.vue`（2 行）+ `SavedPagePicker.vue`（1 行，任务 2.3）；`purge-inspector-dead-code` 动 `constants.ts` / `store.ts` / `ScreenshotView.vue` / `ScreenshotView.css` / `SaveToElementsDialog.vue`，两份 Impact 交叉比对无同名文件冲突（清退单不含 `StructureAnalysisPanel.vue`）；清退单 tasks 4.2 的 `lint:styles` 前置条件已由本单 2.3 消除
