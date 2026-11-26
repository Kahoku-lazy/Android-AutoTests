## Context

`dev_docs/project-viz/` 构成：`tools/`（4 个生成器约 2,100 行）、`data/`（`board.json` 11,074 行 + `history.json` 7,398 行 + 两份对应的 `.js` 镜像）、`charts/`（`board-options.js` 1,261 行）、`html/`（22 个静态页）、页面壳（`index.html` + `overview.js` 543 + `styles.css` 3,219）、若干模块页脚本。

引用面实测（排除该目录自身与 `openspec/changes/archive/**`）：

| 位置 | 性质 |
|---|---|
| `.gitignore` 2 条反选 | 专为它放行 HTML |
| `ruff.toml` 1 条 per-file-ignore | 专为它关掉 `T201` |
| `repo-viz-board/SKILL.md` / `evals.json` / `template/README.md` | 把它当参考实现 |
| `arch-diagram-lite/SKILL.md` / `references/decomposition.md` | 把它当参考实现 |
| `engines-docstring-check/scripts/selftest.py` | 拿它当「顶层目录」路径夹具 |
| `dev_docs/DEV_TEST/REVIEW-Agent文档审计…md` | 历史审计记录 |
| `openspec/changes/repo-wide-python-docstring/design.md` | 他人变更的规划产物 |
| `result.json` / `_acl-recovery/*.json` | 仓库根的旁产物（非本项目） |

## Goals / Non-Goals

**Goals:**

1. 目录消失后，**没有任何配置或技能仍在为一个不存在的路径开特例**。
2. 两个技能仍然可用——只去掉「本仓库的参考实现」这层绑定，方法论本身保留。
3. 退役过程可回退：删的是工作树文件，`git` 历史完整保留。

**Non-Goals:**

- 不搬 WIP 的重构版本，也不把任何产物迁到别处。
- 不新建替代看板；若日后要看依赖/代码量，走 `arch-diagram-lite` 的轻量方案或临时脚本。
- 不改 `dev_docs/DEV_TEST` 的历史审计记录，也不改他人变更的 `design.md`。
- 不清理仓库根的 `result.json` / `_acl-recovery/`（来源不明，另议）。

## Decisions

**D1：整目录删，不做「保留生成器、删产物」的半退役。**
半退役会留下一个「生成器在、产物没了、没人跑」的空壳，正好是本次要消灭的形态。若日后需要看板，重新按技能从零生成比修复一个沉睡管线更省。

**D2：技能里的「参考实现」改成中性表述，而不是删技能。**
`repo-viz-board` 与 `arch-diagram-lite` 是可复用方法论（模板 + 语法子集 + 令牌口径），参考实现只是引子。删掉引子，方法论仍成立。备选：连技能一起删 → 否决，那是把「某个实现退役」误当成「能力退役」。

**D3：`evals.json` 的评测提示词改写成不依赖具体目录的同类场景。**
该评测考的是「在已有看板上做增量修改」，把它绑在某个目录上会让评测随目录消失而失效。改写成「这个代码可视化看板里的 agents 页…」即可保住评测意图。

**D4：`SCOPE_CASES` 的路径夹具换成仍存在的顶层目录。**
它是纯分类判定夹具（不要求路径真实存在），但留着已删目录会让后来者以为 `dev_docs` 下仍有 `project-viz`。换成 `dev_docs/ARCH_PRD/a.py`，判定原因仍是「顶层目录」，测试语义不变。

**D5：历史与旁证文档一律不动。**
审计记录写的是「当时的事实」，改它等于篡改历史；他人变更的 `design.md` 不属本单管辖。两者都在关单里登记为「保留并说明」。

**D6：`skip_specs: true`。**
`openspec/specs/` 无 `project-viz` 能力，退役文档工具不产生需求级变化。不为通过校验虚构能力。

## 模块防火墙自检

- **跨 App import**：不涉及（删的是 `dev_docs/` 下的静态工具）。
- **禁跨层依赖**：该目录本就不被 `backend/` / `engines/` / `frontend/` import（实测无引用）。
- **写库收敛**：不涉及。
- **前端不直连数据库**：维持。
- **仪表盘只读**：不涉及。

## Risks / Trade-offs

- **[有人仍想看依赖图/代码量看板]** → 关单写明替代路径（`arch-diagram-lite` 轻量图，或临时脚本生成，不入库）。
- **[`ruff.toml` / `.gitignore` 删错行影响其它路径]** → 只删点名 `project-viz` 的那几行，改完跑 `python -m run check` 与 `ruff` 配置解析。
- **[技能改述后触发率下降]** → `repo-viz-board` 的技能描述（description）不改，只改正文里的参考实现句；评测提示词同步改写以保持覆盖。
- **[WIP 分支上的 `simplify-project-viz-pipeline` 变成悬空]** → 关单登记「该变更随之作废，不再搬回」；其归档仍在 WIP 分支上，不影响本线。
