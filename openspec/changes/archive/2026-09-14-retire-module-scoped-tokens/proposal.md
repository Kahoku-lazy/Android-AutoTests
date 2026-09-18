## Why

P3 死令牌清理的**批次②：模块专属色三族共 68 个令牌**，在 `frontend/src` + `frontend/tests` + `frontend/index.html`（241 个文件）中**精确 `var(<name>)` 消费为 0**：

| 族 | 个数 | 残留原因 |
|----|:--:|------|
| `--ai-*`（AI Assistant） | 18 | Doodle Craft 前的「暖纸/玻璃」皮肤；模块现用 `--c-ai` + `--doodle-*` + `--ai-status-*` |
| `--case-*`（Case Manager） | 38 | 旧「淡蓝玻璃」皮肤（`rgba(162,210,255,…)` 一族）；模块现用 `--c-case` + 通用中性色 |
| `--app-stat-*`（仪表盘统计卡） | 12 | 「奶油低饱和 · 参考图配色」遗留；StatsCard 已改走 `--c-*` |

其中 **2 个是传递性死亡**：`--ai-bg-success` / `--ai-bg-error` 全仓唯一的引用就是同批要删的别名行（`tokens.css:138` `--ai-hint-green-bg: var(--ai-bg-success)`、`:140` `--ai-hint-red-bg: var(--ai-bg-error)`）——别名一删，它们就成了孤儿，故一并在本变更内删除。

判据（已实测，见 design §Decisions）：

1. 精确 `var(name)` / `var(name,` 扫描 = 0（含 `frontend/index.html`）；
2. 无动态构造 `var(--${…})`；
3. 无 `getPropertyValue` / `setProperty` 读取（全仓仅 `useSidebarResize.ts:25,30` 写 `--side-w`，不在本批）。

## What Changes

- `frontend/src/shared/styles/tokens.css`：删除 68 行令牌定义（`--ai-*` 18 · `--case-*` 38 · `--app-stat-*` 12）
- **保留 4 个在用兄弟令牌**（同族、非死）：`--case-border-subtle`(3 处) · `--case-border`(1 处) · `--ai-hint-orange`(3 处) · `--app-stat-text`(1 处，经 `views/components/AnimalFace.vue:124` 的 `--af-ink` 实际使用)
- 同步 `.agents/skills/doodle-craft/references/tokens.md` §1.11「仪表盘统计卡」表：删 11 行死令牌，保留 `--app-stat-text` 行
- **BREAKING**：无。68 个令牌 0 消费 → 无视觉 / 行为变化
- 按 schema 约定设 `skip_specs: true`（无 Requirement 文本变更）

## 关联文档

- 令牌唯一真相源：`frontend/src/shared/styles/tokens.css`
- 文档同步点（唯一提及本批死令牌处）：`.agents/skills/doodle-craft/references/tokens.md` §1.11
- 确认无需改动：`.agents/skills/prototype-design/references/hifi-guide.md` 的 `--font-display` 是该技能自带 `:root` 的同名令牌（且属批次③）；`dev_docs` 全仓 0 提及
- 前置变更：`openspec/changes/archive/2026-09-14-retire-deprecated-tokens`（批次①）

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

（无 —— 不改 Requirement 文本，故无 delta）

## Impact

- 前端：`frontend/src/shared/styles/tokens.css`（约 −70 行）
- 技能文档：`.agents/skills/doodle-craft/references/tokens.md`（约 −11 行）
- 验证：`npm run typecheck` + `npx vite build --mode development` + `vue-frontend-check`（calibration §7 强制扫描）+ 「68 名全仓 0 命中」静态复核
- 不影响：任何页面实际渲染（删除项从未被消费）
