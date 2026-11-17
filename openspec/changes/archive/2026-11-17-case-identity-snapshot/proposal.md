## Why

从平台选了用例之后，任务标题写的是工作流名，用例标题没有落库。任务清单、报告抬头、BUG 单和仪表盘都只能看出跑的是哪条工作流，看不出选了哪条用例、做了什么。

## What Changes

- 提交工作流任务时冻结一份用例身份快照。平台来源按选择顺序记下项目名、行编号和当时标题；上传里程碑只记来源，不把文件名当成用例标题。
- 任务清单增加「用例」列。一条显示标题；多条显示「第一条 · 共 N 条」，悬停展开「项目 / 标题」。上传里程碑显示「里程碑」。旧任务显示「—」，不回填。
- 重跑复制整份快照，不回读用例库。用例后来改名或删除，历史任务不变。
- BUG 单标题仍用失败步骤或失败类别。登记时把同一句展示文案和行列表抄进 BUG 快照；详情展开全部行，关键字可搜这句文案。已有 BUG 单不补、不改标题、不改幂等键。
- 仪表盘最近任务卡在工作流名下增加同一句副行。HTML 报告由引擎渲染、不认识用例库，本次不改报告抬头。

## 关联文档

无独立需求编号。本次范围来自本轮确认：用例身份从选择一直跟到任务清单和 BUG 单，便于一眼看出做了什么、结果是什么。`PRD-平台总需求.md` 未单列该字段。不改任务状态、计费和 BUG 标题规则。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- `task-card-sop-form`: 平台提交冻结用例身份；上传里程碑只记来源；重跑复制快照。
- `task-list-module`: 任务清单展示由快照算出的同一句用例文案，旧任务为空。
- `bug-ticket-management`: BUG 单抄录同一句文案和行列表，标题与幂等键不变。
- `dashboard-agent-tasks`: 最近任务卡增加用例身份副行。

## Impact

- 后端：`backend/apps/task_list/`（模型、提交、列表、重跑）、`backend/apps/case_manager/api_rows.py`（编译时交出来源行）、`backend/apps/bug_manager/`（登记与搜索）、`backend/apps/dashboard/ai_usage.py`。
- 前端：`frontend/src/modules/task-list/`、`frontend/src/modules/bug-manager/`、`frontend/src/modules/dashboard/`。
- 接口：任务列表与 BUG 列表增加用例身份字段。任务标题、BUG 标题、报告渲染契约不变。
- 测试：`tests/task/`、`tests/bug_ticket/`、`frontend/tests/task-list/`、`frontend/tests/bug-manager/`。
