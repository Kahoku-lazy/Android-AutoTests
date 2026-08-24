# test-runner 模块 CLAUDE.md

> 全局边界 / 模板样式 / 协议要点 / 关单清单 → `../../CLAUDE.md`；本文只写本模块增量，冲突以全局为准。

## 红线（全局表 test-runner 行的展开）

| 只做 | 禁止 |
|------|------|
| 任务看板 / 新建任务 / 防抖保存 / 队列轮询 / WS 进度 / 步骤级结果 | 管理用例定义（那是 case-manager） |
| 报告只读拉取 + 跳转 report-generator | 生成报告文件 / 写业务数据 |

- 跨模块读取（用例定义 / 设备列表）只经本模块 `api.ts` 封装函数，禁止直接 import 其他模块的 api。
- 状态判定走权威字段：前端状态推导已删，`taskUtils` 只读后端 `state` + `running` 本地镜像，**禁止新增推导逻辑**（全局 L4 禁令）。

## 本模块契约（端点有增删必须同改此处）

**信封特例（非全局 `{status, data}`）**：`/runner/*` 响应为**平铺** `{status, runs, queued, ...}`（裸 JsonResponse，前端按平铺读取）；`GET /tasks` 列表内字段 **camelCase**（与平台 snake_case 惯例不同）。已登记 ARCH-06 §4 / PRD-06 §5 章首，禁止在未收敛前改成信封式或 snake_case。

- 执行：`/runner/run` · `/runner/run/{id}/stop` · `/runner/active`
- 任务：`/runner/tasks` · `/runner/tasks/save` · `DELETE /runner/tasks/{id}`
- 队列：`/runner/queue/cancel`，body 为 **snake_case**：`client_task_id` / `device_serial`
- 跨模块只读：`/cases/definitions` · `/cases/{api-testing|web}/definitions` · `/devices`

状态字面量（`constants.ts` 为唯一真相源，禁止散落魔法字符串）：

- `TASK_STATUS`：idle / running / queued / done；`TASK_OUTCOME`：completed / stopped / interrupted / error（`TERMINAL_OUTCOMES` 即终态集合）
- 表单边界：name ≤ 30、loopCount 1~10000、intervalSeconds 5~300（`FORM_BOUNDS`）
- 定时阈值：队列轮询 1500ms、防抖保存 1000ms、日志 500 条截断保留 300（`POLL_INTERVAL` / `SAVE_DEBOUNCE` / `LOG_*`）

## 本模块特殊布局/样式

- 硬编码尺寸只准来自 `constants.ts`（`DIALOG_WIDTH` 520px / `FORM_LABEL_WIDTH` 88px 已收敛于此，禁止新增散落字面量）。

## 本模块协议要点

**WS（本模块专属，全项目仅 2 个 WS 消费点之一）**：

- 连接经 `useTaskWebSocket.ts`，URL 走 `wsUrl('/ws/test-run/{runId}')`（Vite 代理，禁直连端口）；handler 注册表模式解决列表页↔详情页跨页闭包陈旧。
- 事件 type 9 种一个不能漏：`log` / `heartbeat` / `case_started` / `step_started` / `step_result` / `iteration_result` / `case_finished` / `run_finished` / `device_error`（后端另发 `run_started`，前端暂不消费）。
- `runProgress` 结构决定进度条正确性；`applyWsMessage` 是 WS 消息 → task 对象的唯一应用入口，禁止旁路改 task。

## 关单附加项（全局清单的 delta）

```
[ ] WS 9 种事件 type 覆盖无漏；重连 / 序号检测行为不变
[ ] 状态与结局字面量经 constants.ts，无新魔法字符串
[ ] 跨模块读取走 api.ts 封装，无直接 import 其他模块 api
[ ] 队列取消 body 字段 snake_case
```
