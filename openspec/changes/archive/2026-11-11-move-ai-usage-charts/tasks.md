## 1. 搬移图表

- [x] 1.1 `index.vue`：「每日 Token 用量」与「每日 DeepSeek 费用（元）」两块 `AppCard` 从 `ch-trend` 移入 `ch-ai`，包在 `ch-ai__body` 之后的 `.ai-usage-trends` 容器里，容器首行为 `.subhead`「用量趋势」+ `Usage` tag；验证：`ch-ai` 内自上而下为 用量卡片组 → 子标题 → 按日两图。**验证结果**：`.ai-usage-trends` 内顺序为 `.subhead` → `.dashboard__trends--ai`（两张按日图）→ `--single`（今日折线）→ `--single`（Voice）。
- [x] 1.2 `index.vue`：「今日 Token 与费用（逐小时）」整行卡随同移入该容器，位置在按日两图之后；验证：`TodayUsageChart` 仍收到 `todayUsageSeries`，卡片仍整行。**验证结果**：`todayUsageSeries` prop 未改，卡在 `.dashboard__trends--single` 内整行。
- [x] 1.3 `index.vue`：「Voice 来源 Token 消耗」卡（含 `voice-usage-summary` 与 `usage-empty` 空态）随同移入，位置在今日折线之后；验证：Voice 无数据时空态仍渲染。**验证结果**：`v-if="voiceUsageLabels.length"` 与 `v-else` 空态块整体搬移，未改条件。
- [x] 1.4 `index.vue`：从 `ch-trend` 删除上述三块图，仅保留「助手任务卡 + 任务执行结果」一行两列、`最近动态` 子标题与 `ActivityTimeline`；验证：`ch-trend` 内不再出现 token / 费用 / Voice 相关文案。**验证结果**：`ch-trend` 内只剩 `.dashboard__trends`（0/1 号 tone）、`最近动态` 与 `ActivityTimeline`。

## 2. 样式

- [x] 2.1 `DashboardView.style.css`：新增 `.ai-usage-trends { margin-top: var(--app-space-lg); }`；验证：`cd frontend && npm run lint:styles` 无本次新增问题。**验证结果**：新增规则只引用已声明令牌；样式门禁输出中 `dashboard` 0 命中（其余 40 处为既有 task-list G6 越界）。
- [x] 2.2 确认 `.dashboard__trends` / `--ai` / `--single` 与 960px 断点在 `ch-ai` 内同样生效；验证：窄屏下三行图各退为单列。**验证结果**：直接复用原有三个类，未新增断点；960px 规则对所有 `.dashboard__trends*` 生效，与所在章节无关。

## 3. 规格同步

- [x] 3.1 归档后修主 spec `openspec/specs/dashboard-trend-charts/spec.md` 的 Purpose：图表分属「AI 用量」与「趋势与动态」两个章节；验证：`openspec validate dashboard-trend-charts --strict` 通过。**验证结果**：Purpose 已改为两章节口径；`openspec validate dashboard-trend-charts` 为 valid（`--strict` 仍因既有「requirement 文本 >500 字符」警告非零，属存量）。
- [x] 3.2 归档后修主 spec `openspec/specs/model-usage-ledger/spec.md` 与 `dashboard-ai-usage` 的 Purpose（如有章节表述）；验证：两份 spec `--strict` 通过。**验证结果**：`dashboard-ai-usage` Purpose 已补「用量趋势」并把「平台运营章节」改为「平台概览章节」；顺手把 `model-usage-ledger` 遗留的 `TBD` Purpose 补成实际用途。两者 validate 均为 valid（长文本警告为存量）。

## 4. 门禁与验收

- [x] 4.1 `cd frontend && npx vue-tsc --noEmit`；验证：0 错误。**验证结果**：退出码 0。
- [x] 4.2 `cd frontend && npm run lint:styles && npm run lint:lines`；验证：通过（本次新增 0 问题）。**验证结果**：`lint:lines` 通过（虚线 0 处）；`lint:styles` 本次 0 新增，整体仍为既有 40 处 G6。
- [x] 4.3 `cd frontend && npm run build && npx vitest run tests/dashboard`；验证：构建成功、62 passed。**验证结果**：`vite build` 14.65s 成功；`vitest` 7 files / 62 tests 全过。
- [ ] 4.4 `python run.py check`；验证：前端相关门禁全 PASS，其余失败逐条说明是否既有。**验证结果**：退出码 1；前端 6 项全 PASS（`vitest` / `vite-build` / `prettier` / `eslint` / `dashed-whitelist` / `vue-tsc`），另 `boundary` / `vue-file-size` / `mock-data` 亦 PASS。7 项失败与本次无关且与上一次基线完全相同：`ruff-format` / `ruff-lint` / `ruff-engines-format` / `ruff-engines-lint` / `openapi-schema` / `openapi-coverage` / `prettier-ts`，均指向工作区里另一批未提交的后端与模型重构。
- [ ] 4.5 目视验收：「AI 用量」章节内四张图顺序与子标题正确；「趋势与动态」只剩任务图与最近动态；验证：用户确认。
