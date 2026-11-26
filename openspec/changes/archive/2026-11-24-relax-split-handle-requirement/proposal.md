## Why

`doodle-craft` 的版式规则里有一条**无条件的 MUST**：`references/page-layout.md` 写「两栏之间 MUST 有 `SplitHandle`（共享件）」，并声称这套分栏版式「由用例管理工作台（`/cases/projects/:id`）确立」。

代码事实两条都不成立：

1. `shared/components/SplitHandle.vue` 在 `src` 内**零引用**——没有任何页面渲染它。
2. `/cases/projects/:id` 当前渲染的是 `ProjectSheet.vue`（用例表），不是「左目录树 + 可拖动分隔 + 右只读预览」；该模块没有 tree / pane 相关代码。

即：技能在描述一个**当前不存在的版式**，还把「使用 SplitHandle」写成无条件 MUST。技能是它未被当成死代码删除的唯一依据。

需求方裁决：**保留组件、放宽规则口径**——不要求每个分栏都必须用它，只在确实采用可拖动分栏时强制使用，同时纠正「由用例管理工作台确立」这句失实描述。

## What Changes

- **改 `doodle-craft/references/page-layout.md`**：
  - 「由用例管理工作台（`/cases/projects/:id`）确立」——改为如实说明：该分栏壳是**可选版式**，当前无页面采用（用例管理工作台现为用例表）；姊妹模块若需要左树 + 右预览，照此实现。
  - 「左栏可拖动」行的 MUST 收窄为条件式：**若**采用可拖动分栏，**MUST** 使用 `SplitHandle`（共享件）并遵守其后全部交互细则（拖动范围、键盘步进、双击复位、按模块记忆宽度、窄屏不渲染手柄、不得另画第二条分隔线）；**若**左栏固定档位宽、不提供拖动，则 MUST NOT 渲染手柄。
- **保留** `shared/components/SplitHandle.vue` 与其在 `standalone-html.md` 里「手柄行为照抄 `shared/components/SplitHandle.vue`」的指引（该指引描述交互规格来源，与「是否有页面在用」无关）。
- **不动**：任何产品代码、任何 `openspec/specs/` 规格。

> **BREAKING**：无。本单只改技能文档，不改运行时行为，也不改规格。

## 关联文档

无 PRD 编号：本单是**设计系统技能的口径校正**，不涉产品行为。
依据：2026-11-24 前端复杂度体检（`SplitHandle` 零引用）+ 需求方裁决「改技能口径，保留组件」。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

（无 —— 技能文档不是 `openspec/specs/` 下的能力规格；产品行为与需求文本均未变化，故 `.openspec.yaml` 设 `skip_specs: true`。）

## Impact

- **修改**：`.agents/skills/doodle-craft/references/page-layout.md`（两处：来源说明、MUST 收窄）。
- **不动**：`SplitHandle.vue`、`standalone-html.md`、其它 doodle-craft 文档、任何 `frontend/src` 代码、任何 spec。
- **验证**：文档自洽性检查（不再有无条件「MUST 有 SplitHandle」；「确立」改为「可选」）；本单零代码改动，不触发前端门禁，但仍需确认 `SplitHandle.vue` 仍在库。
