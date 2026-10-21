## Why

测试报告里 12 条 AI 执行记录中 11 条失败，其中 3 条是服务重启把正在跑的任务直接打断、1 条是旧版本代码在收尾阶段抛 `AttributeError`；这些基础设施问题让“通过率”失真，也让已经跑到第 8/9 步的任务白跑。同一批记录还暴露出执行/验收角色的操作问题：执行者拿不到工具返回的坐标就自己估、误触布局编辑态后不会退出、明知本步未完成仍提交；验收者在没有调用日志工具的情况下判“没有日志”，或要求执行者出示工具无法提供的 base64。两者叠加，使“2 次驳回即整条用例失败”的代价被放大。

## What Changes

- **优雅停机**：`run.py stop` 先停止派发新任务并等待正在跑的任务结束（默认最多 180 秒），超时才强制退出。
- **中断留痕**：非正常退出后启动恢复不再把遗留 running 记为 `failed`，改为新增的 `interrupted` 状态，并回写费用与完成时间；`interrupted` 不计入通过/失败统计。
- **状态贯通**：任务清单、测试报告列表、任务详情、报告筛选 Tab 全部识别 `interrupted`，显示“已中断”。
- **旧代码异常防回归**：为任务收尾用到的状态常量补回归测试，避免再出现 `TaskStatus` 缺成员的 `AttributeError`。
- **执行提示词**：增加“提交前逐条自检、未达成不得声称完成、先执行上一条驳回指令、坐标以工具返回为准、手势后核对、handover 必带 action_time”等硬约束。
- **验收提示词**：增加“判日志结论前必须实际调用检查工具、不得要求工具无法提供的证据、驳回意见必须落在执行者工具集内”等硬约束。

## 关联文档

PRD-平台总需求 §7 观测（任务事件时间线、测试报告）；ARCH-平台架构设计（report_generator / task_list 职责）。

## Capabilities

### New Capabilities

- `task-execution-lifecycle`：服务停机/重启时的任务生命周期——优雅排空、中断状态、恢复口径与前端可见性。
- `role-prompt-guardrails`：执行角色与验收角色系统提示词必须声明的操作与验收约束。

### Modified Capabilities

- `ai-task-device-dispatch`：把“重启后遗留 running 标 failed”改为“标 interrupted 并回写费用”，排队拉起 pending 的行为不变。

## Impact

- 后端：`backend/models/constants.py`、`backend/apps/task_list/{api,views,urls}.py`、`backend/apps/task_list/apps.py`、`backend/gateway/middleware.py`（本地排空端点放行）。
- 运维脚本：`run.py` 的 `stop` 流程。
- 前端：`frontend/src/modules/task-list/{constants.ts,helpers/task-detail.ts}`、`frontend/src/modules/report-generator/{api.ts,constants.ts,index.vue}`、任务详情状态文案。
- 提示词：`engines/agents/prompts/executor_prompt.py`、`engines/agents/prompts/verifier_prompt.py`。
- 测试：`tests/graybox/unit/test_ai_startup_recovery.py` 及新增排空/中断/提示词断言用例。
