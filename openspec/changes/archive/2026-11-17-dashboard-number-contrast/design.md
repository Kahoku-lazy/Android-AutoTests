# 设计：深彩渐变

## Context

- `KpiCard.vue` 两处数值（`.kpi-card--kpi .kpi-card__value` 与 `.kpi-card--entry .kpi-card__stat strong`）用 `linear-gradient(90deg, accent 80% + paper, accent 30% + paper)` 做 `background-clip: text`。
- `DashboardView.style.css` 的 `.part-card__hero-value` 与 `.part-card__cell b` 用三段式（55% 混墨 → 满色 → 20% 混纸）。
- 纸面 `--paper`（#f3efe2）与卡白（#f7f3e8）都很亮，把 accent 往纸上混就等于往白里混：绿 #6bcb77 混成 #86d28c→#cae4c2，对比度 1.63→1.23:1。

## Goals / Non-Goals

**Goals**：主数值在纸面 / 卡白上对比度 ≥ 4.5:1（大字号门槛 3:1，留足余量）；同色相仍然可辨（绿/紫/桃/青各是各的）；渐变可见但不抢眼。

**Non-Goals**：不改卡片几何（描边、硬影、图钉、微倾）、不改图标底色、不改标题与描述配色、不动排版与数据。

## Decisions

### D1 两端都向墨色混，而不是向纸色混

```
linear-gradient(90deg,
  color-mix(in srgb, var(--kpi-accent) 48%, var(--ink)) 0%,
  color-mix(in srgb, var(--kpi-accent) 30%, var(--ink)) 100%)
```

墨色 `--ink`（#1e1e24）是这套纸面上最暗的锚点。accent 向它混合既降低明度（拿对比度），又保留色相（拿多彩）——比"再挑一个深色"更不容易跑出配色系统。

实测（白卡 #f7f3e8，WCAG 相对亮度）：

| accent | 渐变两端 | 终点对比度 |
| --- | --- | --- |
| `--c-device` 绿 | #43714c → #35523d | 7.8:1 |
| `--c-ai` 紫 | #7f4a8a → #5b3964 | 8.6:1 |
| `--c-runner` 桃 | #8a6663 → #624b4b | 7.2:1 |
| `--c-element` 靛紫 | #60528b → #473f64 | 8.8:1 |
| `--c-case` 青 | #357271 → #2c5254 | 7.8:1 |
| `--c-report` 灰紫 | #4b4552 → #3a3640 | 10.6:1 |

对照旧口径：1.14~3.02:1。

### D2 48% → 30% 这个区间

- 两端都 ≥ 48%，色相不会糊成同一种深灰；两端差 18%，肉眼可见轻微渐变，但不至于让数字一半深一半浅。
- 起点再亮（>55%）对比度掉到 4.4 以下（黄系先失守）；终点再亮（>35%）「轻」得读不动。

### D3 回退色取终点

`color: color-mix(accent 30%, ink)`：浏览器不支持 `background-clip: text` 时数字仍是终点色（≥4.5:1），不会退回黑色或透明。

### D4 账单卡与统计卡同一条配方

`.part-card__hero-value` / `.part-card__cell b` 改成同一对 `color-mix`，只把 `--kpi-accent` 换成 `--part-accent`。一个仓库里"数值"只有一套颜色配方，不再出现三段式。

## Risks / Trade-offs

- [数值变深，卡片整体观感更"重"]：卡片其余部分（描边/硬影/图标）已经是彩色的，数值变深反而让层次从"彩色纸片"回到"有字的卡片"。
- [共享件改动波及 BUG / 报告 / 任务清单]：已与需求方确认按共享件统一改；三页原本同样读不动。
- [色相在高浓度混墨后略微偏灰]：实测同一排卡片仍能一眼分出绿 / 紫 / 桃 / 靛紫。

## Migration Plan

纯样式。回退 = 两处渐变与两处回退色还原为 80%→30% 纸色混法，并回滚 spec 与 cards.md。

## Open Questions

无（方案 A 与「共享件统一改」已由需求方在候选图中选定）。
