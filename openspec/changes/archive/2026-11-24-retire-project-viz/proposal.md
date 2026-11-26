## Why

`dev_docs/project-viz/` 是仓库自绘的代码可视化看板（六个页面 + 生成器 + 图表底层），现状：**53 个文件、约 3.4 万行、2.5 MB**，其中绝大部分是生成产物（`board.json` 逾 1.1 万行、`history.json` 逾 7 千行、`styles.css` 3 千余行）。

它的问题不是「写得差」，而是**没有维护闭环**：

- **不在 CI**，没有任何测试引用，改坏了没人知道；
- **产物淹没真相**：真源只有一份生成器和一份手写架构 JSON，其余全是可再生数据，却与源码同目录同命名风格；
- **成为别人的参照负担**：`repo-viz-board` 与 `arch-diagram-lite` 两个技能都把它写成「参考实现」，`ruff.toml`、`.gitignore` 各有一条专为它开的例外——一个没人维护的目录仍在持续向规则与技能里渗透特例；
- 上一轮 WIP 曾试图重做它的管线（`simplify-project-viz-pipeline`，28/29 任务完成），现在需求方裁决：**不要了**。

本单把该目录连同专为它存在的 8 处配置/文档特例一并退役，让「谁在维护看板」这个问题消失，而不是继续挂着。

## What Changes

- **删除 `dev_docs/project-viz/` 整个目录**（53 个文件）。
- **清掉专为它存在的配置例外（2 处）**：
  - `.gitignore` 中放行 `dev_docs/project-viz/index.html` 与 `html/*.html` 的两条反选规则；
  - `ruff.toml` 中 `dev_docs/project-viz/tools/sync_sidebar.py` 的 per-file-ignore。
- **清掉把它当「参考实现」的技能表述（5 处，改述不删技能）**：
  - `repo-viz-board/SKILL.md` 的「参考实现：本仓库 `dev_docs/project-viz/`」；
  - `repo-viz-board/evals/evals.json` 里点名该目录的评测提示词（改为不依赖具体目录的同类场景）；
  - `repo-viz-board/assets/template/README.md` 中「见 `dev_docs/project-viz/ae-harness.js` 的实现」；
  - `arch-diagram-lite/SKILL.md` 的「参考实现：`dev_docs/project-viz/index.html` 第 1 节…」；
  - `arch-diagram-lite/references/decomposition.md` 中把它与 `gen_board_data.py` 对照的那一格。
- **修一处路径夹具**：`engines-docstring-check/scripts/selftest.py` 的 `SCOPE_CASES` 用 `dev_docs/project-viz/tools/a.py` 当「顶层目录」样例，换成一个仍存在的顶层目录路径（判定逻辑不变）。
- **不动**：`dev_docs/DEV_TEST/REVIEW-Agent文档审计复核与修复方案.md`（历史审计记录，如实保留）、`openspec/changes/repo-wide-python-docstring/design.md`（他人变更的规划产物）、仓库根的 `result.json` 与 `_acl-recovery/`（非本项目产物，另议）。

> **BREAKING**：无产品行为变化——该目录不进构建、不被后端/前端/引擎 import、不参与 CI。

## 关联文档

无 PRD 编号：本单是**文档工具退役**，不涉产品能力。
依据：需求方裁决「不要了」（2026-11-24，承接 `reconcile-wip-snapshot-with-head` 的 B 块）。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

（无 —— `openspec/specs/` 下无任何 `project-viz` 能力；该目录是文档工具，退役它不改变任何对外行为。故 `.openspec.yaml` 设 `skip_specs: true`。）

## Impact

- **删除**：`dev_docs/project-viz/`（53 个文件 / 约 3.4 万行 / 2.5 MB）。
- **修改**：`.gitignore`、`ruff.toml`、`.agents/skills/repo-viz-board/{SKILL.md,evals/evals.json,assets/template/README.md}`、`.agents/skills/arch-diagram-lite/{SKILL.md,references/decomposition.md}`、`.agents/skills/engines-docstring-check/scripts/selftest.py`。
- **不做**：不搬回 WIP 的重构版本（`simplify-project-viz-pipeline` 随之作废）、不迁移任何产物到别处、不新建替代看板。
- **验证**：该目录内文件数为 0；`project-viz` 在 `.gitignore` / `ruff.toml` / `.agents/skills` 内命中 0；`engines-docstring-check` 的 selftest 通过；`python -m run check` 通过。
