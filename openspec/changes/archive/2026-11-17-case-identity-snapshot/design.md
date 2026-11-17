## Context

动机见 proposal.md。现状：工作流提交把 `workflow.name` 写入 `Task.title`，平台用例只编译进附件 `platform-cases.yaml`，`Task.case_title` 保持空串。任务终态写入 `Task.result` 时会保留已有键，但该 JSON 不是身份字段。BUG 单没有外键，登记时抄任务快照。HTML 报告由 `engines/ae_harness` 渲染，入参只有任务名。

## Goals / Non-Goals

**Goals:**

- 用例身份只在提交时写一次，列表、BUG 单、仪表盘读同一句。
- 重跑与任务删除之后，身份仍然可读，且不回读用例库。

**Non-Goals:**

- 不改任务标题、BUG 标题、步骤名、报告 HTML、计费与任务状态。
- 不回填旧任务，不在同步历史错误时补用例身份。

## Decisions

### D1 身份放新 JSON 字段，不复用 `case_title` 或 `result`

`Task` 新增 `case_identity`（JSON，默认 `{}`）。形态只有两种：

- 平台：`{"source":"platform","rows":[{"project":"...","id":"...","title":"..."}]}`
- 里程碑：`{"source":"milestone","rows":[]}`
- 旧任务与未写入的任务：`{}`

`case_title` 保留给旧的「指定一条」语义，本变更不写它。`result` 会被终态覆盖流程碰到，不放身份。行标题取提交当时的值，最长按用例表 500 截断；项目名按 200 截断。

备选：从附件 YAML 的 `subject` 回拆。否掉，因为同名用例、上传里程碑和「用例 · 第 N 步」都会拆错。

### D2 展示文案只算不存

纯函数 `case_identity_label(identity)` 是唯一口径：

- 无身份或 `rows` 不是列表：`""`
- `source=milestone`：`里程碑`
- 一行：该行标题
- 多行：`{第一行标题} · 共 {N} 条`

空标题写成「未命名用例」，避免单元格空白。函数放 `task_list` 的无 Django 依赖模块，供序列化与 BUG 登记共用；前端各自实现同一规则，接口同时下发 `case_label` 与 `case_rows`，前端不重算计数。

### D3 平台编译时一并返回行身份

`case_manager.api.compile_automation_cases` 继续返回里程碑文本。新增只读函数返回按 `case_ids` 顺序的 `{project,id,title}`，校验失败与编译共用同一套拒绝原因。`task_list.views` 在创建任务前调用它，再经 `task_list.api.create_task` 写入。不让 `task_list` 直接读 `AutomationCase`。

上传分支写 `{"source":"milestone","rows":[]}`。两条分支都在 `create_task` 时写入，失败回滚由现有请求事务承担；若创建与附件保存不在同一事务，身份写入失败必须让提交返回 500，不得留下无身份的新任务冒充平台任务。实现时把创建、写身份、存附件放进同一事务。

### D4 重跑复制字段，不重新编译

`rerun_task` 已复制附件。本变更只追加复制 `case_identity`。不按 `id` 回查用例表。

### D5 BUG 单抄贝，不读附件

`BugTicket` 新增 `case_label`（500）与 `case_rows`（JSON，默认 `[]`）。登记时由 `bug_manager` 只读 `Task.case_identity`，调用同一纯函数，写入自己的列。`source_ref` 与 `title` 的生成规则不动。关键字增加 `case_label__icontains`。详情返回 `case_rows`；列表返回 `case_label` 即可。

已有单这两列为空。重复登记只在新值非空且与旧值不同时更新它们，避免一次空身份把已抄录的文案擦掉。处理状态仍不覆盖。

### D6 三处展示

- 任务清单：工作流列后加「用例」列。`case_label` 为空显示「—」；非空显示文案。`case_rows` 多于一条时，悬停按顺序显示「项目 / 标题」。
- BUG 详情：元信息增加「用例」。`case_label` 为空不渲染该行。`case_rows` 多于一条时在该行下列出「项目 / 标题」。
- 仪表盘：`recent_tasks` 增加 `case_label`。空串时前端不渲染副行。活动时间线不改，避免把用例名拼进「助手任务:」动作句。

## 模块防火墙自检

- `task_list` → `case_manager`：只调用 `api.py` 的只读编译/取行函数，不读 Model，不写用例库。
- `bug_manager` → `task_list`：继续只读 `Task` Model。身份字段在 Task 上，不新增对 `task_list.views` / `task_runner` 的依赖。
- `dashboard` → `task_list`：继续只读 `Task`，不写库。
- 写库仍走各自 `api.py`：任务经 `create_task` / `rerun_task`，BUG 经既有 `_upsert_draft`。
- 前端只读新字段，不直连数据库。
- 引擎不参与。报告渲染不新增跨包依赖。

## Risks / Trade-offs

- [主规格仍写任务详情页与按用例拆 BUG 单，和现行代码不一致] → 本变更只用 ADDED，不修改那些过时条文；实现以现行代码和本 delta 为准。
- [选择上百条时悬停很长] → 单元格仍是一句；悬停与详情允许滚动，不换行撑高表格。
- [创建与附件不在同一事务] → 提交路径收进一个事务；失败不留任务。
- [前端与后端各有一份空值展示] → 计数与文案由后端 `case_label` 给出，前端只决定空值显示「—」还是不渲染。

## Migration Plan

1. 加 `Task.case_identity` 与 `BugTicket.case_label` / `case_rows`，默认空，不回填。
2. 先写提交与重跑，再接列表、BUG、仪表盘。
3. 回退：字段可留空不用；前端不读新字段即恢复旧表。已写入的快照不删除。

## Open Questions

无。展示口径已在探索中确认：多选用「第一条 · 共 N 条」加悬停；上传里程碑显示「里程碑」，不写文件名。
