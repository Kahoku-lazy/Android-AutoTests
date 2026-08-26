# test_runner App AGENTS.md

> 全局边界 / 协议要点 / 关单清单 → `../AGENTS.md`；本文只写本 App 增量，冲突以全局为准。
> 版本：v1.0 · 最后更新：2026-08-21 · v1.0：从已归档 `dev_docs/_archive/后端claude笔记.md` §0️⃣ 模块表迁出并展开；登记 WS 事件表（10 种）与信封特例。

## 红线（全局索引表 test_runner 行的展开）

| 只做 | 禁止 |
|------|------|
| 任务看板 CRUD、队列、执行（`runner.py` / `remote_runner.py`）、进度推送 | 管理用例定义（写 `cm_` 表走 case_manager api；只读定义可 Model） |
| 执行状态以 `state_machine.py` 权威 state 为准 | 视图/consumer 自行推导状态（前端已删推导，后端是唯一真相源） |

- **状态机勿绕过**：任何状态迁移走 `state_machine.py`；`recovery_helpers.py` 只做恢复辅助，不得另起一套状态口径。改状态字面量必须同步前端 `constants.ts`（`TASK_STATUS`: idle/running/queued/done；`TASK_OUTCOME`: completed/stopped/interrupted/error）。
- 设备占用/释放必须经 `device_pool` 的 api（防火墙 #2），禁止本 App 直接 ORM 改设备状态。
- `executors/`（api/ui/web 三适配器）与 `views/` 拆分已定；执行器改动无测试保护禁止大搬家。

## 本 App 契约（特例 + 真相源）

真相源：`apps/test_runner/urls.py`（13 端点：`run` / `active` / `queue/cancel` / `run/{id}/stop` / `run/{id}/status` / `runs` / `run-step` / `tasks` / `tasks/save` / `tasks/{id}` / `monitor/{id}` / `run/{id}/snapshot` / `step-screenshots/*`）+ `views/` + `api.py`。

- **预留端点**：`monitor/{id}` / `run/{id}/snapshot` / `run/{id}/status` / `runs` 为 TREP v1.0 Phase 0 预留（2026-08-21 校验确认前端暂未消费），保留路由；前端新增消费时同步本文与前端 `test-runner/AGENTS.md`。

**信封特例（legacy 平铺，禁止新增/改造，已登记 ARCH-06）**：

- `/runner/*` 响应为**平铺** `{status, runs|tasks|active, ...}`（非全局 `{status, data}`）。
- `GET /tasks` 列表字段 **camelCase**（全平台唯一），前端 `taskUtils` 按 camelCase 读取。
- 队列取消 `/runner/queue/cancel` body 为 **snake_case**：`client_task_id` / `device_serial`。

## 本 App 协议要点

**WS（本 App 专属，全项目仅 2 个 WS 生产点之一）**：`/ws/test-run/{run_id}`

- 事件真相源 `callbacks.py`，**10 种 type 一个不能漏**：`log` / `heartbeat` / `case_started` / `step_started` / `step_result` / `iteration_result` / `case_finished` / `run_finished` / `device_error` / `run_started`（前端暂不消费 `run_started`，仍须推送）。
- `heartbeat` 每 5s；前端 15s 无心跳判连接丢失——改间隔必须双边同步。
- 新增/改事件 type 必须同步全局 `../AGENTS.md` §2 + 前端 `test-runner/AGENTS.md` + `.agents/skills/android-autotests-rules/references/frontend.md` + skill `vue-frontend-check`（双边契约）。
- 消费者只推送；写库仍走 `api.py`。

## 关单附加项（全局清单的 delta）

```
[ ] WS 10 种事件 type 覆盖无漏；heartbeat 5s 行为不变
[ ] 状态/结局字面量与前端 constants.ts 一致（无新魔法字符串）
[ ] 设备锁经 device_pool api；--check-boundaries 通过
[ ] 信封保持平铺、tasks 列表保持 camelCase（未收敛前不改）
```
