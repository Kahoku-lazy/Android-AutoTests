## 1. 后端字段与提交契约

- [x] 1.1 `AITask` 新增 `case_title = CharField(max_length=255, default="", blank=True)`，生成迁移并应用；验证：`python manage.py makemigrations --check` 无待生成迁移，`sl_log_ports` 等既有表不受影响。
- [x] 1.2 改 `TaskSubmitInputSerializer`：新增 `agent_id`（必填整数）、`case_title`（可选）、`device_serial` 必填；`goal` 改可选、`assistant_route` 保留可选；验证：`python manage.py check` 通过。
- [x] 1.3 改 `TaskSubmitAPIView`：按 `agent_id` 取智能体（不存在 404/400），用 `engine_adapter.sop_role_models` 校验执行/验收模型，缺 `device_serial` 或 YAML 时 400；创建任务时写入 `case_title`；验证：`pytest tests/api/test_task_submit_sop.py -q` 通过。
- [x] 1.4 改 `api.create_task` / `rerun_task` 支持并复制 `case_title`；`serialize_agent_task_row/detail` 下发 `case_title`；验证：`python manage.py check` 通过，详情接口返回该字段。

## 2. 后端执行链

- [x] 2.1 新增 `api.build_sop_run_input(task)`（固定模板、句号结尾），`task_runner` 用它替换 `build_sop_opening` 并透传 `case_title=task.case_title`；删除无调用方的 `build_sop_opening`；验证：`grep -rn "build_sop_opening" apps engines` 无输出。
- [x] 2.2 `run_platform_sop(..., case_title="")` 按标题过滤：空=全部、指定=只跑一条、不存在=可读失败；验证：`pytest tests/engines/agents/test_platform_case_title.py -q` 通过（用 `run_case` 替身断言只收到指定用例）。

## 3. 前端表单

- [x] 3.1 安装 `js-yaml` 与 `@types/js-yaml`；验证：`cd frontend && npm install && npx vite build` 通过。
- [x] 3.2 新增 `helpers/yaml-case-titles.ts`：`parseCaseTitles(text)` 支持单条/列表、只取非空 `title`、返回可读错误；验证：`npx vitest run tests/ai-assistant/p0/yaml-case-titles.spec.ts` 通过。
- [x] 3.3 重写 `useTaskPublish`：状态改为 `title / agent_id / configFile / device_serial / case_title / caseTitles`；`canSubmit` 要求标题、智能体、YAML、设备；提交只带五项；选 YAML/换文件时解析并清空用例；验证：`npx vitest run tests/ai-assistant/p0/useTaskPublish.spec.ts` 通过。
- [x] 3.4 重写 `TaskBoard` 新建任务弹窗：任务标题、智能体（单选、未选置灰）、YAML、设备（必选）、测试指定用例（全部用例+标题）；移除目标/文档控件；验证：`npx vue-tsc --noEmit` 与 `npx vite build` 通过。

## 4. 测试与门禁

- [x] 4.1 新增 `tests/api/test_task_submit_sop.py`：缺 agent_id 400、agent_id 不存在 400、缺设备 400、缺 YAML 400、成功时 `AITask.case_title` 落库；验证：`pytest tests/api/test_task_submit_sop.py -q` 全绿。
- [x] 4.2 新增引擎用例：空 `case_title` 跑全部、指定标题只跑一条、不存在时返回 fail 且 `completed` 为空；验证：`pytest tests/engines/agents/test_platform_case_title.py -q` 全绿。
- [x] 4.3 前端用例：未选智能体不可提交、提交字段只有五项、换 YAML 清空用例、解析失败不生成选项；验证：`npx vitest run tests/ai-assistant` 本次触及文件全绿。
- [x] 4.4 跑定向门禁：后端 `manage.py check` + `makemigrations --check` + `ruff` + 两个 pytest 文件；前端 `vue-tsc` + `lint` + `vite build` + 定向 vitest。验证：退出码均为 0。

## 5. 文档与归档

- [x] 5.1 更新 `frontend/src/modules/ai-assistant/AGENTS.md` 的任务卡片段：五个字段、智能体必选、用例下拉来源、`case_title` 语义。
- [x] 5.2 运行时验证：重启后端，提交一条带 `case_title` 的任务，确认只跑该用例；任务详情 `case_title` 可见；验证：任务状态与日志符合预期。
- [x] 5.3 `openspec validate task-card-sop-params --strict` 通过后归档；验证：`openspec list --specs` 与主规格更新，`git status` 只有预期文件。
