## Why

P3 复查得出**死令牌 122 个**（已排除 `--el-*`，那批由 Element Plus 全量样式内部消费）。本变更处理**第一批：两族显式标注 `@deprecated` 的令牌**——

1. `--app-module-*`（8 个）：段注释即「旧命名，值同 `--c-*`；新代码用 `--c-*`」；
2. `@deprecated 旧色` 段中被后取代的 23 个（含 `--app-paper-dot` —— 它因 ② 删除 6 处模块点阵而**新近成为孤儿**）。

这 31 个令牌在 `frontend/src` + `frontend/tests` 中**0 个 `var()` 消费点**，且代码里不存在 `getPropertyValue('--x')` 这类绕过读取（已核实：全仓仅 `useSidebarResize.ts` 的 `setProperty('--side-w')`，与本批无关）。

## What Changes

- 删除 `tokens.css` 的 `--app-module-*` 段（1 行注释 + 8 个令牌）
- **收缩**（非整段删除）`@deprecated 旧色` 段：删 23 个死令牌，**保留仍被消费的 6 个** —— `--app-green` · `--app-blue` · `--app-accent-blue` · `--app-accent-purple` · `--app-ink` · `--app-ink-muted`
- 同步 `.agents/skills/doodle-craft/SKILL.md:61`：删除「另有语义色 `--app-module-*` 系列与上述 8 色对应…改模块色时两处同步」这一句，让模块色唯一真相源回到 `--c-*`
- **BREAKING**：无。31 个令牌 0 消费 → 无视觉 / 行为变化
- 按 schema 约定设 `skip_specs: true`

## 关联文档

- 令牌唯一真相源：`frontend/src/shared/styles/tokens.css`
- 主题技能：`.agents/skills/doodle-craft/SKILL.md`（模块色映射表 + `--app-module-*` 说明）
- 前置变更：`openspec/changes/archive/2026-09-14-unify-l3-container`（使 `--app-paper-dot` 成为孤儿）
- 说明：`dev_docs/文档编号对照表.md` 不存在，本变更无对应编号文档；属死令牌清理（P3 第一批）

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

（无 —— 不改 Requirement 文本，故无 delta）

## Impact

- 前端：`frontend/src/shared/styles/tokens.css`（约 −35 行）
- 技能文档：`.agents/skills/doodle-craft/SKILL.md`
- 验证：`npm run typecheck` + `npx vite build --mode development` + `vue-frontend-check` + 「31 个令牌全仓 0 命中」静态复核
- 不影响：任何页面的实际渲染（删除项从未被消费）
