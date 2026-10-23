## Context

`build_task_flow` 现在用 `TaskEvent.objects.filter(task_id=...).order_by("seq")` 取整行 ORM 实例，再交给 `_grouped` / `_rounds` / `_flow_cases` 做纯内存聚合。实测（任务 141，147,850 条事件）：取数 11.78 秒，`_grouped` 0.29 秒、`_rounds` 0.02 秒、`_flow_cases` 0.13 秒；其中 139,948 条是 `ToolCallDeltaEvent`，`_detail` 对增量类型一律返回空串，聚合只用它们的 `is_delta` / `event_type` / `step_seq` / `attempt` / `phase`。

开发代理侧，Vite 的 `proxy.on("error")` 在连接失败时 `res.writeHead(500).end()`（空 body），axios 只能显示 `Request failed with status code 500`。

## Goals / Non-Goals

**Goals:**

- 报告接口服务端耗时从 10 秒级降到 4 秒内（实测约 3.3 秒），响应契约与输出逐字段不变。
- 代理连接失败与后端业务 5xx 在浏览器侧可区分。

**Non-Goals:**

- 不引入报告缓存、不做分页/懒加载、不改前端页面组件。
- 不改事件写入路径与 `task_events` 表结构，也不清理历史增量事件。
- 不改 WebSocket 代理行为。

## Decisions

**1. 分两段取数：先取分组列，再补代表行。**

主查询用 `.values_list()` 只取分组需要的 5 列（`seq` / `event_type` / `is_delta` / `step_seq` / `attempt`），147,850 行实测 1.7~2.1 秒；用 `_spans` 切出 9,602 段后，只对每段的第一行回查展示与明细字段（9,602 行，0.5~0.9 秒）。阶段列（`phase`）也只在代表行上取——`_grouped` 只用每组第一行的阶段。

备选：整行 ORM 实测 11.06 秒，否决；`.only()` / `.defer("payload")` 仍是模型实例，访问被 defer 的字段会逐行回查（数千次 N+1），否决；用 SQL 窗口函数把增量段折叠成 9,602 行，理论上还能把主查询降到 0.3 秒，但要窗口子查询 + 分组，Django/MySQL 组合复杂且容易与 `_grouped` 的合并语义漂移，本次不做，留作事件量继续增长时的后续优化。

**2. 增量的 payload 在库内就置空。**

回查时用 `Case(When(is_delta=False, then=F("payload")), default=None)` 投影出 `report_payload`，增量行的 payload 不会被读入进程；非增量行的 `payload` 与数值字段随这 9,602 行一起返回。`started_at` / `ended_at` / `called_at` 用 `Coalesce` 在库里折成一个 `moment`，少传两列日期。

约束：`_detail` 只对非增量类型取 `payload`；若将来新增需要明细的增量事件类型，必须把该类型从 CASE 的置空范围里排除，否则明细为空。

**3. 代理在 `configure(proxy)` 里抢先注册 error 监听。**

`configure` 在 Vite 注册内建 error 处理器之前被调用，因此我们的监听先执行：连接失败时写 `503` + `{status:false,message:"后端服务未就绪，请稍后重试"}`。Vite 内建处理器随后运行，看到 `headersSent || writableEnded` 就不再写 500，只打印一条 `http proxy error` 日志。

守护：`res` 必须是 `ServerResponse`（`typeof res.writeHead === "function"`）且未开始写出；WS 升级失败时 `res` 是 socket，直接跳过，保持原行为。后端自身的 5xx 不经过 error 事件，天然原样透传。

备选：在前端 axios 层做重试与文案映射（用户本轮未选，留待后续）；把代理换成 nginx（开发环境不适用）。

## 模块防火墙自检

- 只改 `backend/apps/task_list/task_reports.py` 与 `frontend/vite.config.js`，无新增跨 App import，无写库。
- `task_reports.py` 继续只读 `TaskEvent` / `Task` / `TaskAttachment`，不碰 `ai_assistant` 的内部实现。
- 配置层不引入前端业务依赖，代理只处理传输层错误。

## Risks / Trade-offs

- [新增增量类型且需要 payload 明细] → 在 `_load_details` 的 CASE 条件与 `_spans` 合并规则上同步修改，并在测试中覆盖。
- [两段取数漏掉某个字段] → 行对象字段与两段查询列一一对应；`tests/api/test_task_event_flow.py` 逐字段断言，另有变更前后输出对比（任务 139 / 141 完全一致）。
- [代理 503 被前端误当业务错误] → 页面 `ErrorState` 直接显示 `message`，文案已说明"后端服务未就绪"。
- [Vite 内建处理器仍打印错误日志] → 保留，便于定位；不影响响应。
