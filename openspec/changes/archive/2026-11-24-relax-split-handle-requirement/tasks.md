## 1. 校正版式来源说明

- [x] 1.1 `.agents/skills/doodle-craft/references/page-layout.md`：把「由用例管理工作台（`/cases/projects/:id`）确立，姊妹模块可照抄」改为如实表述——这是一套**可选**分栏版式，当前无页面采用（用例管理工作台现为用例表 `ProjectSheet`）；姊妹模块若需要左树 + 右预览，照此实现。验证：该行不再出现「确立」，且明确写出「当前无页面采用」。

## 2. 收窄 SplitHandle 的 MUST

- [x] 2.1 同文件「左栏可拖动」行：把「两栏之间 MUST 有 `SplitHandle`（共享件）」改为条件式——**若采用可拖动分栏，MUST 使用 `SplitHandle`**；**若左栏固定档位宽、不提供拖动，则 MUST NOT 渲染手柄**。其后全部交互细则（220px ~ min(560px, 容器宽 − 360px) 夹取、← / → 16px、Shift 48px、Home / End、双击复位到 T0、`app-split-<mod>-tree-w` 记忆、窄屏不渲染、不得另画第二条分隔线）**逐字保留**。验证：该行仍含 `MUST`（条件成立时强制），细则一项不少。
- [x] 2.2 该行标签由「左栏可拖动」改为「左栏可拖动（可选）」，与条件式一致。验证：标签与正文语义无矛盾。

## 3. 确认组件与其它文档不受影响

- [x] 3.1 确认 `frontend/src/shared/components/SplitHandle.vue` **未改动**（本单零代码改动）。验证：`git status --porcelain` 不含该文件。
- [x] 3.2 确认 `references/standalone-html.md` 的「手柄行为照抄 `shared/components/SplitHandle.vue`」指引仍在。验证：该句命中数 1。
- [x] 3.3 复扫 `page-layout.md` 内是否还有其它「无条件 MUST 使用 SplitHandle」表述。验证：结果为 0 或仅剩本次改后的条件式。

## 4. 关单

- [x] 4.1 `openspec validate relax-split-handle-requirement --strict` 通过（`skip_specs: true`，零 delta）。验证：输出 `Change 'relax-split-handle-requirement' is valid`。
- [x] 4.2 关单汇报写明：本单零代码改动、`SplitHandle.vue` 保留且仍零引用、将来做分栏时按条件式 MUST 使用它；并把「组件保留、不要因零引用再来删」写清。随后归档。
