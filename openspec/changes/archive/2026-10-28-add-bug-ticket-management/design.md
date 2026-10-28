## Context

任务结果已经结构化落在 `Task.result`：UI 自动化任务有 `failed`（失败用例标题列表）与 `reason`；用例编写任务有 `passed`、`verdicts`、`modules`、`reason`、`case_import`。任务终态统一由 `task_list.api.finalize_task` 写入，服务重启遗留的 `running` 由 `recover_orphaned_tasks` 改为 `interrupted`。平台现有任务可见性按 `AIAgent` 的用户可见范围过滤，前端导航由 `sidebarNavConfig.ts` 单一配置驱动。约束：跨 App 写只能走对方 `api.py`；任务删除是调试动作；报告接口不返回完整文档。

## Goals / Non-Goals

**Goals:**

- BUG 单与任务解耦存储：任务删除后 BUG 单仍可查，保留任务编号与标题快照。
- 自动登记与历史补录共用同一套提取规则，幂等且不覆盖人工处理状态。
- 列表、统计与详情都按当前用户可见 Agent 隔离。
- 前端只通过 `/api/bugs/*` 读写，任务链接直达 `/tasks/:id`。

**Non-Goals:**

- 不做 BUG 评论、附件、指派、优先级、SLA、导出。
- 不自动修改或关闭来源任务，不根据 BUG 状态回写 `Task.result`。
- 不把产品被测失败（UI 自动化失败用例）与平台代码缺陷再做二级区分；本轮只按任务类型分两类。
- 不为 BUG 单新建独立详情路由；详情用抽屉，避免与任务详情抢导航层级。

## Decisions

### 1. 新建 `bug_manager` App，`BugTicket.task_id` 不用外键

用独立表 `bug_tickets` 保存台账；`task_id` 用带索引的整数快照，不建 FK。理由：任务删除是调试动作，BUG 记录属于审计数据，不应随任务级联删除；同时避免 `task_list` 与 `bug_manager` 的迁移依赖成环。任务标题、任务类型、Agent 编号一并快照，列表不依赖任务表即可展示。

备选：FK `Task` + `SET_NULL`。能保证引用完整性，但删除任务会丢关联或产生空值，且迁移依赖更重，不采用。

### 2. 分类由任务类型映射，来源键保证幂等

`BugCategory` 固定 `ui_automation` / `case_authoring`，由 `TaskKind` 映射。唯一约束为 `(task_id, category, source_ref)`：

- UI 自动化任务级：`source_ref="task"`；
- UI 自动化失败用例：`source_ref="case:<sha1(用例标题)[:16]>"`，避免把长标题塞进唯一索引；
- 用例编写任务级：`source_ref="task"`；
- 用例入库失败：`source_ref="import"`。

同步用 `get_or_create`，已存在时只更新标题、正文、任务标题/类型/Agent 快照，不更新 `status` 与 `resolved_at`，从而保留人工处理结果。并发唯一冲突时捕获 `IntegrityError` 后重查一次。

### 3. 提取规则放在纯函数模块

`bug_manager/extract.py` 提供 `build_bug_drafts(task_like)`，只接收任务对象属性与已解析的 `result` 字典，返回 `BugDraft` 列表，不访问数据库、不依赖 Django。规则：

- `cancelled` → 空；
- UI 自动化 `failed` 且 `failed` 列表非空 → 每个标题一张；否则一张任务级；
- UI 自动化 `interrupted` → 一张任务级；
- 用例编写 `failed` → 一张任务级，正文拼接 `summary`、`reason`、失败模块的 `message`、最后一条验收意见；
- 用例编写 `completed` 且 `case_import.status=failed` → 一张入库失败；
- 其他状态 → 空。

标题格式固定：`UI 自动化失败：<用例标题>`、`UI 自动化任务失败：<任务标题>`、`测试用例编写未通过：<任务标题>`、`测试用例入库失败：<任务标题>`，超过 500 字符截断。

### 4. 自动登记挂在终态写库之后

`finalize_task` 完成 `Task.save` 后调用 `bug_manager.api.record_task_bugs(task)`，异常只记日志、不影响任务返回；`recover_orphaned_tasks` 把任务改为 `interrupted` 后逐条调用。把登记放在任务落库之后，避免 BUG 正文读取到旧状态；放在任务状态判定之外，避免登记失败改变任务结果。

备选：Django signal。会在任意 `Task.save()` 触发，测试与批量更新容易产生意外登记，不采用。

### 5. 历史补录用显式同步接口 + 管理命令

`POST /api/bugs/sync/` 扫描当前用户可见的 `failed` / `interrupted` 任务与 `completed` 的用例编写任务，逐个调用 `record_task_bugs`，返回 `scanned/created/updated/skipped`。另提供 `python manage.py sync_bug_tickets` 供部署后一次性补录。页面提供「同步历史错误」按钮，避免 GET 产生写副作用。

### 6. 列表接口服务端过滤，详情单独取

`GET /api/bugs/` 接受 `category`、`status`、`keyword`，返回 `summary` 与 `items`；`items` 只带 `detail_preview`（前 240 字），完整正文走 `GET /api/bugs/{id}/`。统计口径为当前用户可见全集，不受分类/状态过滤影响，便于页头 KPI 稳定。关键字匹配 BUG 标题、正文、任务标题与 `task_id` 字符串。

### 7. 状态更新用 PATCH，状态机极简

`PATCH /api/bugs/{id}/` 只接受 `status`，允许 `open` / `resolved` / `ignored` 任意互转。置 `resolved` 时写 `resolved_at`，其他状态清空。非法值返回 400。用 DRF 视图 + `api.py` 写库，不引 ViewSet 的额外路由。

### 8. 前端单页 + 抽屉

新增 `frontend/src/modules/bug-manager/`：

- `/bugs` 单路由；页头、KPI、分类 FilterTabs、状态筛选、关键字、同步按钮、AppTable；
- 行点击打开 `el-drawer`，抽屉内加载详情，展示错误正文、任务链接、状态切换；
- 任务链接用 `router-link` 或 `router.push('/tasks/' + task_id)`，不拼 host；
- 分类色：UI 自动化用 `--c-ai`，用例编写用 `--c-case`；页面模块色用 `--c-runner`，与任务/报告区分；
- 表格列：BUG 编号、分类、标题、关联任务、状态、创建时间、操作。

## 模块防火墙自检

- `task_list` → `bug_manager`：只在 `finalize_task` / 启动恢复内调用 `backend.apps.bug_manager.api.record_task_bugs`，属于跨 App 写走 `api.py`；不 import 其 model/view/serializer。
- `bug_manager` → `task_list`：同步扫描时只读 `Task` Model；不 import `task_list` 的 views/runner/task_reports。`record_task_bugs` 接收任务对象，不反向调用任务写接口。
- `bug_manager` 内部：所有 INSERT/UPDATE 收敛到 `api.py`；视图只做参数校验与序列化。
- 前端：只经 `/api/bugs/*`；任务跳转只到 `/tasks/:id`；不直连数据库、不读 `task_list` 私有模块。
- `gen_arch_stats.py` 的 `TABLE_PREFIX` 登记 `bug_manager: "bug_"`，表名 `bug_tickets`。

## Risks / Trade-offs

- [自动登记漏掉历史任务] → 页面显式同步 + 管理命令；同步幂等，可重复执行。
- [UI 失败用例标题变更导致 source_ref 变化] → 同一任务重复同步可能新增一条；标题来自任务快照，正常不会变；可接受。
- [任务删除后任务链接 404] → BUG 单保留任务标题与编号，抽屉提示「任务已删除」；不级联删除审计记录。
- [BUG 数量增长导致列表变慢] → 列表只取必要字段与预览，详情单独取；`task_id`、`category`、`status` 建索引。
- [同步扫描全量任务耗时] → 当前任务规模小；按用户可见 Agent 过滤，仅扫描相关终态；后续可加分页/游标。
- [状态被自动登记覆盖] → `get_or_create` 的更新字段不含 `status`，并有测试锁定。
- [MySQL 唯一索引长度] → `source_ref` 固定 64 字符、`category` 32 字符，避免长标题进索引。
