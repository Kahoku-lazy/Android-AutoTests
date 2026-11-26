## Context

分叉点 `2111f52c`（2026-11-23「归档 retire-dsh-plugins」）。WIP 提交 `1228869b`（2026-11-24 16:01）的实测构成：

| 区域 | WIP 改动文件 | HEAD 改动文件 | 重叠 | 判断 |
|---|---:|---:|---:|---|
| `frontend/src` | 49 | 251 | 47 | 重叠部分是注释差异 → A 需重做 |
| `frontend/tests` | 10 | 76 | 2 | 大多数是 WIP 独有（死用例删除）→ A 可低成本重做 |
| `dev_docs/project-viz` | 55 | 12 | 9 | 重叠是「HEAD 改 / WIP 删」→ B 可定点搬回 |
| `engines` | 82 | 104 | 81 | docstring 块 → C 丢弃 |
| `tests` | 216 | 221 | 216 | docstring 块 → C 丢弃 |
| `.agents/docs` | 51 | 52 | 51 | docstring 块 → C 丢弃 |
| `.agents/rules` | 2 | 2 | 2 | docstring 规范 → C 丢弃 |

合计 WIP 1107 文件，与 HEAD 重叠 **1012**。

关键约束：`AGENTS.md` 现已规定「全仓代码不写注释」，`ab494da8` 已把全仓注释删净；`e0e1a0fb` 已移除 `pinia` / `mermaid` / `marked` / `dompurify` / `mitt` / `playwright` 与 `fastapi` / `uvicorn`，并同步了 `frontend/AGENTS.md` 的技术栈（去 Pinia / Mermaid，Vite 6）。

## Goals / Non-Goals

**Goals:**

1. 让三块内容各自有明确归宿：C 丢弃并留痕、A 重做到底、B 定点搬回。
2. 全程遵守「不写注释」与「零引用依赖已移除」两个新事实。
3. 不碰任何人未提交的改动。

**Non-Goals:**

- 不做 `git merge` / `git rebase` / 整分支 `cherry-pick`（见 D1）。
- 不恢复任何 docstring 规范文件，也不为「补齐注释」补任何一行注释。
- 不改产品行为：A 只删零引用代码，B 只动文档工具产物。
- 今天 4 单已完成的删除不重复做。

## Decisions

**D1：不合并分支，按块处置。**
1012/1107 的重叠意味着 `git merge` 会把整棵树变成冲突战场，且 91% 的冲突内容是「一侧加注释、一侧删注释」——没有任何业务分歧，纯噪声。用合并解决它，代价远高于重做。备选：merge → 否决。

**D2：C 块丢弃，且要「留痕地丢弃」。**
不是因为麻烦，而是因为**方向相反**：C 的产出是「补齐 docstring/注释」，而现行规则是「全仓不写注释」。留着 C 的任何产物都会与规则直接冲突。故：不 checkout、不参考、在关单里写明「已作废，勿再搬」。
`frontend/src` 里那 47 个重叠文件同属此类——差异只是注释，一律以当前 HEAD 为准。

**D3：A 块按当前 HEAD 重做，不搬补丁。**
把 WIP 的 diff 打过来会连注释一起带回来（这些文件在 WIP 里都带 docstring）。正确做法：按今天已做过的同一套流程重做——先写等价快照（锁定现值），再删/改，再验证断言一字未改。
**已完成的子集不重复**：`task-detail.ts`、`mediaUrl.ts`、`DoodleNote.vue` 及 3 个对应用例已由今天的 4 单删除。

**D4：B 块移交退役单，本单不做。**
原计划用 git checkout 1228869b -- dev_docs/project-viz 定点搬回；需求方随后裁决「不要了」，于是改为由 
etire-project-viz 退役整个目录（含 .gitignore / 
uff.toml 的专属例外与两个技能的「参考实现」表述）。本单只记录该移交，不重复执行。

**D5：openspec 产物只搬 B 的，不搬 A 的旧归档。**
`simplify-project-viz-pipeline` 有 28/29 任务完成，搬回继续推进是合理的。`2026-11-24-prune-frontend-dead-code` 的归档描述的是带注释的旧实现（含 `formatIsoNaive` 等已不存在的函数），搬回会让 openspec 历史与代码不符；本单重新记录 A，旧归档留在 WIP 分支上。

**D6：只读地使用 WIP 分支。**
全程只做 `git diff` / `git show` / `git checkout <commit> -- <path>`，不对 `wip/docstring-snapshot-2026-11-24` 做任何写操作，也不切换当前分支。

**D7：`skip_specs: true`，但 B 块会带进一份别人的 delta。**
A 删的是零引用代码（无 spec 承载）；C 不执行。B 搬回的 `simplify-project-viz-pipeline` 自带 `openspec/changes/simplify-project-viz-pipeline/specs/project-viz/spec.md`——一份**新增能力**的 delta。它属于那一单：搬回后由它自己推进与归档（归档时才并入主规格），本单不代替它归档，也不改它的 Requirement 文本。因此本单自身零 delta。

## 模块防火墙自检

- **跨 App import**：不涉及。
- **禁跨层依赖**：A 只删文件与改 `shared/` 内部；B 不进 Vite 构建、不 import `frontend/`。
- **写库收敛**：不涉及。
- **前端不直连数据库**：维持。
- **仪表盘只读**：不涉及。

## Risks / Trade-offs

- **[A 重做与今天的 4 单边界不清，导致重复删除或漏删]** → tasks 里逐文件列出「剩余待删」，并在开工前用 `Test-Path` 核对「今天已删的不在清单里」。
- **[B 搬回后与 `AGENTS.md` 自述不一致]** → D4 的三项复核作为验收条件。
- **[将来又有人在 WIP 分支上继续改，产生第二份真相]** → 本单执行完应在关单注明该分支「除归档记录外不再作为开发线」，由需求方决定是否删除。
- **[C 块被后人重新捡起]** → 关单与本设计明确写「已作废，勿再搬」，并在 `.agents` 相关处不新增任何指向它的说明。
