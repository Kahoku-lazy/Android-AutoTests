## Context

动机见 `proposal.md - Why`。现状事实（已核对代码）：

- `frontend/src/modules/dashboard/index.vue` 的「AI 用量」KPI 区共 5 张 `StatsCard`：第一行三张（累计用量 / 当天用量 / 缓存命中率）带 `hide-desc` 且不传 `desc`；第二行两张（总费用 / 当天费用）传 `desc="DeepSeek"`。
- `StatsCard` 是共享 `KpiCard`（`variant="entry"`）的薄包装，副标题由 `KpiCard` 的 `.kpi-card__desc` 槽位渲染，样式与令牌齐备（`--app-size-xs`、`--app-text-secondary`）。
- `StatsCard` 的 `hideDesc` 开关只服务这三张卡，全仓无其它调用方；`desc` 缺省时回退「核心指标实时更新」。
- 布局 `.ai-usage-kpis` 为 3 列网格、`align-items: start`，`KpiCard--entry` 有 `min-height: 142px`。

## Goals / Non-Goals

**Goals:**

- 五张 KPI 卡副标题口径一致为「DeepSeek」，视觉完全沿用既有 `KpiCard` 副标题规格（不新增令牌、字号、颜色、间距）。
- 副标题只有 `desc` 一个入口，删除不再有调用方的 `hideDesc`，避免同一区块出现第二套「无副标题」写法。

**Non-Goals:**

- 不改数值口径、单位、精度、跳转目标、卡片顺序与布局列宽。
- 不改 `KpiCard` 共享件（副标题槽位已够用），也不给右侧智能体卡加副标题。
- 不动后端接口与数据模型。

## Decisions

1. **用既有 `desc` 属性补齐，而非新增 `subtitle` 概念**
   理由：`KpiCard` entry 变体的 `desc` 就是副标题位，第二行两张卡已经在用；新增属性等于同一视觉开两套入口，违反「一个零件只有一套皮肤」。备选（新增 `subtitle` 属性）被否。

2. **删除 `StatsCard.hideDesc`**
   理由：改动后全仓零调用方，保留会成为死开关，也会诱导后续卡片再次走「不显示副标题」的旁路；副标题缺省行为由 `desc || "核心指标实时更新"` 单点决定。备选（保留开关仅删用法）被否，代价是遗留不可达分支。

3. **单测改为覆盖 `desc` 真实行为**
   `frontend/tests/dashboard/p0/StatsCard.spec.ts` 的 `hideDesc=true` 用例替换为：显式传 `desc` 时 `.kpi-card__desc` 渲染该文案（且不再出现缺省文案）。仪表盘五张卡的一致性由实现核对 + 页面目视验证承担——该页无 index 级挂载测试，为本次小改动新建整页测试属过度投入。

4. **不新增样式**
   副标题出现的唯一视觉变化是第一行三张卡多一行 11px 文本；`min-height: 142px` 与 `align-items: start` 下仍与第二行等高对齐，不需要改 CSS。

## 模块防火墙自检

- 跨 App import：无新增，本改动只碰前端 dashboard 模块内文件与其单测。
- 禁止跨 App import service/runner/consumer/state_machine：无涉及。
- 所有 INSERT/UPDATE/DELETE 收敛到各 App 的 `api.py`：无写操作，仪表盘仍为只读。
- 前端不直连数据库：不涉及。

## Risks / Trade-offs

- [第一行卡片高度变化可能让两行间距观感变紧] → 已确认 `.ai-usage-kpis` 为 `align-items: start` 且 entry 卡有 `min-height`，两行卡片本就等高；落地后按 1686×520 视口目视一次两行间距。
- [删除 `hideDesc` 若有仓外调用方会编译失败] → 全仓 grep 仅三处调用，且 `vue-tsc --noEmit` 会兜住；编译失败即回退该删除。
- [文案「DeepSeek」硬编码在模板] → 与第二行两张卡写法一致，且它属于固定数据来源标注而非可配置项，不引入常量层。
