## 1. 删除组件与用例

- [ ] 1.1 删除 `frontend/src/shared/components/DoodleNote.vue`（178 行）。验证：`DoodleNote` 在 `frontend/src` 内命中 0。
- [ ] 1.2 删除 `frontend/tests/shared/p0/DoodleNote.spec.ts`。验证：`npm run test` 全绿，无 `Cannot find module`。
- [ ] 1.3 确认 `DoodleBtn` 等其它 `Doodle*` 零件未受影响。验证：`DoodleBtn` 在 `frontend/src` 命中数 > 0（当前 7 处）。

## 2. 规格

- [ ] 2.1 delta spec `specs/frontend-l4-data-surface/spec.md` 已把枚举收为 `AppCard` / `KpiCard` / `SketchCard`，两个场景名与正文逐字保留。验证：`openspec validate retire-doodlenote-part --strict` 通过；`git diff` 中该 spec 的两个 Scenario 段落无改动。
- [ ] 2.2 本单 `.openspec.yaml` **不设** `skip_specs`。验证：`openspec status --change retire-doodlenote-part --json` 显示 specs 为 done。

## 3. 同步 doodle-craft（7 处）

- [ ] 3.1 `.agents/skills/doodle-craft/SKILL.md`：删掉「助手角色卡」行里「DoodleNote 皮」的表述（改为描述 `.route-card` 自身）、卡片清单里的 `DoodleNote`、以及「列表条目 / 线路卡 | `DoodleNote`」整行。验证：该文件 `DoodleNote` 命中 0。
- [ ] 3.2 `.agents/skills/doodle-craft/references/components/cards.md`：删除 §4「DoodleNote 涂鸦内容卡 / 便利贴」整节，**重排后续小节编号并修正交叉引用**；同时删掉 §7 开头「AppCard / SketchCard / DoodleNote 基类 / TaskBoard 任务卡的 `dashed` 属待迁移存量」里的 `DoodleNote` 基类一项。验证：该文件 `DoodleNote` 命中 0；小节编号连续。
- [ ] 3.3 `.agents/skills/doodle-craft/references/components/decorative.md`：删掉「胶带 `DoodleNote`」这一行。验证：该文件 `DoodleNote` 命中 0。
- [ ] 3.4 `.agents/skills/doodle-craft/references/components/known-gaps.md`：把「现役是 `AppCard` / `SketchCard` / `KpiCard` / `DoodleNote`」改为不含 `DoodleNote` 的三件。验证：该文件 `DoodleNote` 命中 0。
- [ ] 3.5 `.agents/skills/doodle-craft/references/tokens.md`：reduced-motion 降级清单去掉 `DoodleNote`。验证：该文件 `DoodleNote` 命中 0。
- [ ] 3.6 `.agents/skills/doodle-craft/references/components/assistant-marker-card.md` 与 `references/standalone-html.md`：两处提到 `DoodleNote` 的对比/枚举句去掉该名称，语义保持不变。验证：两文件 `DoodleNote` 命中均为 0。

## 4. 门禁与关单

- [ ] 4.1 `npm run typecheck`、`npm run build`、`npm run lint:styles`、`npm run test` 四条 exit 0。验证：记录退出码。
- [ ] 4.2 全仓文档复扫：`DoodleNote` 仅在 `openspec/changes/**`、`openspec/specs/frontend-l4-data-surface`（经 delta 归档后）与历史审计 `dev_docs/DEV_TEST/REVIEW-*` 中残留。验证：复扫输出贴进关单。
- [ ] 4.3 关单汇报写明：删除的用例其被测组件已删、`DoodleBtn` 与其它卡零件未动、技能 7 处已同步。随后归档。
