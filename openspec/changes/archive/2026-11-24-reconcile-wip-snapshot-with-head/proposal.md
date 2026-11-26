## Why

2026-11-24 的在制改动被整体压在 WIP 提交 `1228869b` 上（分支 `wip/docstring-snapshot-2026-11-24`），不在当前分支线上。它同时装了**三块性质不同**的内容，而其中最大的一块已经被后续两个提交废掉：

| 块 | 内容 | 现状 |
|---|---|---|
| A | 前端死代码清理（14 个零引用文件、30 个死图标、3 个死动画导出、15 个死常量、时间格式化收口） | **仍有价值**，但今天已按当前 HEAD 做过一部分 |
| B | `dev_docs/project-viz` 看板与管线重构 | **不要了**——需求方裁决退役整个目录，已移交 `retire-project-viz`（归档 `2026-11-24-retire-project-viz`） |
| C | 全仓 docstring / 注释补齐（engines / tests / backend / .agents/docs 等） | **已作废**——`AGENTS.md` 改为「全仓代码不写注释」，提交 `ab494da8` 把所有注释删光了 |

直接合并这条分支不可行：以 `2111f52c`（2026-11-23）为分叉点，WIP 改了 **1107 个文件**，当前 HEAD 改了 **1537 个**，**两者重叠 1012 个（91%）**——因为两边都在改同一批文件的注释层，一侧加、一侧删。这不是「几处冲突」，是把整棵树当冲突。

本单的目标**不是把分支合进来**，而是按块裁决：**丢弃 C、重做 A、B 移交退役单**，让三块各自落到与当前基线一致的状态。

## What Changes

- **C 块整体丢弃（不搬任何注释 / 规范改动）**：`.agents/rules`(2) / `.agents/docs`(51) / `engines`(82) / `tests`(216) 及 `frontend/src` 中纯注释差异，一律以当前 HEAD 的「无注释」状态为准。**本单不恢复任何 docstring 规范文件**。
- **A 块按当前 HEAD 重做剩余部分**（今天已完成的子集不重复，见下表）：
  - 删除剩余 11 个零引用文件：`StepScreenshotPanel.vue`、`TaskOutcomeDonut.vue`、`TaskMediaThumb.vue` + `.style.css`、`CaseImportCard.vue`、`TaskShareCharts.vue`、`DualAxisBarLineChart.vue`、`SeriesBarChart.vue`、`RateBar.vue`、`useExpandCollapse.ts`、`ocrMatch.ts`、`yaml-case-titles.ts`（含 3 个失效用例）。
  - 图标库 45 → 15；动画导出去 `selectPop` / `iconBounce` / `loadingDots` 并清理只服务它们的 `.wb-loader` / `.wb-select-ring`。
  - 任务清单常量去 15 个死项。
  - 时间格式化收口到 `shared/helpers/datetime.ts`（4 原语 + 2 组选项），5 个调用方改引；设备池非法时间由 `Invalid Date` 改为「—」。
  - **全部按当前基线重写为无注释版本**，并补等价快照用例（先锁现值再换实现）。
- **B 块移交退役（不在本单执行）**：需求方裁决「不要了」，`dev_docs/project-viz/` 整个目录连同专为它存在的配置/技能特例已由 `retire-project-viz` 删除并归档。本单因此**不再搬回** WIP 的看板重构版本，`simplify-project-viz-pipeline` 随之作废。搬回后同样满足「不写注释」。
- **openspec 规划产物只搬 B 相关的**：`simplify-project-viz-pipeline` 的 artifacts 搬回并继续推进（它本就有 28/29 任务完成）；**A 的旧归档 `2026-11-24-prune-frontend-dead-code` 不搬**——它描述的是带注释的旧实现，搬回来会与当前代码不符，由本单重新记录。

> **BREAKING**：无对外行为变化。A 是删除零引用代码，B 是文档工具的产物重构，C 不执行。

## 关联文档

无 PRD 编号：本单是**分支协调 + 工具链清理**，不改变产品行为。
依据：`git` 实测（分叉点 `2111f52c`、重叠 1012/1107）+ 需求方裁决「单独开一个 change 处理它与两提交的冲突」。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

（无 —— A 删的是零引用代码且无 spec 承载其存在；C 不执行。B 的 `dev_docs/project-viz` 本身是文档工具，但搬回的 `simplify-project-viz-pipeline` **自带 `specs/project-viz/spec.md`（新能力 delta）**，那份 delta 属于该单、由它自己归档时并入主规格；本单只做搬运与推进，不代替它归档，故本单自身 `skip_specs: true`。）

## Impact

- **丢弃**：WIP 中约 398 个文件的注释/docstring 改动（不落盘）。
- **删除**：`frontend/src` 11 个文件 + `frontend/tests` 3 个用例文件（A 的剩余部分）。
- **局部修改**：`shared/icons/index.ts`、`shared/animations.ts`、`shared/styles/motion.css`、`modules/task-list/constants.ts`、`shared/helpers/datetime.ts` + 5 个调用方。
- **删除**：`dev_docs/project-viz/`（53 个文件 / 约 3.4 万行）——由 `retire-project-viz` 执行并归档，不在本单重复。
- **不动**：今天 4 单已完成的删除（`task-detail.ts` / `mediaUrl.ts` / `DoodleNote.vue` 及 3 个用例）、任何他人未提交改动（`TodayUsageChart.vue`、`useECharts.ts`、`style.css`、`echarts-setup.ts`）。
- **门禁**：`npm run typecheck` + `npm run build` + `npm run lint:styles` + `npm run test`；`dev_docs/project-viz` 按其自带自检跑。
