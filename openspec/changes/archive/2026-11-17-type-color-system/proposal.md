## Why

字体与颜色各自只到「原子 / 零散硬写」两层：字重 5 种取值、行高 17 种取值全无令牌；次要文字对比度 3.12:1、弱化文字 1.64:1 不达 WCAG AA；语义边框令牌 <code>--app-border-light</code> 指向白色，在白卡上不可见；98 个颜色原子里 16 个从未被引用。审计见 <code>dev_docs/DEV_TEST/设计-字体与颜色体系审计与方案-20261104.html</code>。

## What Changes

- **P0 令牌层**：新增 <code>--font-weight-*</code>（400/500/600/700/800）、<code>--line-height-*</code>（1.25/1.4/1.6/1.75）、<code>--app-text-primary/tertiary/disabled</code>、<code>--app-bg-canvas/muted</code>、<code>--app-border-subtle/strong</code>；<code>--app-text-secondary</code> 由 <code>#96918c</code> 改为 <code>#6b6b74</code>（5.21:1）并新增原子 <code>--color-ink-42</code>。
- **P1 组件层**：字重 / 行高字面量换成令牌；<code>color: var(--ink)</code> 换成 <code>--app-text-primary</code>；边界线与分隔线换成 <code>--app-border-subtle</code>。
- **P2 收敛**：删除 16 个从未引用的颜色原子；字号字面量收进刻度（新增 <code>--app-size-4xl</code> 供 404 巨字），EmptyState 图标回到 3xl。

## 关联文档

- 审计与方案：<code>dev_docs/DEV_TEST/设计-字体与颜色体系审计与方案-20261104.html</code>
- 规则来源：<code>.agents/skills/doodle-craft/SKILL.md</code> §设计令牌

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

（无 —— 纯视觉令牌与样式调整，<code>skip_specs: true</code>）

## Impact

- 前端：<code>shared/styles/tokens.css</code>、<code>shared/components/**</code>、<code>modules/**</code> 的样式与少量模板样式。
- 门禁：<code>frontend/tests/check-style-gates.mjs</code> 的调色板白名单加 <code>--color-ink-42</code>。
- 后端 / 接口 / 交互逻辑：无改动。
