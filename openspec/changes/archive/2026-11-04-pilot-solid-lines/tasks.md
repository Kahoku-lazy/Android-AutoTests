## 1. 任务详情（task-list）

- [x] 1.1 `CaseImportCard.vue`：容器框 `2.5px dashed` + `2px` 圆角 + 硬投影 → `1px solid` + `--app-radius-lg`，去投影。验证：`npm run lint:lines` 中该文件不再出现。**验证结果**：已改；该文件不在门禁输出中。
- [x] 1.2 `TaskMediaThumb.style.css`：外框与占位两处虚线 → `1px solid`（占位改浅线）。验证：lint:lines 通过。**验证结果**：两处已改。
- [x] 1.3 `StepLogCheck.style.css` / `StepLogEvidence.style.css` / `TaskAttemptCard.vue`：`1.5px dashed` → `1px solid`（颜色沿用 `--ai-warm-border`）。验证：lint:lines 通过。**验证结果**：三处已改；`--ai-warm-border` 跨边界借用属既有问题（批 3 仍 50 处，未增加）。

## 2. 仪表盘（dashboard）

- [x] 2.1 `DashboardView.style.css`：`.dashboard__footer` 与 `.usage-empty` 虚线改 1px 实线。验证：lint:lines 通过。**验证结果**：已改；试点期的 `.dashboard-workbench .ac-card` 覆盖块在全量迁移后删除（全局已实线）。
- [x] 2.2 `ActivityTimeline.vue`：行分隔 `1px dashed` → `1px solid`。验证：lint:lines 通过。**验证结果**：已改。

## 3. 全量迁移（经确认从试点扩为全量）

- [x] 3.1 全局卡片壳：`workbench-theme.css` 的 `.wb-shell .ac-card` 由 `2.5px dashed` + 硬投影 + 微倾改为 `1px solid var(--color-ink-79)` + `--app-radius-lg` + 无投影 + 无微倾；删除 `.ac-card--dashed` 修饰块与 `AppCard.vue` 的 `type` 死代码。验证：`npm run lint:lines` 通过。**验证结果**：全局 11 个 AppCard 实例一并实线化；`type` prop 已随调用点（0 处）删除。
- [x] 3.2 对话框与表纸：`tokens.css` 的 `--comp-sheet-border` / `--comp-dialog-border` 改 `1px solid var(--color-ink-79)`，`style.css` 的 `.el-dialog` / `.el-drawer` 兜底值同步。验证：lint:lines 通过。**验证结果**：已改，兜底不再含 `dashed`。
- [x] 3.3 其余组件：`SketchCard`、`DoodleNote` 基类、`CaseFileSheet`、`VoiceConsole`、`TranscriptPanel`、`WifiPortPanel`、`PageFlowNode`、`WorkflowDirTree`、`DisconnectDialog`、`LoginView` 改实线；`AgentRouteCard` 自持 `2.5px dashed`（白名单）。验证：lint:lines 通过。**验证结果**：虚线收口到只剩 `KpiCard.vue`（1 处）与 `AgentRouteCard.vue`（1 处）。
- [x] 3.4 门禁基线清零：`check-dashed-whitelist.mjs` 的 `BASELINE` 清空，任何非白名单文件出现 `dashed` 立即阻断。验证：`npm run lint:lines` 显示 `0 个文件 / 0 处`。**验证结果**：输出 `虚线出现在 0 个文件 / 0 处（白名单组件 2 个，存量登记 0 个）`。

## 4. 门禁与验收

- [x] 4.1 前端门禁：`npx vue-tsc --noEmit`、`npm run build:check`、`npm run lint:lines` 通过。验证：命令输出通过。**验证结果**：`vue-tsc` 0；`build:check` 29.7s 通过；`lint:lines` 通过。
- [x] 4.2 全量前端测试：`npx vitest run` 全绿。验证：76 文件 463 用例通过且无未处理错误。**验证结果**：首跑 75 文件 458 passed 但报 1 个 `listOnTimeout`；复跑 76 文件 463 passed、退出码 0，判定为首跑的既有定时器收尾竞态，与纯样式改动无关。
- [x] 4.3 页面人工验收：任务详情、仪表盘、助手看板（虚线白名单）、对话框、表纸、工作流节点、登录页各看一遍。验证：用户目视确认。**验证结果**：用户以「归档」指令确认通过（未再单独描述目视过程）。
