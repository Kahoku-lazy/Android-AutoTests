## Why

`openspec/specs/frontend-l4-data-surface/spec.md:76` 的 MUST 把 `DoodleNote` 与 `AppCard` / `KpiCard` / `SketchCard` 并列为「可复用数据块 MUST 使用的 shared 卡片零件」。

但 `shared/components/DoodleNote.vue`（178 行）在当前代码里**没有任何消费方**：`src` 内零 import、模板零标签、字符串零引用，只有 `tests/shared/p0/DoodleNote.spec.ts` 在测它。也就是说，这条 MUST 列举的四个零件里，有一个已经没有任何页面在用——规格在为一个不存在的用法背书。

上一单（`prune-frontend-dead-code`）曾把它按「零引用」列入删除清单，核实后因这条 MUST 而回滚。现在需求方裁决：**从 MUST 的枚举里移除 `DoodleNote` 并删除该组件**，让规格与代码同时收口，而不是留一个谁也不用的「备件」继续占用检索面。

## What Changes

- **修改 `frontend-l4-data-surface` 的「Cards and grids reuse shared parts」需求**：卡片零件枚举由 `AppCard` / `KpiCard` / `SketchCard` / `DoodleNote` 收为**前三者**；两个场景（指标行复用 KPI 卡、模块自建网格）逐字保留。
- **删除 `frontend/src/shared/components/DoodleNote.vue`**（178 行）与 `frontend/tests/shared/p0/DoodleNote.spec.ts`。
- **同步 `.agents/skills/doodle-craft/`** 中把 `DoodleNote` 当作现役组件描述的位置（SKILL.md 卡片清单、`components/cards.md` §4、`components/decorative.md` 胶带行、`components/known-gaps.md` 现役零件行、`tokens.md` 降级清单、`assistant-marker-card.md`、`standalone-html.md`），改为「已退役（2026-11-24）」或删除该行，避免技能继续指着一个不存在的组件。
- **不动**：`AppCard` / `SketchCard` / `KpiCard` 三个零件及其视觉口径；`DoodleBtn`（按钮零件，与 `DoodleNote` 无关，仍在用）。

> **BREAKING**：无运行时行为变化（该组件零引用，删除不影响任何页面渲染）。规格层面是收窄一条 MUST 的枚举。

## 关联文档

无 PRD 编号：本单是**规格收窄 + 死组件清退**。
依据：2026-11-24 前端复杂度体检 + 需求方裁决「从 MUST 枚举移除并删组件」。
关联记录：`dev_docs/DEV_TEST/DEV-前端死代码清理与时间收口-2026-11-24.md` 第六节待裁决项 3。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `frontend-l4-data-surface`: 「Cards and grids reuse shared parts」的零部件枚举去掉 `DoodleNote`（行为不变，仅收窄可用零件集合）。

## Impact

- **规格**：`openspec/specs/frontend-l4-data-surface/spec.md` 一条 Requirement 经 delta 更新。
- **删除**：`frontend/src/shared/components/DoodleNote.vue`（178 行）、`frontend/tests/shared/p0/DoodleNote.spec.ts`（约 40 行）。
- **文档**：`.agents/skills/doodle-craft/` 下 7 处提及需同步（见 tasks 第 3 组）。
- **不动**：`AppCard` / `KpiCard` / `SketchCard` / `DoodleBtn`、任何页面、接口、后端与引擎。
- **门禁**：`npm run typecheck` + `npm run build` + `npm run lint:styles` + `npm run test`。
