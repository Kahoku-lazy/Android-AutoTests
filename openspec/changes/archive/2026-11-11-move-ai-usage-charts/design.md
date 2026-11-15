## Context

动机见 `proposal.md` - Why。当前实现约束：

- `index.vue` 的 `ch-ai` 章节只有一层 `.ch-ai__body`：`minmax(0,460px) minmax(0,860px)` 两列网格，左账单卡、右智能体卡，`--solo` 时退成单列。
- `ch-trend` 章节按顺序含：`.dashboard__trends`（助手任务卡 1.4fr / 任务执行结果 1fr）→ `.dashboard__trends--ai`（每日 Token / 每日费用，1fr 1fr）→ `.dashboard__trends--single`（今日逐小时折线，整行）→ `.dashboard__trends--single`（Voice 来源，整行）→ `.subhead` 最近动态 → `ActivityTimeline`。
- 图表组件 `TrendBarChart` / `SeriesBarChart` / `TodayUsageChart` 与 `voiceUsageSeries`、`tokenSeries`、`costSeries`、`todayUsageSeries` 全部在 `index.vue` 顶部声明，位置移动不涉及任何取数改动。
- `.dashboard__trends` 网格修饰类：`--ai` = `1fr 1fr`，`--single` = `1fr`；960px 以下全部退成单列。
- `.dashboard-workbench .doc-body > section:last-child` 的 `flex: 1` 与 `:deep(.activity-timeline) { flex: 1 }` 仍作用于「趋势与动态」，用于让活动卡撑到页脚。

## Goals / Non-Goals

**Goals:**

- 四张 AI 用量图表移入「AI 用量」章节，位置在用量卡片组之后。
- 两章节都用既有 `.dashboard__trends` 网格族，不新增图表布局类。
- 「趋势与动态」只保留任务执行类内容与最近动态。

**Non-Goals:**

- 不改章节顺序、章节名称、章节外壳与色标。
- 不改任何图表的组件、系列、纵轴、图例、刷新与取数逻辑。
- 不改「趋势与动态」的活动卡撑底规则。

## Decisions

**1. 复用 `.dashboard__trends` / `--ai` / `--single`，不新建图表网格类。**

同一套「两列 / 整行 / 960px 单列」语义在两个章节都成立；新类只会复制三行 CSS 并让断点规则分叉。

**2. 用 `.ai-usage-trends` 容器包住子标题与三行图，容器只负责 `margin-top: var(--app-space-lg)`。**

子标题自带 4px 上距，若把间距挂在第一行图上会与 `.subhead` 的 margin 叠加成两处间距来源；收敛到容器更可控。

**3. 加「用量趋势 / Usage」子标题。**

「AI 用量」章节因此呈现"快照 → 趋势"两层，和「平台概览」里"运行指标 → 测试用例"的分层手法一致。不加子标题时四张图直接接卡片，分组边界不清。

**4. 顺序沿用搬移前的相对顺序：按日两张 → 今日折线 → Voice。**

保留原有阅读节奏，避免搬移同时改顺序造成两处变化叠加、难以定位问题。

**5. 至少一行图表保留 `.dashboard__trends` 的 `margin-bottom`，章节板下内距不变。**

`.dashboard__trends` 自带 `margin-bottom: var(--app-space-md)`，最后一行的下边距与章节板 `--app-space-lg` 内距叠加，与原来在趋势章节里的表现一致。

## 模块防火墙自检

- 跨 App import：无。只动 `frontend/` 的 Vue 模板与页面级 CSS。
- 禁止跨 App import service/runner/consumer/state_machine：无后端改动。
- 所有 INSERT/UPDATE/DELETE 收敛到各 App 的 `api.py`：不涉及写操作。
- 前端不直连数据库；仪表盘不做写操作：图表数据仍来自既有只读 stats 接口，未新增请求。
- 未引入新的跨模块依赖。

## Risks / Trade-offs

- [「趋势与动态」删掉四张图后内容变少，`ActivityTimeline` 被 `flex: 1` 拉高显得空] → 这是既有「活动卡撑到页脚、页尾不露白」的设计意图，本次保留；若观感不佳，需要另立变更调整该章节的撑底策略。
- [「AI 用量」章节变长，首屏看不到趋势图] → 图表排在快照之后，符合"先看数、再看曲线"的顺序；章节顺序与页头不动。
- [跨章节共用横轴标签可能被改坏] → 三张按日图仍由同一份 `aiTokenChart.labels` 派生，搬移不碰取数代码。

## Open Questions

无。
