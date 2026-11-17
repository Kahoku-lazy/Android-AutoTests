## Context

- 审计数据见 <code>dev_docs/DEV_TEST/设计-字体与颜色体系审计与方案-20261104.html</code>：374 处 font-size（8 字面量）、字重 5 档、行高 17 种、98 原子（16 死）、123 处硬编码色值。
- 现状语义层：<code>--app-text-secondary</code> = <code>--color-ink-57</code>（3.12:1），<code>--app-border-light</code> = 白，<code>--app-border-lighter</code> = 纸白。
- 门禁：<code>check-style-gates.mjs</code> 管调色板白名单（上限 = 白名单长度）与「非原子声明不得持纯色字面量」。

## Goals / Non-Goals

**Goals:**

- 补齐排版令牌（字重 / 行高），组件不再写数字。
- 修语义层：三级文字 + 两级边框 + 表面色，次要文字达到 AA。
- 颜色原子只减不增（除本次新增 <code>--color-ink-42</code>），死令牌清零。

**Non-Goals:**

- 不改字号刻度主体（12–48 保留），只补 96px display 档。
- 不做暗色主题、不改图表配色策略、不动模块色 <code>--c-*</code>。
- 不追求一次清完 123 处硬编码色值（图表侧留待单独变更）。

## Decisions

### 1. 字重取 5 档而不是 3 档

现状 400/500/600/700/800 都在用（600 有 50 次），砍到 3 档会改变大量标题观感。令牌化保留 5 档，只禁字面量。

### 2. 行高取 4 档，按「最接近」映射

1.25 / 1.4 / 1.6 / 1.75。现状 1.2→tight（略松）、1.35/1.4→snug、1.5/1.6→normal、1.7→relaxed；<code>line-height: 1</code> 与 px 值保留（图标与固定高场景）。

### 3. 新增 <code>--color-ink-42</code> 承载 AA 次要文字

<code>#6b6b74</code> 与现有原子不同值，必须按调色板规则登记；同步把名字加入门禁白名单，上限随之上调 1。

### 4. 边框语义两级：subtle / strong

<code>--app-border-subtle</code> = ink 10% 混合（1px 卡片/分隔线），<code>--app-border-strong</code> = ink 24%（悬停/聚焦）。旧 <code>--app-border-light/-lighter</code> 保留（仍被部分组件当“白边”用），迁移到 P1 再判。

## 模块防火墙自检

- 只改前端样式层与一个前端门禁脚本；无跨模块 import、无后端改动、无写库。

## Risks / Trade-offs

- [次要文字变深，界面变重] → 只改一个令牌值，全站一致；先看仪表盘与任务详情两页。
- [行高映射带来细微版式位移] → 取众数档（1.4 / 1.6）为新默认，逐条替换后可回退。
- [批量替换误伤非文本用途的 <code>--ink</code>] → 只替换 <code>color:</code> 声明与 <code>border/outline</code> 声明，不动 <code>background</code> / <code>box-shadow</code>。
- [新增原子被门禁判超上限] → 同步更新 <code>PALETTE</code>，上限随白名单长度自动 +1。
