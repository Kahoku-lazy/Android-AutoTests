## 1. 工作流进入设备槽

- [x] 1.1 工作流提交改为必选设备并调用 `dispatch_device()`，删除 `dispatch_assistant_sop()`。验证：`python -m pytest -c tests/pytest.ini tests/task/unit/test_assistant_sop.py -q` 覆盖空设备 400 且不建任务。
- [x] 1.2 同地址第二条保持 pending，不同地址可同时 running，前序终态后拉起最早 pending。验证：`python -m pytest -c tests/pytest.ini tests/task/unit -q -k "dispatch or assistant_sop"`。
- [x] 1.3 删除带地址的 pending 或 running 任务后补一次 `dispatch_device()`；排空拒绝派发时记录任务编号与地址。验证：同上单测新增删除补派发与排空日志用例通过。

## 2. 任务清单只返回工作流记录

- [x] 2.1 `GET /api/tasks/` 只返回 `assistant_sop`，支持 `workflow_id` 与 `status` 筛选，并返回现存工作流名称。验证：`python -m pytest -c tests/pytest.ini tests/task -q -k "task_list or assistant_sop"`。
- [x] 2.2 提交接口去掉设备执行与用例编写创建分支，保留历史记录的关闭、重跑和清空。验证：对无 `workflow_id` 的提交断言 400，工作流提交断言 200。

## 3. 助手页运行弹窗

- [x] 3.1 去掉「不指定设备」，未选设备或设备列表失败时禁止提交。验证：`cd frontend && npx vitest run tests/ai-assistant`。

## 4. 任务清单表格

- [x] 4.1 删除新建弹窗、平台用例选择器和卡片分组，空态不再提示新建。验证：`cd frontend && npx vitest run tests/task-list`。
- [x] 4.2 用 `AppTable` 按设备管理表纸实现工作流分类、执行状态下拉、5 行分页、表头图标、实线无阴影和行内操作。验证：`cd frontend && npm run lint:styles` 与 `npx vue-tsc --noEmit` 通过。

## 5. 规格与边界

- [x] 5.1 跑 `openspec validate --change queue-workflow-tasks`，确认 delta 可归档。验证：命令退出码为 0。
- [x] 5.2 跑 `python utils/gen_arch_stats.py --check-boundaries`，确认没有新增跨 App 内部 import。验证：命令退出码为 0。
