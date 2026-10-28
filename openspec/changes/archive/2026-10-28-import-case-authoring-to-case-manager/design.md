## Context

现状：Agent-02 的用例只存在 `Task.result.document`（Markdown），报告页直接渲染这份文档；用例管理已有 `CaseProject` → `CaseDirectory` → `CaseFile` → `TestDefinition` + `CaseStep` 的完整写路径（`case_manager/api.py`），且所有查询按 `created_by` 隔离。任务表没有发起人字段，任务可见性靠 `Task.agent` 反查 `AIAgent` 的可见性。

约束：跨 App 写必须走对方 `api.py`；引擎侧只做纯解析，不依赖 Django；报告接口是全局 `{status, data}` 信封；任务终态与报告缓存以 `Task.status` + 事件最大 `seq` 为键。

## Goals / Non-Goals

**Goals:**

- 验收通过的用例进入当前用户的「AI 生成用例」项目，一个任务一个文件。
- 用例字段、步骤、模块、来源任务可追溯，重复导入不产生重复数据。
- 报告只保留任务摘要、入库结果卡、模型事件流与验收意见，跳转地址直达用例文件页。
- 导入是可降级后处理：失败不改变任务验收结论。

**Non-Goals:**

- 不导入需求原子表、方法分配表、E2E 旅程、冲突登记与待确认问题；这些仍留在 `Task.result.document` 作为审计原文。
- 不在新建任务表单里选择目标项目/目录；本轮固定写「AI 生成用例」项目。
- 不做「失败任务草稿入库」、人工审核后入库、增量更新已有用例。
- 不改用例管理的读接口、项目工作台与文件表格的编辑交互。

## Decisions

### 1. 复用现有用例模型，不新建 AI 用例表

`TestDefinition` + `CaseStep` 已经覆盖「单条用例 + 有序步骤」，`CaseFile` 正好承载「一个任务一张表」，`CaseProject` 承载用户级归属。新增一张 AI 专用表会复制字段、破坏仪表盘按项目统计与现有编辑能力。

备选：新建 `AiCaseDraft` 表，等人工确认后再转正式用例。代价是多一套状态机与页面，本轮不做。

### 2. 固定项目 + 每任务一个文件

项目名固定为「AI 生成用例」，按 `(created_by, name)` 唯一；文件名为 `{任务标题}（任务 {id}）`，截断到 200 字符，按 `(project, directory, name)` 唯一。任务 id 后缀保证同名任务不互相覆盖，也让文件与任务一一对应。

备选：任务表单选择项目/目录。归属更灵活，但要把 case-manager 项目接口接进 task-list，并处理「用户没建项目」的空态；本轮不做。

### 3. 任务增加创建人快照，导入归属发起人

`Task` 增加 `created_by` 字符串字段（默认空）。提交时写 `request.user_id`，重跑复制原值；历史任务为空时回退 `task.agent.owner_id`，两者都为空则跳过导入并记失败原因。

不能直接用 `agent.owner_id`：Agent-02 是超管共享智能体，普通用户跑出的用例会写进超管项目，普通用户在用例管理里看不到。

### 4. 导入放在任务收尾、落库之前，同步执行

`task_runner._run_case_authoring` 得到 `CaseAuthoringResult` 后，先解析并导入，把 `case_import` 放进返回的 result，再 `finalize_task`。导入在同一后台线程内完成，不引入队列/异步回调；单任务用例量通常 10~40 条，写入耗时可接受。

备选：任务完成后再由前端触发导入。会把「是否已导入」变成前端状态，刷新/多端不一致，且失败无法回写任务结果。

### 5. 解析扩展放在引擎，持久化放在 case_manager

`case_document_check.py` 增加：
- `CaseRow.module`：跟踪 `## 模块：NAME（KEY）` 标题；
- `case_step_pairs(case)`：按 `<br>` 拆分「测试步骤」「预期结果」，去掉 `1)` / `1.` 前缀，按序号配对；两侧数量不一致时退化为一条步骤（完整步骤 → 完整预期），不猜测缺失项。

`task_list` 把解析结果转成中性行（标题、优先级、模块、前置条件、步骤、来源用例编号），调用 `case_manager.api.import_case_rows`。`case_manager` 不反向依赖 `task_list`，引擎不依赖 Django。

### 6. 幂等靠来源任务 + 文件复用

`TestDefinition` 增加 `source_case_id` 与 `source_task_id`（均可空、带索引）。导入前按 `source_task_id` 查该文件下是否已有用例：有则直接返回原文件与条数；无则在单事务内创建项目、文件与全部用例。任一步失败整体回滚。

备选：每次导入先删后建。会覆盖用户对已导入用例的编辑，且失败时可能丢数据，不采用。

### 7. 报告契约改为「入库结果 + 事件流」

`case_import` 结构固定为：

```json
{
  "status": "imported | skipped | failed",
  "project_id": 12,
  "file_id": 34,
  "path": "/cases/projects/12/files/34",
  "case_count": 18,
  "skipped_count": 0,
  "message": ""
}
```

报告不再返回 `document`；`path` 只在 `imported` 时非空。前端用 `router-link` 跳转，不拼 host/port。完整 Markdown 仍保留在 `Task.result.document`，仅作为审计与重导入来源。

### 8. 前端只删文档区、加入库结果卡

`TaskDetailPage.vue` 删除 `renderMarkdown`、`documentHtml` 与「生成的测试用例」区块；在事件流之前加入「用例入库结果」卡：成功显示条数与「打开用例文件」，失败/跳过显示原因。`helpers/markdown.ts` 与其单测随渲染入口一起删除。

## 模块防火墙自检

- `task_list` → `case_manager`：只经 `backend.apps.case_manager.api.import_case_rows` 写库，符合「跨 App 写走 api.py」；不 import `case_manager` 的 view/serializer/内部实现。
- `case_manager` → `task_list`：无依赖；导入行由调用方传入，不读 `Task`。
- `task_list` → `engines.agents.workflow.case_document_check`：只调用纯函数解析，不写库、不反向依赖 App。
- `case_manager/api_import.py` 归属 case_manager 写路径，内部可读本 App Model；所有写入从 `api.py` 导出，View/Tool 可复用。
- 前端只经既有 `/api/cases/*` 读页面，报告只经 `/api/tasks/{id}/report/`；不新增直连数据库或直写接口。

## Risks / Trade-offs

- [并发首次导入同一用户] 两个任务同时创建「AI 生成用例」项目，唯一约束冲突 → `get_or_create` 捕获 `IntegrityError` 后重查一次。
- [同名项目/文件已存在] 文件带任务 id 后缀，项目按用户唯一；冲突时复用已有记录，不报错。
- [导入部分行不合法] 逐行跳过并计数，不因单行阻断整批；全部跳过时返回 `skipped`，不建空文件。
- [步骤数与预期数不一致] 退化为一条完整步骤，保留原文，不编造对应关系；可能不如逐条精确，但可判定、可编辑。
- [报告不再返回 document] 属于对外契约破坏性变更 → 前端同一提交更新；旧前端若仍读 `document` 会显示空，需与后端同版本部署。
- [历史任务无 created_by] 回退 Agent owner；若仍为空则跳过导入，任务结论不受影响。
- [报告缓存] `case_import` 在 `finalize_task` 前写入 result，终态缓存键包含状态与最大 seq，不会缓存到导入前的旧值。

## Migration Plan

1. 发布 `task_list` 迁移（`Task.created_by` 可空默认空）与 `case_manager` 迁移（`source_case_id` / `source_task_id` 可空）。
2. 部署后端：新任务开始记录创建人；导入逻辑只对 `passed=true` 的新任务生效，历史任务不受影响。
3. 部署前端：报告切到入库结果卡；旧报告数据没有 `case_import` 时显示「未入库」提示。
4. 回滚：前端先回退；后端保留新增可空字段即可，无需回滚数据。已导入的用例是正常业务数据，回滚不删除。

## Open Questions

无。目标项目、写入范围、文件粒度已由用户确认；E2E/原子不入库列为 Non-Goal。
