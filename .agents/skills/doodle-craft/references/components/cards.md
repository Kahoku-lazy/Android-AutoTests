# 卡片族规格 — 钉板卡 / 撕纸卡 / 指标卡 / 涂鸦条目卡

四种卡片各有专职，**不互相替代**（选型判据见 [../../SKILL.md](../../SKILL.md)）。**以代码为准**：`frontend/src/shared/components/**` 与 `shared/styles/workbench-theme.css`。令牌值见 [../tokens.md](../tokens.md)。

> **作用域警示**：`.ac-card` 的涂鸦皮肤**只在 `.wb-shell`（或 `.workflow-workbench`）内生效**。页面根忘带主题作用域 → 卡片变实线大圆角 + 灰阴影（EP 出厂皮肤）。

> **线型规则（2026-11-04 起，强制；2026-11-09 修订）**：虚线是**组件皮肤**，不是页面装饰。目前**只有 `AgentRouteCard`（`.route-card` 助手角色卡）**可以声明 `dashed`；`KpiCard` 已于 2026-11-09 按需求改为实线（描边 = 硬阴影色 `--kpi-accent`），并移出白名单。把白名单组件的虚线样式抄到别的组件里**不算白名单**，一律实线。判定口径见 [../../SKILL.md](../../SKILL.md) §线型规则。下表列的是**当前代码**，其中 AppCard / SketchCard / TaskBoard 任务卡的 `dashed` 属待迁移存量，改到即改实线，不要照抄。

## 1. AppCard 钉板卡（可复用数据块）

用 `el-card` 外壳，皮肤在 `workbench-theme.css`（**只在 `.wb-shell` 内生效**）：

```
边框 2.5px dashed var(--ink)   背景 var(--app-bg-card)   圆角 2px
阴影 4px 4px 0 0 var(--ac-accent)（硬偏移，0 模糊）
内边距 var(--app-space-md)      hover/focus-within：回正 + translate(-1px,-1px) + 影 5px
```

- **微倾** `--ac-tilt`（默认 `0.3deg`，无钳制）；父级常用 `sketchTiltAt(i)` 注入 `±0.4°~1.5°`
- **图钉** `.ac-card__pin`：14×14、居中置顶、2px 墨框、底 = accent、`pointer-events: none`、`aria-hidden`；`pin=false` 关闭
- **props**：`type`（`default` / `dashed`，当前视觉无差异）/ `tone`（`--c-*` 或色值）/ `tilt` / `pin`；无 `tone` 回落 `--c-dashboard`
- **用途**：图表卡 / 表格卡 / 指标组。**不替代** SketchCard（入口）、KpiCard（指标）

**裸 `el-card`（EP 覆盖，非 `.ac-card`）**：底白、圆角 `--app-radius-md`、框 `2.5px solid var(--ink)`、影 `--app-shadow-md`；hover（仅 `.wb-shell` 内、非 `.ac-card`）抬起 `translateY(-3px)` + `--app-shadow-lg`。**禁止**用裸 `el-card` 当数据块外壳。

## 2. SketchCard 撕纸入口卡

原生 `<article>`，自包含样式：

```
边框 2.5px dashed var(--ink)   背景 #fff   圆角 2px
阴影 4px 4px 0 0 var(--sketch-accent)   min-height 168px   padding 16px 16px 28px
微倾 默认 -1.2deg        hover + focus-visible：回正 + translate(-1px,-1px) + 影 5px
```

- **图标块** 34×34、2.5px 墨框、底 = accent；**删除键** 26×22、1.5px 虚线墨框、hover 变马克笔红底白字（`stopPropagation`，不进入）
- **排版**：标题 `--app-size-md` / 800；正文 `--app-size-sm` / 2 行截断；无描述显示「暂无描述」；右下 meta `--app-size-xs` / 700
- **a11y**：`role="button"` + `tabindex="0"` + Enter/Space
- **主数值配色（2026-11-17 修订）**：`kpi` 与 `entry` 两个变体的数值都走 `color-mix(accent 48%, ink) → color-mix(accent 30%, ink)` 的同色相深彩渐变，CSS 回退色取终点；上一版「accent 80%→30% 混纸色」实测对比度只有 1.1~3.0:1，已作废。**数值一律不许再混纸色**——想要浅色渐变就改用色块或描边承载。
- **用途**：用例资源网格入口

## 3. KpiCard 指标卡

原生 `<div>`，自包含样式：

```
边框 2.5px solid color-mix(in srgb, var(--ink) 12%, var(--paper))（淡灰白；2026-11-09 由 dashed 改实线）   背景 #fff   圆角 var(--comp-kpi-radius)=2px
阴影 右下三层浅色硬影（同色相 42%/20%/8% 混纸白，偏移 4/8/12px，0 模糊；2026-11-09）      微倾 默认 -0.8deg（--comp-kpi-tilt）
可点时 hover：回正 + translate(-1,-1) + 影 5px
```

- **装饰** `deco`：`none`（默认）/ `pin`（12×12 图钉）/ `tape`（64×18 斜胶带）；都 `pointer-events: none`
- **variant="kpi"**：居中 + 形状 `diamond`（默认）/ `triangle` / `square` / `circle` + label（`--app-size-sm` / 700）+ value（`--app-size-2xl` / 800）
- **variant="entry"**（仪表盘入口）：图标槽 + 标题（`--app-size-sm` / 800）+ 主值（`--app-size-2xl` / 800，深彩渐变：accent 与墨色 48%→30%）+ 描述（`--app-size-xs`）+「进入」按钮；`live` 显示 8×8 红点脉冲
- **a11y**：可点时 `role="button"` + Enter/Space
- **用途**：仪表盘入口统计、报告 / AI 指标行。**禁止**另造第二套清新风统计卡

## 4. 错误内容卡（`bug-detail`）· 已登记的渐变卡

不是共享组件，是 BUG 单详情抽屉里「错误内容」正文块（`.bug-detail__body`）的皮肤，落点 `modules/bug-manager/components/BugDetailDrawer.style.css`。

| 维度 | 规格 |
|------|------|
| 框 | `1.5px solid var(--app-border-strong)`（墨 24%） |
| 圆角 | `var(--app-radius-md)`（`6px 10px`） |
| 影 | `4px 4px 0 0 var(--ink)`，模糊半径 0 |
| 底 | `--comp-bug-error-fill`：`linear-gradient(135deg, color-mix(--color-red-69 18%, transparent), color-mix(--color-red-69 6%, transparent))` |
| 正文 | 等宽字体、`14px`、`--app-line-height-relaxed`；卡内滚动 `max-height: 46vh` |

> **2026-11-17 需求方指定**：这是**已批准的渐变偏离**，范围只限这一处（错误语义的唯一红色卡片）。浓度刻意压到 18% → 6%：45% 会把 14px 等宽正文压成"红底黑字"的告警条。其它卡片仍为平涂，**不得**照抄成通用"红色卡片"。

