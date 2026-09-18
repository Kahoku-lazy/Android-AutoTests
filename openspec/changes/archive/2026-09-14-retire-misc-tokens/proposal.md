## Why

P3 死令牌清理的**批次③（收尾批）：25 个杂项令牌**，在 `frontend/src` + `frontend/tests` + `frontend/index.html` 中精确 `var(<name>)` 消费为 0。逐名做「带边界的全仓出现次数」扫描后，**每个名字在全仓只出现 1 次 —— 就是它自己的定义行**，不存在消费点，也不存在被其它令牌引用的别名链。

| 段 | 令牌 |
|----|------|
| 中性色 · 背景/表面 | `--app-bg` · `--app-bg-warm` |
| 中性色 · 边框/高亮/激活 | `--app-icon-border` |
| 阴影/遮罩/光晕 | `--app-shadow-ink` · `--app-glow-sky` · `--app-glow-ocean` · `--app-glow-forest` |
| 辅助/图标/杂项色 | `--app-icon-teal-bg` · `--app-icon-orange-bg` · `--app-disconnect-text` · `--app-footer-yellow` |
| 字体与字号（@deprecated aliases） | `--app-font-size-sm` · `--app-font-size-base` · `--app-font-size-lg` · `--font-display` |
| 阴影/Motion/Layout 维度 | `--app-icon-shadow` · `--app-text-shadow-light` · `--app-card-hover-elevation` · `--app-card-hover-lift` |
| 独立区 · Crayon Doodle | `--doodle-card` · `--doodle-border` · `--doodle-radius-sm` · `--doodle-texture-cross` · `--doodle-texture-dots` · `--doodle-texture-stripe` |

其中 `--app-font-size-*` 四行（含 `--font-display`）整块是 `@deprecated legacy aliases`；`--app-glow-*` 三行整块是「登录页装饰光晕」。两组清空后**各自留下一条孤立注释**，属本变更必须一并处理的残留。

## What Changes

- `frontend/src/shared/styles/tokens.css`：删 25 行令牌定义（397 → 329 → 304 行量级）
- 同文件注释同步（均为删除的直接后果，非顺手改动）：
  1. 删孤儿注释 `/* 登录页装饰光晕（仅氛围，非交互色） */`（其下 3 个 glow 令牌全删）
  2. 删孤儿注释 `/* @deprecated legacy aliases — 统一用 --app-size-*（…）*/`（其下 4 个令牌全删）
  3. 修 section 标题 `/* ── 阴影/遮罩/光晕（rgba 色值）── */` → `/* ── 阴影/遮罩（rgba 色值）── */`（该段只剩 `--app-overlay`，已无光晕令牌）
- 同步 `.agents/skills/doodle-craft/references/tokens.md` §1.7「阴影层级」：删 `icon` 行（其 CSS 变量列为 `--app-icon-shadow`）
- **确认不改**：`.agents/skills/prototype-design/references/hifi-guide.md`（`--font-display` 是该技能自带 `:root`，值为 `'DM Sans'`）与 `frontend/public/exec-arch.html`（自带 `:root`，值为 `'Nunito'`）的同名令牌——与本仓 `tokens.css` 无关
- **BREAKING**：无。25 个令牌 0 消费 → 无视觉 / 行为变化
- 按 schema 约定设 `skip_specs: true`

## 关联文档

- 令牌唯一真相源：`frontend/src/shared/styles/tokens.css`
- 文档同步点：`.agents/skills/doodle-craft/references/tokens.md` §1.7（唯一提及本批死令牌处）
- `dev_docs` 与 `openspec/specs`：本批 25 名 0 提及（已逐名带边界扫描）
- 前置变更：`2026-09-14-retire-deprecated-tokens`（批次①）· `2026-09-14-retire-module-scoped-tokens`（批次②）

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

（无 —— 不改 Requirement 文本，故无 delta）

## Impact

- 前端：`frontend/src/shared/styles/tokens.css`（约 −27 行：25 令牌 + 2 注释，1 行标题改写）
- 技能文档：`.agents/skills/doodle-craft/references/tokens.md`（−1 行）
- 验证：`npm run typecheck` + `npx vite build --mode development` + `vue-frontend-check`（calibration §7 强制扫描）+ 「25 名全仓仅剩定义行→删除后 0 出现」静态复核
- 不影响：任何页面实际渲染（删除项从未被消费）
