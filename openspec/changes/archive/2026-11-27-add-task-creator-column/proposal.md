## Why

任务清单回答不了「这条任务是谁提交的」：`task_tasks.created_by` 其实已经记录了提交人（工作流提交时写入当前登录用户 id），但任务列表接口从不下发、页面也没有这一列。多人共用一套平台（admin / Kahoku 等账号各建各的任务）时，看板上只能看到「创建时间」，无法追责、也无法按人排查。

## What Changes

- 任务清单 `/tasks` 表格新增「创建人」列，显示提交该任务的**账号名**（如 admin、Kahoku）；账号已注销或解析不到时显示「—」。
- `GET /api/tasks/` 的任务行新增两个只读字段：`created_by`（提交人用户 id，原样下发）与 `created_by_name`（解析后的账号名，解析不到为空串）。
- 创建人在**读取时**解析，不落库、不做数据迁移：历史任务只要 `created_by` 有值即同样显示账号名；该字段出现之前的老任务 `created_by` 为空，显示「—」。
- 重跑任务沿用原任务的提交人（既有 `rerun_task` 已复制 `created_by`），本变更不改该口径。
- **BREAKING**：无。列表行只新增两个字段，信封、路由、任务表结构均不变。

## 关联文档

- 需求来源：需求方直接提出（2026-11-27，「任务详情没有创建人，通过工作流创建的任务不知道是哪位用户发出的」）。
- `PRD-平台总需求`：AI 任务「按智能体下发、指定设备与用例、重跑、取消」与「可观测」场景；账号体系复用 Django 内置用户表。
- 相关既有规格：`ai-task-list`（任务清单行内容与操作）。

## Capabilities

### New Capabilities

<!-- 无新增能力：本次只在既有任务清单行上补一个展示字段。 -->

### Modified Capabilities

- `ai-task-list`: 新增「任务行展示创建人」要求——行内展示提交人账号名，解析不到时显示「—」，且不得因解析失败让该行报错。

## Impact

- **后端**：`backend/apps/task_list/api.py`（列表行序列化、`TASK_LIST_FIELDS` 白名单）、`backend/apps/task_list/views.py`（列表查询批量解析账号名，一次查询不按行逐个查）、`backend/shared/users.py`（新增按 id 批量取账号名的通用能力）。
- **接口**：`GET /api/tasks/` 的行新增 `created_by` / `created_by_name`；无数据库迁移，信封不变。
- **前端**：`frontend/src/modules/task-list/components/TaskBoard.vue`（新增「创建人」列与单元格）、`frontend/src/shared/types/ai.ts`（`TaskRecord` 补两个可选字段）。
- **测试**：`tests/task/api/` 新增一条灰盒用例（登录 → 提交工作流任务 → 列表行带账号名 → ORM 读回 `created_by`）；`frontend/tests/task-list/` 补该列的展示断言。
- **文档**：`.agents/docs/apps/task_list/task_list_task_lifecycle.md`、`.agents/docs/frontend/task_list/task_list_task_board_page.md` 补创建人列口径。
