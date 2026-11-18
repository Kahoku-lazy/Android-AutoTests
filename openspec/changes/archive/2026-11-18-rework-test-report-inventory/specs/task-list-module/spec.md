# Delta: task-list-module

## REMOVED Requirements

### Requirement: Task detail report moves to the task list

**Reason**: 任务详情报告端点 `GET /api/tasks/{id}/report/` 与前端 `/tasks/:id` 已随 retire-engines-agents 下线（本需求原文未同步）；「测试报告列表行点击进 `/tasks/:id`」的条款与报告台账新语义冲突——报告行改为直接打开已生成的 HTML 报告。
**Migration**: 任务卡「报告」按钮与报告台账行均按 `report-ai-task-list` 的「Report row opens the generated report」打开报告；`/api/reports/task/{id}` 与 `/reports/task/:id` 继续保持 404。
