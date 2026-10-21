## 1. 后端：一周口径与当日 4 小时槽

- [x] 1.1 `apps/dashboard/ai_usage.py`：`ai_daily_series` 与 `ai_task_daily_execution` 的 `days` 默认值由 12 改为 7。验证：`python -m pytest tests/graybox/unit/test_dashboard_today_usage.py -q` 通过（含默认 7 天断言），实测 `/api/dashboard/stats/` 的 `charts.ai_tokens.labels` 为 7 项。
- [x] 1.2 `apps/dashboard/ai_usage.py`：新增 `ai_today_usage_slots(user_id)`，返回 `{"labels": [7 个 HH:00], "tokens": [None, 6 项], "cost": [None, 6 项]}`，按 `stat_hour // 4` 分桶，token 取输入 + 输出、费用取 `cost_total` 并量化到 8 位，越界桶丢弃。验证：单测 4 条覆盖「token 与费用跨桶累加」「04 时归入右端窗口」「无用量返回 `[null,0,0,0,0,0,0]`」「默认 7 天」，全部通过。
- [x] 1.3 `apps/dashboard/views.py`：`charts` 增加 `today_usage`（来自 `ai_today_usage_slots`）。验证：`python manage.py check` 无问题；实测响应 `today_usage` 为 `{"labels": [7 项], "tokens": [null,0,0,5148201,0,0,0], "cost": [null,0.0,0.0,2.66413176,0.0,0.0,0.0]}`，无缓存字段。

## 2. 前端：类型与数据映射

- [x] 2.1 `frontend/src/shared/types/dashboard.ts`：新增 `TodayUsageChart` / `TodayUsageChartRaw`，挂到 `DashboardRawData.charts.today_usage`（可选，兼容旧响应）。验证：`npx vue-tsc --noEmit` 通过。
- [x] 2.2 `useDashboardStats.ts`：默认值、`mapStatsResponse`、返回接口三处同步 `todayUsageChart`。验证：`tests/dashboard/p1/DashboardView.logic.spec.ts` 映射断言通过。
- [x] 2.3 `DashboardView.logic.ts`：暴露 `todayUsageSeries`（「Token 消耗」`#4ECDC4` 左轴 / 「费用」`#F7C948` 右轴，`unit` 区分格式）。验证：单测断言两条系列的 name/color/axisIndex/unit 与数据透传。

## 3. 前端：折线卡与布局

- [x] 3.1 新增 `components/TodayUsageChart.vue`：`useECharts` + `type: "line"` 两条系列、7 个刻度、`null` 空点、双纵轴（左 token 紧凑单位 / 右 `x 元`）、tooltip 对 `null` 显示 `—`、不平滑（离散桶不平滑失真）、`min-height: 220px`。验证：`npm run lint:styles` 通过（画布字号仍 18 处未增），页面渲染为双折线双轴。
- [x] 3.2 `index.vue`：新增 `.dashboard__trends--single` 整行卡「今日 Token 与费用（每 4 小时）」，`sketchToneAt(4)` / `sketchTiltAt(4)`；章节副标题同步改「近 7 日」。验证：截图确认第三行卡占满整行、与既有卡同款钉板样式。
- [x] 3.3 `DashboardView.style.css`：新增 `.dashboard__trends--single { grid-template-columns: 1fr; }` 并纳入 `@media (max-width: 960px)`。验证：`npm run lint:styles` 通过；截图 1686 宽下卡宽 1306px。

## 4. 文档、门禁与验收

- [x] 4.1 `dev_docs/DEV_TEST/接口文档/API-仪表盘.md`：三处「近 12 天」改「近 7 天」，示例改 7 项，补 `today_usage`（含 `current` 与「未走完为 null」）。验证：该文档内检索「近 12」无匹配。
- [x] 4.2 前端门禁：`npx vue-tsc --noEmit` 通过、`npm run lint:styles` 通过、`npm run build` 通过；后端 `python manage.py check` 与 `python -m ruff check apps/dashboard/ tests/graybox/unit/test_dashboard_today_usage.py` 通过。
- [x] 4.3 人工验收：真实页面确认三张柱图横轴 7 个刻度、折线卡整行位于费用图下方、7 个 4 小时刻度不叠字、token 与费用双线双轴、图例无缓存命中、折线只画到当前时刻。验证：Playwright 截图 `temps/visual-check/trends.png`，hover 读到「11:19 · 进行中 / 5.1M / 2.66 元」，控制台 0 error。

## 5. 验收修正：按时间进度绘制 + 跨零点换天

- [x] 5.1 后端 `ai_today_usage_slots` 改为「按时间进度出数」：只有走完的窗口才挂刻度，未走完/未开始为 `null`，进行中窗口由 `current: {hour, tokens, cost}` 返回；整点边界时 `current` 为 `null`；支持注入 `now` 便于测试。验证：5 条单测覆盖「11:05 时 12:00 及以后必须为 null」「走完后归入右端刻度」「整点无 current」「空数据 windows=0」「默认 7 天」，全部通过。
- [x] 5.2 前端折线改用 0–24 数值轴（`interval: 4`）：末端点落在当前时刻，未来刻度无点；tooltip 对已完成刻度显示窗口区间、对末端点显示「进行中」。验证：`helpers/hourlyPoints` 单测（点序列 4 条）通过；页面 hover 实测三处文案正确。
- [x] 5.3 新增 `composables/useMidnightRefresh`，`index.vue` 挂载后按「距下一个本地 00:00:05」定时刷新，跨零点自动切到新的一天；卸载清定时器。验证：单测覆盖「剩余毫秒含 5 秒余量」「跨零点触发一次」「卸载后不再触发」，共 3 条通过。
- [x] 5.4 同步更新 delta spec 与接口文档：`tokens`/`cost` 未走完为 `null`、`current` 语义、整点边界、跨零点换天。验证：`openspec validate --strict` 通过。

## 6. 验收修正：逐小时取数 + 平滑曲线 + 点击查看

- [x] 6.1 后端 `ai_today_usage_slots` 改为逐小时落桶：`tokens`/`cost` 各 24 项（下标 = 小时 0–23），只给已走完的小时，`current` 指向进行中的那一小时；`labels` 字段移除（横轴刻度由前端按 0–24 渲染）。验证：5 条单测覆盖「逐小时值正确」「11 点进行中时 11 点及以后为 null」「整点无 current」「空数据」「默认 7 天」。
- [x] 6.2 前端点序列改为第 h 小时落在 h+1 时刻，`current` 仅在**已有消耗**时才追加为末端点（避免刚过整点掉到 0 的假谷底）。验证：`helpers/hourlyPoints` 8 条单测通过。
- [x] 6.3 曲线改平滑（`smooth: 0.25`），横轴仍 0–24 每 4 小时一个刻度；`tooltip.triggerOn = "mousemove|click"`，悬停与点击都能读出时间 + token + 费用。验证：Playwright 实测 hover 与 click 均显示「11:00（10:00–11:00）Token 消耗：3.9M 费用：1.98 元」。
- [x] 6.4 卡片标题改「今日 Token 与费用（逐小时）」，与数据粒度一致。验证：页面标题文案。
- [x] 6.5 同步 delta spec（逐小时、平滑、点击/悬停、任意时刻）与前端类型/默认值。验证：`openspec validate --strict` 通过，`vue-tsc` 与 `npm run build` 通过。
