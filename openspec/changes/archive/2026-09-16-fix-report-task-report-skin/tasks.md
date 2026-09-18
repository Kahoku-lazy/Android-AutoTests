## 1. 复用共享件替换私有实现

- [x] 1.1 性能统计 5 个指标块改用共享 `KpiCard`（含 `value` / `label` / `color` / `shape`），删除 `class="kpi-card perf-stat-item"` 借用标记与 `.kpi-dot/.kpi-value/.kpi-label`；验证：检索 `perf-stat-item` / `kpi-card` / `kpi-dot` / `kpi-value` / `kpi-label` / `num-fail` / `num-pass` 命中数为 0
- [x] 1.2 执行历史表 `#cell-rate_bar` 改用 `<RateBar :rate="record.rate ?? 0" :show-fail="(record.failed ?? 0) > 0" />`，删除 `.rate-cell/.progress-bar/.p-pass/.rate-text` 标记；验证：写法与 `index.vue:338` 一致；Chromium 实测旧 `.progress-bar` / `.p-pass` 标记高度为 `0px`（复现"进度条不可见"），改用 RateBar 复用共享件自带的可见轨道
- [x] 1.3 用例明细整页空态由 `.empty-note` 改用共享 `EmptyState`；验证：检索 `empty-note` 命中数为 0
- [x] 1.4 补 `RateBar` 与 `EmptyState` 的 import；验证：`npm run typecheck` 未新增任何与 `TaskReport` / `report-generator` 相关的报错

## 2. 任务信息条与零散样式

- [x] 2.1 任务信息条模板类名由 `.task-meta-bar` / `.task-meta-item` 改为本文件已定义的 `.task-meta-card` / `.meta-item`；验证：检索 `task-meta-bar` / `task-meta-item` 命中数为 0，且 Chromium 中信息条容器样式生效
- [x] 2.2 补 `.full-width` 与 `.conclusion-text` 样式（取令牌）；验证：两类的规则已在本作用域定义

## 3. 用例明细 / 失败分析样式补齐

- [x] 3.1 补齐 `.case-list/.case-card/.case-card.expanded/.case-header/.case-card.bug-card .case-header/.case-header:hover/.case-expand-icon/.case-card.expanded .case-expand-icon/.case-id-badge/.case-title-area/.case-title-text/.case-status-text/.case-stats/.stat-total/.stat-pass/.stat-fail/.case-body`；验证：Chromium 实测卡片边框 `2px`、`.case-header` 悬停底色由透明变为 `rgb(255,254,245)`、展开箭头带 `transform` 过渡
- [x] 3.2 补齐 `.step-list/.step-card/.step-strip/.step-card.step-done .step-strip/.step-body/.step-header-row/.step-index/.step-type-tag/.step-desc/.step-xpath/.step-empty`；验证：Chromium 实测 `.step-strip` 宽 `4px` 且底色 `rgb(107,203,119)`（`--c-device`），步骤条可见
- [x] 3.3 补齐 `.bug-card/.bug-header-sub/.bug-meta/.bug-meta-label/.bug-meta-value/.step-fail-reason`，并移除 `.step-fail-reason` 上会压过新规则的行内 `style="margin: 0 22px 12px; padding: 8px 12px;"`；验证：两类均有本作用域规则，文件内不再出现该行内 style
- [x] 3.4 补齐 `.mono` / `.time-text` / `.kpi-sub` / `.perf-stats-section` / `.perf-stats-title` / `.perf-stats-grid` / `.table-card` / `.task-report-table`；验证：全部有本作用域规则
- [x] 3.5 新增 CSS 全部取令牌（不对称 `--app-radius-*`、扁平 `--app-shadow-*`、字号不低于 `--app-size-xs`、间距优先 `--app-space-*`）；验证：`npm run lint:styles` 的"消费位置裸色字面量"仍为 **33 处**（与改动前一致，未新增）；新增行不含任何 hex / rgb / 圆角 / 阴影字面量

## 4. 未找到分支回到骨架

- [x] 4.1 `v-else`「任务未找到」分支改为 `.doc-page .wb-shell .task-report-page` + `WorkbenchHeader` + `.doc-body` + 共享 `EmptyState`（返回按钮带 `wb-btn`）；验证：检索 `not-found` 命中数为 0，分支 DOM 含骨架与主题作用域类

## 5. 门禁与验收

- [x] 5.1 `cd frontend && npm run lint:styles` 退出码 0；验证：批 2 / 批 3 硬门禁全绿
- [x] 5.2 `npx vite build --mode development` 通过（`built in 40.51s`，退出码 0，需放宽沙箱以允许 esbuild 启动子进程）；`npm run typecheck` 报错分组为 `tests/dashboard/p0|p1`（12+8+7）、`src/modules/device-inspector/store.ts`（4）、`src/modules/case-manager/components/ProjectTree.vue`（3）—— 后两者所在文件**未被本变更（或变更 1）修改**（`git diff --name-only` 可核），属既有无关报错，本变更未新增
- [x] 5.3 Playwright + Chromium 渲染断言（加载真实 `tokens.css` + `style.css` + `workbench-theme.css` + 本页 `<style>` 源码与复刻 DOM）：7 项断言全 PASS —— 含**改动前反证**（旧 `.progress-bar` / `.p-pass` 高度实测 `0px`，即进度条原本不可见）；`.case-card` 边框 `2px`、`.step-strip` 宽 `4px` 且呈 `--c-device` 色、`.case-id-badge` 底色不透明、`.case-expand-icon` 含 `transform` 过渡、`.case-header` 悬停换底。**限制**：契约级验证，未加载真实运行中的应用与数据
- [x] 5.4 模板类 → CSS 规则对照（对应 `frontend-l2-page-region`「No L2 declaration without a consumer」）：脚本提取模板静态与动态类共 **58 个**，报出的 5 处缺口经逐名核验全部为 `:class` 对象语法解析假阳性（`expanded` 与动态返回的 `badge-pass/badge-fail/badge-stopped` 均有本作用域规则，已单独断言 `DEFINED`）；**真实缺口为 0**。另删除一条无模板消费方的死规则 `.run-meta`
- [x] 5.5 `git diff --name-only` 的本变更部分仅含 `frontend/src/modules/report-generator/TaskReport.vue` 一个文件（+80 / -46）；工作区其余改动属其他在飞工作，未触碰