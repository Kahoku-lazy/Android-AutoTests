## Why

Agent-02 已经把用例写进 `Task.result.document`，但这份结果只停留在任务报告里：不能编辑、不能筛选、不能被执行侧消费，任务一多就变成一堆无法复用的 Markdown。平台已有完整的用例管理模型（项目 → 目录 → 文件 → 单条用例 + 步骤），需要把验收通过的用例直接落进去。

## What Changes

- 新增「Agent-02 结果写入用例库」：任务终态且验收通过后，把 `Task.result.document` 的每条用例解析成 `TestDefinition`，每个步骤解析成 `CaseStep`，写入当前用户固定的「AI 生成用例」项目；一个任务对应一个用例文件，模块名写入 `module` 字段。
- 写入必须幂等：同一任务重复导入不产生重复用例；重复导入时复用已存在的文件并跳过已导入结果。
- 写入归属必须是任务发起人，不是 Agent-02 的 owner；`Task` 增加创建人快照，提交任务时写入，重跑时继承。
- 用例行保留来源追溯：新增 `source_case_id`（源文档用例编号）与 `source_task_id`（来源任务），不占用平台 `TC-YYYYMMDD-NNNN` 编号。
- 报告页不再渲染「生成的测试用例」Markdown；只保留任务摘要、模型事件流与验收意见，并给出一个可点击的用例管理地址（`/cases/projects/:projectId/files/:fileId`）。**BREAKING**：报告响应不再把完整 `document` 下发给前端。
- 写入失败不得把任务判失败：任务仍按验收结果完成，结果里记录导入状态与原因，报告给出可读提示。

## 关联文档

无关联需求编号：本次由用户口头需求驱动（Agent-02 结果入库 + 报告跳转用例管理）。

## Capabilities

### New Capabilities

- `case-manager-ai-import`: Agent-02 验收结果写入用例管理的映射、归属、幂等、来源追溯与失败降级。

### Modified Capabilities

- `appliance-case-authoring-task`: 任务创建人快照；验收通过后写入用例库；报告从「展示完整 Markdown」改为「事件流 + 用例管理地址」。

## Impact

- 后端 `task_list`：`Task.created_by` 迁移；提交/重跑写入；`task_runner` 在终态前调用导入；`task_reports` 返回 `case_import` 并停止下发 `document`。
- 后端 `case_manager`：新增导入服务与 `api.py` 出口；`TestDefinition` 增加 `source_case_id` / `source_task_id` 与迁移；序列化补充来源字段。
- 引擎 `workflow/case_document_check.py`：解析模块名、步骤/预期按 `<br>` 拆分，供导入复用。
- 前端 `task-list`：删除 Markdown 文档区，新增结果地址卡；`case-manager` 类型补来源字段（只读）。
- 测试：导入映射/幂等/归属、报告契约、前端报告页；OpenSpec `appliance-case-authoring-task` delta。
