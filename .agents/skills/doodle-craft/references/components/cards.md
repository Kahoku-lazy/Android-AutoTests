# 卡片族规格 — 钉板卡 / 撕纸卡 / 指标卡 / 涂鸦条目卡

四种卡片各有专职，**不互相替代**（选型判据见 [../../SKILL.md](../../SKILL.md)）。**以代码为准**：`frontend/src/shared/components/**` 与 `shared/styles/workbench-theme.css`。令牌值见 [../tokens.md](../tokens.md)。

> **作用域警示**：`.ac-card` 的涂鸦皮肤**只在 `.wb-shell`（或 `.workflow-workbench`）内生效**。页面根忘带主题作用域 → 卡片变实线大圆角 + 灰阴影（EP 出厂皮肤）。

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
- **用途**：图表卡 / 表格卡 / 指标组。**不替代** SketchCard（入口）、KpiCard（指标）、DoodleNote（条目）

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
- **用途**：用例 / 元素 / 页面流资源网格入口

## 3. KpiCard 指标卡

原生 `<div>`，自包含样式：

```
边框 2.5px dashed var(--ink)   背景 #fff   圆角 var(--comp-kpi-radius)=2px
阴影 4px 4px 0 0 var(--kpi-accent)      微倾 默认 -0.8deg（--comp-kpi-tilt）
可点时 hover：回正 + translate(-1,-1) + 影 5px
```

- **装饰** `deco`：`none`（默认）/ `pin`（12×12 图钉）/ `tape`（64×18 斜胶带）；都 `pointer-events: none`
- **variant="kpi"**：居中 + 形状 `diamond`（默认）/ `triangle` / `square` / `circle` + label（`--app-size-sm` / 700）+ value（`--app-size-2xl` / 800）
- **variant="entry"**（仪表盘入口）：图标槽 + 标题（`--app-size-sm` / 800）+ 主值（`--app-size-2xl` / 800，色 = accent）+ 描述（`--app-size-xs`）+「进入」按钮；`live` 显示 8×8 红点脉冲
- **a11y**：可点时 `role="button"` + Enter/Space
- **用途**：仪表盘入口统计、报告 / AI 指标行。**禁止**另造第二套清新风统计卡

## 4. DoodleNote 涂鸦内容卡 / 便利贴

共同壳：框 `2.5px dashed var(--ink)`、圆角 `2px`、影 `4px 4px 0 0 <accent>`、内边距 `--app-space-md`、hover 回正 + `translate(-1,-1)` + 影 5px。

| variant | 内容 |
|---------|------|
| `note`（胶带卡）| 底 `--paper`、微倾 `-0.8deg`、顶中胶带 64×18（`pointer-events: none`）、插槽 `header` / `default` / `actions` |
| `sticky`（Do/Dont 便利贴）| status `ok`：底 `--paper`、accent `--c-case`、微倾 `-1.2deg`；`fail`：底 `--app-error-bg`、accent `--app-marker-red`、微倾 `+1.4deg`；`run`：底白、accent `--c-workflow`；`wait`：底 `--paper`、accent `--app-offline` |

**用途**：列表条目卡（助手线路、任务条目）。**不替代** KpiCard / SketchCard / AppCard。排版未定义，由使用方给定。
