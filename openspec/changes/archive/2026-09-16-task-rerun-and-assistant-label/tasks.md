## 1. 后端克隆重跑与助手名

- [x] 1.1 在 `api.py` 增加 `rerun_task(task) -> AITask`：按原任务字段 `create_task`，不改原行；`assistant_name` 写入 `serialize_agent_task_row` / `serialize_agent_task_detail`（线路 name 优先）。pytest 覆盖：原任务仍 failed、新任务 pending 且字段相同；改 agent 线路名后序列化名称变化
- [x] 1.2 `POST /api/ai/agent-tasks/{id}/rerun`：仅失败可重跑，其它状态 400；成功后 `dispatch_device`。权限与删除对齐。`python manage.py check` + `ruff check` 相关路径通过

## 2. 前端卡片

- [x] 2.1 `TaskRecord` 增加 `assistant_name`；失败卡「重新执行」调 rerun 后刷新列表；卡片 meta 增加助手行（当前线路名）。vitest 或组件断言覆盖失败卡有按钮、非失败无按钮、助手文案渲染
- [x] 2.2 同步 `frontend/src/modules/ai-assistant/AGENTS.md` 任务卡字段。`npm run build` 能编过

## 3. 关单

- [x] 3.1 `python manage.py check`、相关 pytest、需要时 `--check-boundaries`
