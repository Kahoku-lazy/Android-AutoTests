## Context

动机见 `proposal.md - Why`。现状事实（已核对代码）：

- [KpiCard.vue](frontend/src/shared/components/KpiCard.vue)：`entry` 变体在卡片底部渲染 `button.kpi-card__enter`，文案由 `enterLabel` 决定（默认「进入」）；`isClickable` 在未显式传 `clickable` 时按 `Boolean(enterLabel)` 推断。按钮有 3 段样式（基础 / hover / reduced-motion）。
- [StatsCard.vue](frontend/src/modules/dashboard/components/StatsCard.vue)：`showEnter` 控制是否传 `enterLabel`，`:clickable="!!path"` 已存在。
- [index.vue](frontend/src/modules/dashboard/index.vue)：6 处 `:show-enter="false"`（AI 五张 + 任务数量）；AI 五张卡仍带 `path="/ai-assistant"`。
- 全仓只有 `StatsCard` 传 `enterLabel`；其它模块（report-generator、ai-assistant）用默认 `kpi` 变体，不渲染按钮。

## Goals / Non-Goals

**Goals:**

- 卡片只有一个激活入口：整卡。删除独立「进入」按钮及其样式、属性与推断逻辑。
- AI 用量五张卡变为纯展示：无路径、不可点、无 role、无 hover。
- spec 与单测跟代码一致，避免「条款说要按钮、代码没有」的老问题。

**Non-Goals:**

- 不改任何跳转目标（设备 / 智能体 / 报告 / 任务清单 / 工作流 / 用例项目工作台）。
- 不改 `entry` 变体的视觉壳（虚线边、硬阴影、微倾、钉图钉、live 点、主数值 accent 色）。
- 不改默认 `kpi` 变体（其它模块的指标卡）与其可点行为。

## Decisions

1. **删 `enterLabel` 而不是让调用方不传**
   理由：全仓唯一调用方是 `StatsCard`，保留属性等于留下一条「把按钮装回来」的路径，而产品口径已明确「卡片不出现进入按钮」。备选（保留 `enterLabel`、仅不传）被否。

2. **`entry` 变体的默认可点性改为 false，由 `clickable` 显式决定**
   原推断 `Boolean(enterLabel)` 随属性一起删除；`StatsCard` 已经传 `:clickable="!!path"`，所以行为等价且更直白：有没有 `path` 就决定可不可点。备选（保留推断、默认 true）被否：会让所有 entry 卡都变成可点，包括纯展示卡。

3. **AI 五张卡删 `path`，而不是加 `disableClick` 开关**
   理由：这五张卡本来就不该有导航目标，删路径是从根上表达「只展示」，不引入第二个布尔开关。备选（新增 `readonly` 属性）被否：组件已经能用「有无 path」表达可点性。

4. **样式整段删除，不做 `display: none`**
   `.kpi-card__enter` 及其 hover、reduced-motion 三块一起删，避免留下「看不见但存在」的 DOM/样式债；`prefers-reduced-motion` 块里只留卡片与 live 点的降级。

## 模块防火墙自检

- 跨 App import：无。纯前端共享件与仪表盘模块改动。
- 写库/接口：不涉及；不改 API、不改数据模型。
- 前端不直连数据库：不涉及。
- 无新增依赖、无新增共享件。

## Risks / Trade-offs

- [其它模块若未来想用「进入」按钮，需要重新加属性] → 产品口径是「卡片整卡可点」，没有第二个入口的需求；真有需求时按新变更再加，不会悄悄复活。
- [删 `showEnter` 后若有遗漏的 `:show-enter` 传参，Vue 会把未知属性透传到根 DOM，成为 `show-enter="false"` 属性] → 实施时全量搜索 `show-enter`，删除 6 处；单测断言根元素无该属性。
- [AI 卡变不可点后，用户可能仍以为可点] → 去掉 `role`/`tabindex`/`cursor: pointer` 与 hover 抬升，视觉上不再给可点暗示。
- [`KpiCard` 是共享件，改它会影响 5 个模块的既有快照/用例] → 已确认只有 `StatsCard` 传 `enterLabel`；其它模块走 `kpi` 变体，按钮本来就不渲染，行为不变；跑 `KpiCard` 单测兜底。
