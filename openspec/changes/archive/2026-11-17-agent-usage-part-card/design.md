## Context

- Agent 卡由 `AppCard`（`.ac-card`）渲染，默认带图钉、硬阴影与 `--ac-tilt` 微倾；内容为 `.agent-usage-card__name` + `.agent-usage-card__stats` 两列。
- 参考图「CARDS AS PARTS」：细墨线、无阴影、顶边色条、右上角四分之一圆、编号 + 粗标题 + 说明。

## Goals / Non-Goals

**Goals：**

- 让 Agent 费用卡读成「编号零件卡」，与左侧已改实线的统计卡同一套平铺语言。

**Non-Goals：**

- 不改 `AppCard` 共享皮肤（其它页面仍用钉板卡）；不改数据字段与布局位置。

## Decisions

### 1. 用模块内 scoped 覆盖，而不是新组件

卡片仍是 `AppCard`，只在 `dashboard` 模块内用 `.agent-usage-card` 覆盖 `border / background / box-shadow / transform`，并加 `::before`（色条）与 `::after`（黄圆）。好处：不复制第二套卡片外壳，`AppCard` 的点击/无障碍能力保留。

### 2. 色条按序号轮转模块色

用 `--agent-accent` 内联变量注入（`--c-ai`、`--c-case`、`--c-runner`、`--c-workflow` 循环），与全站「模块色只做描边/装饰」的规则一致；右上角圆固定 `--c-dashboard` 黄，作为统一的“零件标记”。

### 3. 关闭默认装饰

传 `:pin="false"`，并在 CSS 里 `transform: none !important; box-shadow: none !important`，避免钉板卡的图钉/微倾/硬影与色条打架。

## 模块防火墙自检

- 只改 `frontend/src/modules/dashboard/index.vue`；未动 `shared/`。

## Risks / Trade-offs

- [卡片失去硬阴影后与页面其它卡片的层级语言不同] → 它位于 AI 用量区块内、与同区块统计卡一致；区块级层次仍由钉板容器提供。
- [右上角黄圆在小屏可能压住标题] → 圆 52px，标题区左侧内距 16px、标题字号 18px，实测两列 420px 宽下无重叠；&lt; 360px 时标题会缩短显示名。
