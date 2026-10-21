## Context

See proposal.md - Why. 当前实现的两个约束决定了方案：

1. 任务由 `dispatch_device()` 在进程内起 daemon 线程执行，进程退出即线程消失，没有可恢复的检查点；因此“停机不打断”只能靠**退出前把任务跑完**，不能靠断点续跑。
2. 任务状态是 `task_tasks.status` 的自由字符串（无 choices、无迁移），新增状态只影响读取方与前端映射，不需要改表结构。

## Goals / Non-Goals

**Goals:**

- `python run.py stop` 在 180 秒内等待在跑任务自然结束；期间不再派发新任务。
- 非正常退出遗留的 `running` 落 `interrupted`，带中断说明、`finished_at` 与已发生费用，不污染通过率。
- 前端与测试报告统一识别“已中断”，并提供独立筛选。
- 执行/验收提示词把这次复盘出的可避免失败写成硬约束。
- 锁住收尾状态常量的完整性，避免旧代码式 `AttributeError` 再出现。

**Non-Goals:**

- 不做任务断点续跑或暂停恢复。
- 不自动重跑被中断的任务（由用户手动“重跑”）。
- 不改 `MAX_ATTEMPTS=2` 与“一步失败即整条用例终止”的现有策略。
- 不改日志关键词表、不改用例 YAML、不改验收判据（不在本次范围）。

## Decisions

### 1. 停机用 HTTP 排空信号，而不是文件标志或信号量

`run.py stop` 通过本机 HTTP 调用后端的新端点：

- `POST /api/system/drain/`：置进程内 `_draining` 标志并返回当前 running 数。
- `GET /api/system/drain/`：只读返回 `{running, draining}`。

`run.py` 置位后每 2 秒轮询一次，running 归零则走原有 `kill_port`；180 秒未归零则强制结束。

备选：
- **磁盘标志文件 + 后台线程轮询**：后端需要常驻轮询线程，进程退出后标志残留，下一次启动要清理，复杂度更高。
- **SIGTERM/SIGINT 处理器**：Windows 下 `taskkill` 不保证把信号投递给无控制台的 Python 进程，实测已回退到强制杀，无法保证。
- **直接改 `MAX_ATTEMPTS` 或强杀**：不解决问题。

放行方式：`gateway/middleware.py` 只对**精确路径 `/api/system/drain/` 且 `REMOTE_ADDR` 为回环地址**跳过 JWT，其余 `/api/` 规则不变；视图内再校验一次回环地址与 `POST` 语义。

### 2. 新增 `TaskStatus.INTERRUPTED`，不复用 `failed`/`cancelled`

- `failed` 表示用例真的没通过；`cancelled` 表示用户主动关闭；重启打断是第三种语义，必须能在报告里区分。
- `status` 是自由字符串，新增枚举值不需要迁移。
- 报告聚合沿用现有口径（`PASS_STATUSES` / `FAIL_STATUSES`），`interrupted` 自然落在两者之外，只计入 `total_runs`；通过率分母仍是 pass+fail。

### 3. 启动恢复顺序：先回写费用，再改状态

对每条遗留 running：先 `rollup_task_cost(task.id)`（复用现有函数），再写 `status=interrupted`、`result`、`finished_at`。这样即使改状态失败，费用也不会丢；反过来先改状态则可能把“仍在跑”的任务误标后继续计费。

`recover_orphaned_tasks()` 仍返回恢复条数，日志文案改为 “→ interrupted”。

### 4. 提示词改动只加“可执行、可核对”的硬约束

执行提示词加六条：提交前逐条核对、未达成不得声称完成、先执行上一条驳回指令、坐标以工具返回为准、手势后复核、handover 必带 action_time。
验收提示词加三条：判无日志前必须实际调用检查工具、不得要求 base64/文件路径、驳回意见必须能在执行者工具集内执行。

不在提示词里塞“如何点某个具体控件”的做法，避免把某台设备的 UI 细节写死。

### 5. 旧代码异常用“符号完整性”回归测试兜底

在 `tests/graybox/unit/` 增加断言：`task_runner` 收尾状态映射用到的 `TaskStatus` 成员全部存在，且 `recover_orphaned_tasks` 使用的 `INTERRUPTED` 已登记。它挡不住“跑了旧进程”，但能挡住再次出现缺成员的提交。

## 模块防火墙自检

- 排空端点放在 `task_list` App 内（任务状态归它所有），不新建 App。
- `run.py` 只走 HTTP，不 import Django、不读 task 表。
- 启动恢复继续只经 `task_list/api.py` 写库，`apps.py` 不直写 ORM（保留现有静态断言）。
- 前端只经 `/api/reports/*` 与 `/api/tasks/*` 读取，不新增跨模块 import。
- 提示词改动只在 `engines/agents/prompts/`，不引入数据库字段。

## Risks / Trade-offs

- [stop 最多等 180 秒，CI/本地操作可能觉得慢] → 无任务时立即返回；等待期间每 10 秒打印一次剩余任务数；提供环境变量覆盖超时。
- [回环地址放行成为本地攻击面] → 只放行单一路径、只允许 GET/POST、视图内二次校验回环，且该端点不返回任务内容。
- [前端旧版本不认识 interrupted，会显示原始字符串] → 本次前后端一起发布；后端先上线不会破坏旧页面（只是标签未翻译）。
- [提示词变长可能拉长单次尝试] → 不放开 `MAX_ATTEMPTS`；提示词只写判定纪律，不写探索性指令。
- [强制超时退出仍会打断任务] → 这正是“中断留痕”要覆盖的兜底路径，两者互补。

## Migration Plan

1. 后端先发布（新状态与恢复逻辑）；旧前端把 `interrupted` 原样显示，不影响使用。
2. 前端随后发布标签、筛选与终态判断。
3. 回滚：把 `TaskStatus.INTERRUPTED` 的读取方回退即可；已落库的 `interrupted` 行可手工改回 `failed`，不涉及表结构。
4. 不改任何数据迁移，无需 `migrate`。

## Open Questions

无。
