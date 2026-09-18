## Why

两处文档挂账：`frontend/DESIGN_SYSTEM.md` **不存在**，但 `doodle-craft` skill 内有 6 处指针、`vue-frontend-check` checklist 有 1 处对照（该文件早已并入 checklist，指针属残留）；`tokens.css` 出现两个「皮肤维度六」（动效 Motion 与布局 Layout），段号重复导致引用歧义。

## What Changes

- `doodle-craft`：`SKILL.md` 4 处 + `references/components.md` / `references/layout.md` / `references/tokens.md` 各 1 处，指针改指真实来源（`vue-frontend-check/references/checklist.md` 组件规格验收 / 本 skill 的 `references/*` / `tokens.css`）
- `vue-frontend-check/references/checklist.md`：模块色对照由 `DESIGN_SYSTEM §1.2/1.3` 改为「本文件组件规格验收」
- `tokens.css`：重复的第二处「皮肤维度六 · 布局 Layout」改为「皮肤维度八 · 布局 Layout（分栏 / 比例 / 断点）」，文件头维度清单同步补上该段
- 纯文档/注释修订：不改令牌名、值、选择器与任何代码行为

## 关联文档

- 架构方案：`dev_docs/05-开发与测试/设计方案与报告/设计方案-前端设计令牌分层与数据链.md`
- 无 PRD/ARCH 编号（文档指针与注释编号修订，无行为变化）

## Capabilities

### New Capabilities

- （无）

### Modified Capabilities

- （无）本变更不改变规格级行为，故 `.openspec.yaml` 设 `skip_specs: true`

## Impact

- `.agents/skills/doodle-craft/{SKILL.md,references/components.md,references/layout.md,references/tokens.md}`
- `.agents/skills/vue-frontend-check/references/checklist.md`
- `frontend/src/shared/styles/tokens.css`（仅注释）
- 归档变更（`openspec/changes/archive/**`）与 in-flight 变更中的历史提及保持原样，不追改