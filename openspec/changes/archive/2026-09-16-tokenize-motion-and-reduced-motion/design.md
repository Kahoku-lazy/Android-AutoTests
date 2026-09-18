## Context

- 令牌刻度：`--duration-fast 0.12s` / `--duration-base 0.15s` / `--duration-slow 0.25s`；`--ease: cubic-bezier(0.25,0.1,0.25,1)` —— 与 CSS 关键字 `ease` **严格同值**，故 `ease → var(--app-ease)` 是零视觉变化。
- 实测（行级扫描，避免跨行误报）：含 `transition` 且其中动画 `transform` 的文件共 **10** 个（`ToolboxPanel.style.css`、`DeviceCard.vue`、`CaseBreakdown.vue`、`ReportDetail.vue`、`TaskReport.vue`、`WorkflowFileBrowser.vue`、`AppSidebar.style.css`、`motion.css`、`style.css`、`LoginView.style.css`），改动前 **7** 个缺降级块。
- 无限装饰动画 3 处：`SkeletonCard.vue` `1.4s`、`TaskResultPanel.vue` `1.5s`、`KpiCard.vue` `1.5s` —— 均**已有**降级块。
- 动机见 `proposal.md`。

## Goals / Non-Goals

**Goals**

- 组件级动效时长/缓动全部取自令牌，与令牌同值者零视觉变化
- 含 transform 动效的文件全部提供 reduced-motion 降级
- 把「装饰性无限动画保留固有周期但必须降级」明确登记为例外

**Non-Goals**

- 不为 `1.4s` / `1.5s` 新增令牌（是否纳入刻度待定）
- 不改路由过渡与 `shared/animations.ts` 的既有实现
- 不给"仅颜色过渡"的文件增加降级块（避免噪声）
- 不调整各处的动画曲线语义（`ease-in-out` 等非 `ease` 关键字保持原样）

## Decisions

**D1 只替换与令牌严格同值或可安全对齐的值**
`0.12s` / `0.15s` / `ease` 与令牌同值 → 零视觉变化；`0.1s` / `0.2s` 不在刻度上 → 归到最近档（+0.02s / +0.05s）。`ease-in` / `ease-out` / `ease-in-out` / `linear` 不替换（令牌未登记对应曲线，替换会改变观感）。
备选：新增 `--ease-in-out` 等令牌 —— 否决，本期无跨模块复用需求，且会扩大令牌面。

**D2 降级块的判定口径取「`transition` 是否动画了 `transform`」**
理由：这是"位移/旋转/缩放"的可机械判定代理；仅颜色过渡不构成前庭负担。
备选："所有含 `transition` 的文件都加" —— 否决，会给 30+ 文件加入无意义的块。

**D3 降级用 `transition: none` 而非逐属性豁免**
理由：简化且完整；对启用减少动效的用户，颜色瞬变同样可接受。

## Risks / Trade-offs

- [`0.2s → 0.25s` 涉及 13 处，观感略慢] → 幅度 0.05s，且有刻度依据；tasks 含浏览器断言确认声明值与令牌一致
- [批量替换可能改到非动效位置（如把 `ease` 写进别处）] → 替换限定在含 `transition`/`animation` 且非注释的行，并在干跑阶段人工核对；本次实施中已发现并修正两类脚本缺陷（见 tasks）
- [降级块 `transition: none` 会让展开图标失去旋转反馈] → 图标仍会瞬间切换到新状态，信息不丢失

## Migration Plan

1. 先令牌化（可按文件分批），再补降级块，最后逐项复核
2. 回滚策略：纯样式改动，回滚即 `git revert`；无数据、接口与路由迁移

## Open Questions

（无）