## Why

任务清单里的错误目前只留在每条任务的 `result`、报告事件或验收意见里：UI 自动化失败和测试用例编写未通过混在同一个任务列表，既不能按类别集中查看，也无法登记处理状态或从 BUG 反查任务。平台需要一个独立的 BUG 单台账，把两类问题分开并保留任务追溯。

## What Changes

- 新增 `bug_manager` 后端 App 与 `BugTicket` 表：记录 BUG 编号（由主键派生）、分类、标题、错误正文、处理状态、任务编号/标题/类型快照、Agent 与创建人。
- 分类固定为两类：`ui_automation`（UI 自动化）与 `case_authoring`（测试用例编写），由任务 `task_kind` 映射，不允许混写。
- 任务进入 `failed` / `interrupted` 时自动登记；用例编写任务即使状态为 `completed`，只要 `case_import.status=failed` 也登记入库问题。
- UI 自动化任务按 `result.failed` 的失败用例逐条登记（一条失败用例一张 BUG 单）；没有失败用例明细时退化为一条任务级 BUG。用例编写任务按任务级/入库级各登记一张。
- 自动登记必须幂等：同一任务、同一分类、同一来源键重复同步不新增记录；用户已改的处理状态不被覆盖。
- 提供只读列表/详情、处理状态更新、历史任务同步接口；列表按当前用户可见 Agent 隔离。
- 侧栏「AI任务」分组新增「BUG单管理」入口 `/bugs`；页面提供分类筛选、状态筛选、关键字检索、统计卡、表格与详情抽屉，任务编号可跳转 `/tasks/:id`。
- 新增历史同步命令/接口，用于把平台已有的失败任务补录到 BUG 台账。

## 关联文档

无关联需求编号：本次由用户口头需求驱动（任务错误集中登记、UI 自动化与用例编写分类、关联任务 ID）。

## Capabilities

### New Capabilities

- `bug-ticket-management`: 任务错误到 BUG 单的分类、登记、幂等、状态流转、任务追溯、可见性与同步。

### Modified Capabilities

- `frontend-sidebar-nav`: 「AI任务」分组新增「BUG单管理」入口，并保持现有分组顺序与模块色。

## Impact

- 后端新增 `backend/apps/bug_manager/`（模型、提取器、API、序列化、视图、URL、迁移、同步命令），注册到 `INSTALLED_APPS`、`backend/config/urls.py`、OpenAPI 标签与表前缀统计。
- `task_list`：`finalize_task` 与启动恢复写入终态后调用 BUG 登记；加入跨 App 只写 `bug_manager.api` 的调用，失败不影响任务状态。
- 前端新增 `frontend/src/modules/bug-manager/`（列表页、详情抽屉、API、常量、类型），`router.ts` 汇总路由，侧栏配置与图标子集补入口。
- 测试：提取规则单测、登记/幂等/可见性/状态更新集成测、`/api/bugs/*` 接口测试、前端常量与导航测试。
