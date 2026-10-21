## 1. 后端：中断状态与启动恢复

- [x] 1.1 `backend/models/constants.py` 的 `TaskStatus` 增加 `INTERRUPTED = "interrupted"`，并在 `task_runner` 收尾状态映射旁补回归断言所需常量；`python -m pytest -c tests/pytest.ini tests/graybox/unit -k task_status` 通过
- [x] 1.2 `backend/apps/task_list/api.py` 新增 `begin_drain()` / `is_draining()` / `count_running_tasks()`（进程内标志，不进库），并让 `dispatch_device()` 在排空期间不再领取新任务；单测覆盖“排空中提交仍为 pending”
- [x] 1.3 改写 `recover_orphaned_tasks()`：逐条 running 先 `rollup_task_cost()`，再写 `status=interrupted`、`result`、`finished_at`；保持 pending 派发；`python -m pytest -c tests/pytest.ini tests/graybox/unit/test_ai_startup_recovery.py` 通过（含费用回写断言）
- [x] 1.4 `backend/apps/task_list/apps.py` 的恢复日志文案改为 “→ interrupted”；`inspect.getsource` 静态断言仍通过

## 2. 停机排空端点与 run.py

- [x] 2.1 新增 `GET/POST /api/system/drain/` 视图：GET 返回 `{status,data:{running,draining}}`，POST 置排空并返回同一结构；非回环来源返回 403；接口进 OpenAPI
- [x] 2.2 `backend/gateway/middleware.py` 只对“精确路径 `/api/system/drain/` 且回环地址”跳过 JWT；其余 `/api/` 规则不变；单测覆盖回环放行与非回环 401
- [x] 2.3 `run.py stop_backend()` 改为：POST 置排空 → 每 2 秒轮询 GET → running 归零后停止进程；180 秒超时强制停止（超时可用环境变量覆盖）；无任务时立即返回；`python run.py status` 仍正常

## 3. 前端：已中断状态贯通

- [x] 3.1 `frontend/src/modules/task-list/constants.ts` 增加 `interrupted` 标签与分组映射，`helpers/task-detail.ts` 的 `TERMINAL_STATUSES` 纳入 `interrupted`；`npm run typecheck` 通过
- [x] 3.2 `frontend/src/modules/report-generator/{api.ts,constants.ts}` 双口径 `STATUS_LABEL_MAP` 增加 `interrupted: "已中断"`，`index.vue` 增加“已中断”筛选项与徽章样式；`npm run typecheck` 通过
- [x] 3.3 `TaskDetailPage.vue` 的状态文案把 `interrupted` 显示为“已中断”，不再落“已完成”；`npm run typecheck` 通过

## 4. 提示词：执行与验收纪律

- [x] 4.1 `engines/agents/prompts/executor_prompt.py` 增加六条硬约束（逐条核对、未达成不声称完成、先执行驳回指令、坐标以工具返回为准、手势后复核、handover 带 action_time），并替换“没做完写出来即可提交”的表述
- [x] 4.2 `engines/agents/prompts/verifier_prompt.py` 增加三条硬约束（先调检查工具再判、不得要求 base64/文件路径、驳回意见必须可在执行者工具集内执行）
- [x] 4.3 新增 `tests/graybox/unit/test_role_prompt_guardrails.py`：断言两份提示词分别包含上述条款、且不含“要求 base64”类措辞；`python -m pytest -c tests/pytest.ini tests/graybox/unit/test_role_prompt_guardrails.py` 通过

## 5. 门禁与验收

- [x] 5.1 新增 `tests/graybox/unit/test_task_status_symbols.py`：`TaskStatus` 覆盖 `task_runner` 收尾映射与恢复用到的全部成员；pytest 通过
- [x] 5.2 门禁：`python run.py check` 22/22 阻塞项通过（含 django-check、ruff、boundary、vite-build、vitest、vue-tsc）；全量 `unit or integration` 44 项失败经 `git worktree` 对拍确认为 HEAD 基线遗留，本变更新增失败 0
- [x] 5.3 运行期冒烟（重启加载新代码后实测）：`GET /api/system/drain/` → `{running:0,draining:false}`；`POST` → `{draining:true}`；再 `GET` 仍为 true；`GET /api/tasks/` 无 JWT 仍 401；再次重启后 `draining:false`（标志进程内，不跨重启）

## 验收备注

- 真机长任务验收（提交长任务 → `python run.py stop` 观察到等待 → 重启后 completed；强制 kill 后启动显示 `interrupted` 且报告不计失败）需连设备跑真任务，留给使用方在真机环境执行；代码路径已由 `test_task_drain.py` / `test_ai_startup_recovery.py` 覆盖。
