## Context

动机见 `proposal.md - Why`。已核对的现状：

- `ai_daily_series(user_id, days=12)` 与 `ai_task_daily_execution(user_id, days=12)` 各自用 `days` 生成 `MM/DD` 标签；`views.py` 把前者拆成 `charts.ai_tokens` 与 `charts.deepseek_cost`，把后者放进 `charts.execution`，三张图共用同一段日期区间但各自构造标签。
- 前端三张图分别是 `TrendBarChart`（执行）与 `SeriesBarChart`（token / 费用），后者 `type: "bar"` 写死，不接受图表类型参数。
- `AIUsageHourly` 已有 `stat_date` + `stat_hour`（0–23）两个维度与 `input_tokens`/`output_tokens`/`cost_total`，按 4 小时窗口聚合不需要建表或迁移。
- `USE_TZ = False`、`TIME_ZONE = "Asia/Shanghai"`，`timezone.now()` 即本地时间，`today_start.date()` 就是本地日期，与写入侧的 `stat_date` 同口径。
- 折线写法在仓内有先例（`report-generator` 的 `PassRateTrendChart`：`type: "line"` + `LinearGradient` 面积 + `useECharts`）；费用格式化已有 `formatSignificant(value, 3)`（`shared/animations.ts`）。

## Goals / Non-Goals

**Goals:**

- 三张柱状图横轴统一收成近 7 天，且**只有一个标签来源**（后端同一函数生成）。
- 新增「今日 Token 与费用（每 4 小时）」折线卡：token 与费用两条线、双纵轴，数据都从小时用量表现算。
- 空数据可分：无用量时折线为空而非错误态。

**Non-Goals:**

- 不改 `AIUsageHourly` 表结构、不加迁移、不新增写入路径。
- 不在该图画缓存命中（按需求排除）；也不加缩放条（`dataZoom`）或导出。
- 不把「每 4 小时用量」并入按日柱图，也不改按日柱图的系列（总 Token / 缓存命中）。
- 不改「任务执行结果」面板。

## Decisions

1. **后端默认 `days=7`，而不是前端截断**
   理由：三张图的标签由后端生成；只改前端会让接口文档、spec 与其它调用方继续按 12 天口径。两个函数默认值同时改，`views.py` 无需传参。备选（前端 `slice(-7)`）被否：接口仍吐 12 天，口径分裂。

2. **按时间进度出数：已走完的窗口才挂刻度，进行中的窗口单独给 `current`**
   7 个刻度是 6 个窗口的边界。窗口值挂在窗口右端（`04:00` = `[00:00,04:00)`），且**只有窗口走完才挂**；窗口未走完/未开始时该刻度必须是 `null`，否则会出现「11:05 时 12:00 已有数」的误导。进行中的窗口用 `current: {hour, tokens, cost}` 单独返回，前端把它画在 `hour`（当前时刻）处作为折线末端——这样折线永远止于「现在」，而不是止于某个未来的刻度。`00:00` 没有前序窗口恒为 `null`。备选（把进行中窗口的数挂在右端刻度上）被否：那正是用户看到的错；备选（进行中的窗口也不显示）被否：白天大部分时间图上没有末端点，等于看不到今天已消耗多少。

3. **横轴用 0–24 的数值轴，不用 7 个类目轴**
   要画「末端在当前时刻」，点必须能落在 `11.08` 这种非整刻度位置，类目轴做不到（只能落在 7 个标签之一）。因此 `xAxis.type = "value"`、`min 0`、`max 24`、`interval 4`，标签格式化回 `HH:00`，视觉上仍是 7 个 4 小时刻度。备选（类目轴 + 把末端点钉在下一个刻度）被否：就是现在这个 bug 的成因。

4. **窗口边界左闭右开、按 `stat_hour` 整除 4 分桶**
   `bucket = stat_hour // 4`，`tokens[bucket + 1] += 输入 + 输出`，`cost[bucket + 1] += cost_total`（Decimal 累加后统一量化到 8 位）。`04` 时归入 `[04,08)`，与 spec 场景一致；一次 `values("stat_hour").annotate(Sum(...))` 查完，不逐窗口查询。

5. **折线卡独占一行，新增 `.dashboard__trends--single`**
   现有 `.dashboard__trends--ai` 是两列等宽，塞第三张会把 7 个刻度挤到约 120px 宽、`00:00` 与 `04:00` 直接叠字。整行宽后单卡约 1300px，刻度间距足够。栅格类复用 `.dashboard__trends`，只覆盖列数；`@media (max-width: 960px)` 已把该行的列数降为 1。

6. **新建模块私有 `TodayUsageChart.vue`，不改 `SeriesBarChart`**
   理由：`SeriesBarChart` 被两处柱图共用，给它加 `type` 参数会让「一个组件两套皮肤」，且折线特有的 `symbol`/`areaStyle`/双轴会污染柱图分支。折线组件约 120 行，模块内私有、不跨模块复用。备选（给 `SeriesBarChart` 加 `chartType`）被否。

7. **双纵轴：token 走左轴（紧凑单位），费用走右轴（元，3 位有效数字）**
   token 量级是百万级、费用是 0.x 元级，同轴会让费用线压成一条贴底的直线。左轴沿用柱图的 `compactNumber`；右轴与 tooltip 复用 `formatSignificant(v, 3)`，与 KPI 卡「总费用」的显示口径一致。tooltip 用自定义 `formatter` 逐系列渲染，进行中的末端点标「进行中」，其余标窗口区间 `[起, 止)`。

8. **颜色沿用既有语义：token 青绿 `#4ECDC4`、费用柠黄 `#F7C948`**
   与「每日 Token 用量」的总 Token 系列、「每日 DeepSeek 费用」柱图同色，读者不必再学一套语义；ECharts Canvas 不吃 CSS 变量，仍写字面量并按仓内注释惯例标注对应 token（`#4ECDC4 = --c-case`、`#F7C948 = --c-dashboard`）。备选（另起天蓝 `--c-workflow`）被否：同一页面同一指标两种颜色，反而增加理解成本。

9. **跨零点自动换天：前端定时器刷新，后端不缓存**
   仪表盘是长驻页面，`today_usage` 的「今天」由服务端 `timezone.now()` 决定，页面不刷新就一直停在旧日期。新增模块内 `useMidnightRefresh(callback)`：挂载时按「距下一个本地 00:00:05 的毫秒数」排一个 `setTimeout`，触发后调 `refreshData()` 并重新排期；`onUnmounted` 清定时器。备选（轮询每 60s 比较日期）被否：一天一次的事件不需要高频轮询；备选（后端返回 `server_time` 让前端判断）被否：前端本地日期就是「用户眼中的今天」，还省一个字段。

## 模块防火墙自检

- 跨 App import：`apps/dashboard/ai_usage.py` 已只读 `apps.ai_assistant.api`（`filter_agents_for_user`、`resolve_assistant_name`）与 Model，本次不改这层边界，仍无 service/runner/consumer/state_machine 跨 App import。
- 所有 INSERT/UPDATE/DELETE 收敛到各 App 的 `api.py`：本次为纯只读聚合，仪表盘不写库。
- 前端不直连数据库；折线图数据只经 `/api/dashboard/stats/` 下发。
- 无新增依赖、无新表、无迁移。

## Risks / Trade-offs

- [7 天窗口会让周维度的波动更明显、看起来「数据更少」] → 已在 proposal 说明取舍：横轴信息密度优先，周对比可看按日柱图的 7 根柱。
- [首点 `null` 可能被误读成「00–04 没有消耗」] → tooltip 对 `null` 显示 `—`，卡片标题写明「每 4 小时」，2 号刻度起才承载窗口值；spec 里写死这条语义。
- [`stat_hour` 若存在脏数据（>23 或负数）] → 实现里 `if 0 <= bucket < 6` 兜底丢弃，不抛错。
- [双轴容易让人误读「两条线谁高谁低」] → 轴标题侧标注（左 token、右 元），且 tooltip 明确带单位；不接受「两线交叉就代表某指标超过另一指标」的读法，这是双轴的固有代价，换来的是费用曲线可辨。
- [折线卡与柱图共用 `.trends-chart-card` 的 `flex: 1` 高度] → 柱图靠 `min-height: 200px` 撑开，折线组件给 `min-height: 220px`，都不写死高度，缩小窗口不裁剪。
- [接口新增字段可能被旧前端忽略] → 纯新增字段；不删不改既有字段名。
