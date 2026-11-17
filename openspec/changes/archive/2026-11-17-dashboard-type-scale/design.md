## Context

仪表盘的字号散在 5 个文件里：共享件 `KpiCard.vue`（卡片标题 / 描述 / 数值）、`DashboardView.style.css`（章节标题、区块标题、字段、页脚）、`StatsCard.vue`（小字）、`ActivityTimeline.vue`（时间 / 标签）、`TaskResultPanel.vue`（结果字段）。

当前口径（改前）：

- 章节标题 `.chapter-title` = `--app-size-lg`（20px），区块标题 `.subhead` / `.trends-tasks-card__title` = 14px，卡片标题 `.kpi-card__title` = 14px，其余一律 `--app-size-xs`（12px）。
- 数值 `.kpi-card__value` 的渐变是「55% accent + 45% 墨 → 100% accent → 20% accent + 纸」，跨 4 个明度区，数字一长就左深右浅到像两种颜色。

规格侧：`frontend-doodle-kpi-card` 的「Entry card primary value matches accent shadow」写的是「可用 accent / 紧凑变体 MUST 墨色」，实现早已偏离（两个变体都用了渐变），这次再收窄区间就彻底对不上，按 REMOVED + ADDED 处理。

## Goals / Non-Goals

**Goals:**

- 数值渐变收敛到 accent 80%→30%，两端同色相、跨度只两档。
- 卡片标题 16、其余文本 14、大标题与数值不变。
- 全部改动只用字号令牌（12/14/16/20/28 均在刻度内）。

**Non-Goals:**

- 不改 ECharts 内部字体（`SeriesBarChart` / `TrendBarChart` 的 `fontSize: 12`）。
- 不改布局、栅格、卡片尺寸与硬阴影层数。
- 不改 KPI 卡以外模块的字号。
- 不改数值本身的字号（28px）。

## Decisions

**1. 渐变区间取 `color-mix(accent 80%, paper)` → `color-mix(accent 30%, paper)`。**
两端都混纸色，保证是同一色相的两个浓度，既不混墨（会串色相）、也不出现满色端（会过饱和）。这也与需求方此前对其它图形定的「浓度区间」口径一致（序号 45%→30%）。
备选：仍用 100% accent 做中点（更像高光）——否决：数字够大，高光端会让一半字形过饱和。

**2. 字号改令牌而不是写 px。**
三档直接映射到既有刻度：14=`--app-size-sm`、16=`--app-size-md`、20=`--app-size-lg`、28=`--app-size-2xl`。门禁批 1 只认刻度，写 px 会被拦。

**3. 字号口径写进 `frontend-doodle-kpi-card` 而不是新开能力。**
这条口径横跨 KPI 卡与仪表盘区块，两者共用同一批令牌；为一张字号表单开一个能力，收益低于维护成本。若以后别的模块也要这套口径，再上提为独立能力。

**4. 图表字体不动。**
ECharts 的轴标签 14px 会把横轴挤到换行，且它是 canvas 内绘制，改字号要同时调边距与布局，属另一件事。

## 模块防火墙自检

- 只改 `shared/components/KpiCard.vue` 与 `modules/dashboard/**` 的样式声明，不新增跨模块依赖。
- 不涉及后端、接口、数据库。

## Risks / Trade-offs

- [12→14 后，窄卡片里的小字可能换行或顶到边] → 改动点都是短标签（时间、字段名、Tag），且卡片有 `min-width`；已跑 `tests/dashboard` 120 项与 `vue-tsc`，若真实页面出现换行，按具体选择器回调到 12。
- [数值只有一个字符（如 `0`）时渐变看不出来] → 这是渐变的固有性质，不是缺陷；数字变长时才体现左深右浅。若需求方想要卡片本身（图标块 / 边框）做同区间渐变，属另一处改动。
- [`kpi` 变体改色后与旧规格冲突] → 用 REMOVED + ADDED 显式迁移，归档时旧要求会被删除，不留矛盾条款。
