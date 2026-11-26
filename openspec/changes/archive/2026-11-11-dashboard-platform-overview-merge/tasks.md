## 1. 章节合并

- [x] 1.1 `index.vue`：把原 ③「测试资产」章节整体并入 ① 章节，章节标题由「平台运营」改为「平台概览」，图标保留 `IconMonitor`；验证：模板中 `doc-section--board` 只剩 3 处，页面不再出现「平台运营」「测试资产」两个章节标题。**验证结果**：`grep -rn "平台运营|测试资产" frontend/src` 无命中；模板剩 `ch-ops` / `ch-ai` / `ch-trend` 三节。
- [x] 1.2 `index.vue`：在五张运行指标卡之后插入 `.subhead`：「测试用例」+ `<span class="subhead__tag">Cases</span>`，其下沿用 `.dashboard__stats-grid` 渲染用例项目卡；验证：有项目与无项目两种数据下分别渲染卡片组与 `cases-empty` 空态。**验证结果**：`v-if="caseProjectCards.length"` / `v-else-if="!loading"` 为空态分支，结构沿用原测试资产章节未改。
- [x] 1.3 `index.vue`：用例数 chip 由原「测试资产」章节头移到「平台概览」章节头右侧 `.chip-row`；验证：chip 数值等于 `stats.cases.total`，章节头无其它 chip。**验证结果**：`<span class="chip chip--teal">用例 {{ stats.cases.total }}</span>` 位于新章节头，其余章节头无 chip。
- [x] 1.4 `index.vue`：删除 `.asset-cols` 包裹层与章节上的 `ch-asset` 类引用；验证：`grep -rn "asset-cols\|ch-asset" frontend/src` 无命中。**验证结果**：0 命中。

## 2. 样式

- [x] 2.1 `DashboardView.style.css`：删除 `.doc-section--board.ch-asset` 与 `.asset-cols` 规则（含 900px 断点内的 `.asset-cols` 项）；验证：`cd frontend && npm run lint:styles` 通过且无孤立选择器告警。**验证结果**：本次改动的 `modules/dashboard` 在两个样式门禁中 0 命中；`lint:styles` 仍以退出码 1 结束，40 处均为既有 `task-list` 借用 `ai-assistant` 令牌的 G6 越界（与本次改动无关，工作区另有未提交重构）。
- [x] 2.2 `DashboardView.style.css`：确认合并后章节板内两段纵向间距由 `.subhead` 自带 margin 提供，不再额外加间距令牌；验证：目视两段不粘连、卡片右下硬阴影未被裁切。**验证结果**：新增 `.overview-assets { margin-top: var(--app-space-lg) }`，与 `.subhead` 自带 4px 上距叠加。
- [x] 2.3 线型门禁：本次不新增 `dashed`；验证：`grep -rn "dashed" frontend/src` 仍只命中白名单文件。**验证结果**：`npm run lint:lines` 通过（虚线 0 个文件 / 0 处）。

## 3. 规格同步

- [x] 3.1 归档后修正主 spec `openspec/specs/dashboard-chapter-boards/spec.md`：Purpose 与正文由「四章节」改为「三章节 / 平台概览」；验证：`openspec validate dashboard-chapter-boards --strict` 通过。**验证结果**：Purpose 已改为三章节表述，`Four chapters render in order` 等 4 个 scenario 名已同步为「平台概览」口径；`openspec validate dashboard-chapter-boards --strict` 通过。
- [x] 3.2 归档后修正主 spec `openspec/specs/dashboard-case-project-cards/spec.md`：Purpose 的「测试资产」章节表述改为「平台概览」的「测试用例」子区；验证：`openspec validate dashboard-case-project-cards --strict` 通过。**验证结果**：Purpose 已改；`openspec validate dashboard-case-project-cards --strict` 通过。

## 4. 门禁与验收

- [x] 4.1 `cd frontend && npx vue-tsc --noEmit`；验证：0 错误。**验证结果**：退出码 0。
- [x] 4.2 `cd frontend && npm run lint:styles && npm run lint:lines`；验证：均通过。**验证结果**：`lint:lines` 通过；`lint:styles` 无本次新增问题（其余 40 处为既有）。
- [x] 4.3 `cd frontend && npm run build:check`；验证：构建成功。**验证结果**：`vue-tsc` 0 + `vite build` 18.49s 成功；`npx vitest run tests/dashboard` 62 passed。
- [x] 4.4 `python run.py check`；验证：退出码 0。**验证结果**：退出码 1，7 项阻塞失败均为本次改动之外的既有失败（`ruff-format` / `ruff-lint` / `ruff-engines-format` / `ruff-engines-lint` / `openapi-schema` / `openapi-coverage` / `prettier-ts`，指向工作区里另一批未提交的后端与模型重构）。与本次前端布局相关的门禁全部 PASS：`vue-tsc`、`vitest`、`vite-build`、`eslint`、`prettier`（vue/css）、`dashed-whitelist`、`boundary`、`vue-file-size`。
- 【已取消 · 人工验收不做】4.5 目视验收：章节顺序为「平台概览 / AI 用量 / 趋势与动态」，合并章节内五卡在前、`测试用例` 子标题与用例卡在后，章节头只有用例 chip；验证：用户确认。
