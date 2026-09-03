# API-执行引擎 — /api/runner/*

> 执行引擎（`apps/test_runner`）REST 接口全集：**13 个端点** + 1 条 WS 通道。
> 真相源：`apps/test_runner/urls.py` + `views/*` + `api.py` + `models.py` + `callbacks.py` + `gateway/routing.py`。
> 路径无尾斜杠，统一挂载前缀 `/api/runner/`（见 `config/urls.py`）。

## 1. 总览

| 接口 | 方法 | 鉴权 | 说明 |
|---|---|---|---|
| 启动测试运行接口 | POST /api/runner/run | 需登录(Bearer) | 启动一次测试执行（多设备 + 队列 + 定时计划） |
| 取消排队任务接口 | POST /api/runner/queue/cancel | 需登录(Bearer) | 从设备队列移除排队任务（body 为 snake_case） |
| 停止运行接口 | POST /api/runner/run/{run_id}/stop | 需登录(Bearer) | 优雅停止 / 预检阶段停止 |
| 活跃运行列表接口 | GET /api/runner/active | 需登录(Bearer) | 当前活跃运行（含懒恢复） |
| 运行状态接口 | GET /api/runner/run/{run_id}/status | 需登录(Bearer) | 单次运行状态（**预留，前端暂未消费**） |
| 运行历史列表接口 | GET /api/runner/runs | 需登录(Bearer) | 运行历史列表（**预留，前端暂未消费**） |
| 单步调试接口 | POST /api/runner/run-step | 需登录(Bearer) | 在当前调试设备上单步执行一步 |
| 任务卡片列表接口 | GET /api/runner/tasks | 需登录(Bearer) | 任务卡片列表（列表字段 camelCase，全平台唯一） |
| 保存任务卡片接口 | POST /api/runner/tasks/save | 需登录(Bearer) | 任务卡片 upsert（body 为 camelCase） |
| 删除任务卡片接口 | DELETE /api/runner/tasks/{task_id} | 需登录(Bearer) | 删除任务卡片 |
| 运行监控接口 | GET /api/runner/monitor/{run_id} | 需登录(Bearer) | 协议健康监控（**预留，前端暂未消费**） |
| 运行快照接口 | GET /api/runner/run/{run_id}/snapshot | 需登录(Bearer) | 状态快照，WS 降级兜底（**预留，前端暂未消费**） |
| 步骤截图接口 | GET /api/runner/step-screenshots/{filepath} | 公开 | 步骤标注截图（走 FileResponse，非 JSON） |

> 预留端点说明（`apps/test_runner/AGENTS.md`）：`monitor/{run_id}`、`run/{run_id}/snapshot`、`run/{run_id}/status`、`runs` 为 TREP v1.0 Phase 0 预留，2026-08-21 校验确认前端暂未消费；路由保留，前端新增消费时须双边同步契约。

## 2. 通用约定

- **路径无尾斜杠**（`urls.py` 用 `path("run", ...)` 无斜杠形式注册）。
- **legacy 平铺信封**（已登记 ARCH-06，禁止新增/改造，未收敛前禁止改成信封式）：`/runner/*` 响应为**平铺** `{status, runs|tasks|active, ...}`，**不是**全局 `{status, data}`。
- **`GET /tasks` 列表字段 camelCase**（全平台唯一），前端 `taskUtils` 按 camelCase 读取；其余响应字段以 snake_case 为主（个别内嵌字典为 camelCase，按实际字段列出）。
- **`POST /queue/cancel` 请求体为 snake_case**：`client_task_id` / `device_serial`（区别于本模块其它 camelCase 入参）。
- 需登录端点携带 `Authorization: Bearer <access_token>`。鉴权在**网关中间件** `JWTAuthenticationMiddleware` 统一执行（`/api/*` 除公开路径外一律校验）；多数视图另加 `@require_auth` 作第二层校验。
- 公开路径仅 `step-screenshots`（因 `<img src>` 无法携带 Authorization 头，已登记 `PUBLIC_PREFIXES`）。
- **HTTP 状态码注意**：部分校验失败在代码中 `JsonResponse` 未显式设状态码，默认返回 **200** 但 body 为 `status: false`。前端应以 `status` 字段为准，勿仅凭 HTTP 码判断成败。
- 状态枚举（真相源 `models/test_models.py`）：
  - run 态 `TestRunStatus`：`pending` / `running` / `completed` / `stopped` / `failed`
  - 任务卡态 `TaskCardStatus`：`idle` / `queued` / `running` / `done`
  - 任务卡结局 `TaskOutcome`：`completed` / `stopped` / `interrupted` / `error`（空串 = 未终态）
  - `task_type`：`ui_automation` / `api_testing` / `web_automation`；`mode`：`immediate` / `scheduled`

### 2.1 鉴权失败（全模块通用）

| HTTP | message | 触发条件 |
|---|---|---|
| 401 | 请先登录 | 无 Authorization 头或非 Bearer（网关中间件） |
| 401 | 登录已过期或令牌无效 | token 校验失败（网关中间件） |
| 401 | 未登录或 token 已过期 | `request.user_id` 为空（`@require_auth` 装饰器第二层） |

---

## 3. 执行启动

### 3.1 启动测试运行接口：POST /api/runner/run

| 项 | 值 |
|---|---|
| 鉴权 | 需登录(Bearer) |
| Content-Type | application/json |

#### 请求体

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| case_ids | array[string] | 是 | 用例 ID 列表；为空报错 `case_ids required` |
| device_serials | array[string] | 否 | 目标设备序列号列表（多设备）；为空时回退到 `device_serial`，再回退到当前调试设备 |
| device_serial | string | 否 | 单设备序列号（`device_serials` 为空时的回退项） |
| loop_count | integer | 否 | 循环轮数，默认 3 |
| interval_seconds | integer | 否 | 轮间间隔秒，默认 5，最小 5（`max(5, ...)`） |
| package_name | string | 否 | 目标 App 包名，默认取用例自身声明的包名 |
| start_at | string | 否 | 计划开始时间（ISO 字符串），缺省立即执行 |
| end_at | string | 否 | 计划结束时间（ISO 字符串），到达后自动停止 |
| client_task_id | string | 否 | 前端任务卡片 ID（localStorage / 任务卡主键），用于关联任务卡状态机 |
| task_type | string | 否 | 执行类型：`ui_automation`（默认）/ `api_testing` / `web_automation` |

#### 成功响应（200，UI 自动化路径）

```json
{
  "status": true,                      # 请求是否成功，恒为 true
  "runs": [                            # 立即启动的运行列表
    {
      "run_id": "run_AB123_20260821_153000",  # 运行 ID（格式 run_{serial}_{时间戳}）
      "serial": "AB123"                # 设备序列号
    }
  ],
  "queued": ["CD456"],                 # 因设备忙被排队的设备序列号列表
  "case_count": 3,                     # 本次执行用例数
  "loop_count": 3,                     # 循环轮数
  "parallel": 1                        # 立即并发的运行数（len(runs)）
}
```

#### 成功响应（API / Web 路径，无设备，200）

```json
{
  "status": true,
  "runs": [
    {
      "run_id": "API-RUN-20260821153000-xxxxxxxx",  # 运行 ID（格式 {API|WEB}-RUN-{时间戳}-{client_task_id 前 8 位或 direct}）
      "test_cases": 3                  # 用例数
    }
  ],
  "queued": [],                        # API/Web 无设备队列，恒为空
  "case_count": 3,
  "loop_count": 3
}
```

#### 错误码与文案（校验顺序即优先级）

| HTTP | message | 触发条件 |
|---|---|---|
| 200 | case_ids required | `case_ids` 为空（未显式设状态码） |
| 400 | device_serial is required for UI automation tasks | `task_type=ui_automation` 且无设备序列号 |
| 200 | no enabled test cases found | 按 `case_ids` 查无启用用例（未显式设状态码） |
| 400 | 没有可用设备，请确认设备已连接且状态为在线 | 全部目标设备均不在线/已占用且无排队成功 |

> 设备忙或在线被占时**不报错**，而是把该任务入队并计入 `queued`；仅当「无立即运行且无排队」时才返回 400。

---

### 3.2 取消排队任务接口：POST /api/runner/queue/cancel

| 项 | 值 |
|---|---|
| 鉴权 | 需登录(Bearer) |
| Content-Type | application/json |

#### 请求体（**snake_case**，全平台特例）

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| client_task_id | string | 是 | 排队任务的任务卡 ID |
| device_serial | string | 是 | 设备序列号 |

#### 成功响应（200）

```json
{
  "status": true,                       # 请求是否成功
  "message": "已取消排队任务（3 个用例）"  # 已从内存队列移除，数字为取消任务的用例数
}
```

> 兜底路径（服务重启后内存队列丢失、任务仍以 `queued` 状态落库时）：返回 `message` 为 `已从数据库中取消排队任务`。

#### 错误码与文案

| HTTP | message | 触发条件 |
|---|---|---|
| 400 | 需要提供 client_task_id 和 device_serial | 任一必填字段为空 |
| 404 | 未找到该排队任务，可能已经开始执行 | 内存队列与 DB 均未找到对应 queued 任务 |

---

### 3.3 停止运行接口：POST /api/runner/run/{run_id}/stop

| 项 | 值 |
|---|---|
| 鉴权 | 需登录(Bearer) |
| 路径参数 | `run_id`（string，运行 ID） |

#### 请求

无请求体。

#### 成功响应（200）

```json
{
  "status": true,              # 请求是否成功
  "message": "stop requested"  # 活跃运行：打停止标记，执行循环到检查点自然收尾
}
```

> 预检阶段（已锁设备但尚未真正执行）：返回 `"message": "stopping (pre-flight)"`，延迟执行在检查点释放设备并标记停止，避免设备锁泄漏。

#### 错误码与文案

| HTTP | message | 触发条件 |
|---|---|---|
| 200 | run not found or already finished | 运行不存在或已结束（未显式设状态码） |

---

## 4. 运行查询

### 4.1 活跃运行列表接口：GET /api/runner/active

| 项 | 值 |
|---|---|
| 鉴权 | 需登录(Bearer) |

#### 请求

无请求体。触发懒恢复：重建队列、标记孤儿 running 任务、必要时拉起停滞队列。

#### 成功响应（200）

```json
{
  "status": true,                       # 请求是否成功
  "active": [                           # 活跃运行列表（state.is_running 为真）
    {
      "run_id": "run_AB123_20260821_153000",  # 运行 ID
      "status": "running",              # run 态（TestRunStatus）
      "selected_cases": [{"case_id": "TC-1", "title": "登录", "steps_data": []}],  # 用例快照
      "loop_count": 3,                  # 循环轮数
      "started_at": "2026-08-21T15:30:00",  # 开始时间
      "device_serial": "AB123",         # 设备序列号
      "client_task_id": "task-abc"      # 关联任务卡 ID（可能为空串）
    }
  ]
}
```

---

### 4.2 运行状态接口：GET /api/runner/run/{run_id}/status

> **预留端点**，前端暂未消费。

| 项 | 值 |
|---|---|
| 鉴权 | 需登录(Bearer)（仅网关中间件层，视图未加 `@require_auth`） |
| 路径参数 | `run_id`（string，运行 ID） |

#### 请求

无请求体。

#### 成功响应 — 活跃运行（200）

```json
{
  "status": true,                       # 请求是否成功
  "run_id": "run_AB123_20260821_153000",
  "status": "running",                  # run 态（TestRunStatus）
  "is_running": true,                   # 是否运行中
  "selected_cases": [{"case_id": "TC-1", "title": "登录", "steps_data": []}],
  "loop_count": 3,
  "started_at": "2026-08-21T15:30:00"
}
```

#### 成功响应 — 已完成运行（从 DB，200）

```json
{
  "status": true,
  "run_id": "run_AB123_20260821_153000",
  "status": "completed",                # run 态（DB 原始值）
  "total_iterations": 9,                # 结果总条数（= TestResult 行数）
  "passed": 8,                          # 通过条数（result=pass）
  "selected_cases": [{"case_id": "TC-1", "title": "登录", "steps_data": []}],
  "loop_count": 3,
  "started_at": "2026-08-21T15:30:00"
}
```

#### 错误码与文案

| HTTP | message | 触发条件 |
|---|---|---|
| 404 | run not found | 活跃运行与 DB 均不存在该 run_id |

---

### 4.3 运行历史列表接口：GET /api/runner/runs

> **预留端点**，前端暂未消费。

| 项 | 值 |
|---|---|
| 鉴权 | 需登录(Bearer)（仅网关中间件层，视图未加 `@require_auth`） |

#### 请求

无请求体。

#### 成功响应（200）

```json
{
  "status": true,                       # 请求是否成功
  "runs": [                             # 运行历史，按 id 倒序，最多 50 条
    {
      "run_id": "run_AB123_20260821_153000",  # 运行 ID
      "status": "completed",            # run 态
      "device_serial": "AB123",         # 设备序列号（API/Web 为 "api"/"web"）
      "loop_count": 3,                  # 循环轮数
      "total": 9,                       # 结果总条数
      "passed": 8,                      # 通过条数
      "failed": 1,                      # 失败条数（total - passed）
      "started_at": "2026-08-21T15:30:00",
      "finished_at": "2026-08-21T15:31:20",
      "selected_cases": [{"case_id": "TC-1", "title": "登录", "steps_data": []}]
    }
  ]
}
```

---

## 5. 任务卡片（看板）

### 5.1 任务卡片列表接口：GET /api/runner/tasks

| 项 | 值 |
|---|---|
| 鉴权 | 需登录(Bearer) |

#### 请求

无请求体。执行前先做恢复（`recover_stale_running_taskcards` + 排队终态漂移修复），再按 `-created_at` 取最近 200 条。

#### 成功响应（200）— 列表字段 **camelCase**（全平台唯一）

```json
{
  "status": true,                       # 请求是否成功
  "tasks": [                            # 任务卡片列表
    {
      "id": "task-abc",                 # 任务卡主键（task_id）
      "name": "冒烟测试",                # 任务名
      "mode": "immediate",              # 模式：immediate / scheduled
      "taskType": "ui_automation",      # 执行类型
      "deviceSerial": "AB123",          # 设备序列号
      "caseIds": ["TC-1", "TC-2"],      # 用例 ID 列表
      "loopCount": 3,                   # 循环轮数
      "intervalSeconds": 5,             # 轮间间隔秒
      "running": false,                 # 是否执行中（派生自 status == "running"）
      "runId": "run_AB123_20260821_153000",  # 关联运行 ID（无则为空串）
      "caseItems": [{"id": "TC-1", "title": "登录", "total": 3, "pass": 3, "fail": 0, "rate": 100, "status": "done"}],
      "stepStates": [],                 # 步骤状态
      "overallPass": 8,                 # 累计通过
      "overallFail": 1,                 # 累计失败
      "logs": ["...", "..."],           # 运行日志（最多 200 条）
      "createdAt": "2026-08-21 15:29:00.123456+00:00",  # 创建时间（str 化）
      "creator": "admin",               # 创建人（数字 id 已解析为用户名）
      "currentCaseTitle": "登录",        # 当前执行用例标题
      "currentIteration": 2,            # 当前轮次
      "failedSteps": [],                # 失败步骤
      "status": "done",                 # 任务卡态：idle / queued / running / done
      "outcome": "completed",           # 终态结局：completed / stopped / interrupted / error（空串未终态）
      "state": "done",                  # 权威展示态（state_machine.display_state）
      "round": 1,                       # 轮次
      "conclusion": "通过 8 / 失败 1",   # 结论文案
      "bugTicket": "",                  # 缺陷单
      "startAt": "",                    # 计划开始时间
      "endAt": "",                      # 计划结束时间
      "perfStats": {"count": 10, "max": 1.2, "min": 0.8, "avg": 1.0, "median": 1.0, "per_case": []},  # 性能统计（无数据为 null）
      "step_details": [{"caseId": "TC-1", "caseTitle": "登录", "_date": "2026-08-21 15:30:00"}]  # 步骤明细（含截图路径）
    }
  ]
}
```

> `running` 派生自 `status == "running"`，杜绝 status/running 双源不一致；`state` 为状态判定唯一入口 `state_machine.display_state` 的结果。

---

### 5.2 保存任务卡片接口：POST /api/runner/tasks/save

| 项 | 值 |
|---|---|
| 鉴权 | 需登录(Bearer) |
| Content-Type | application/json |

#### 请求体（**camelCase**，字段即 `api.save_task_card` 的 defaults）

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| id | string | 是 | 任务卡主键（task_id），为空报错 `任务ID不能为空` |
| name | string | 否 | 任务名，默认 "" |
| creator | string | 否 | 创建人（数字 id 会被解析为用户名），默认 "" |
| mode | string | 否 | 模式，默认 "immediate" |
| taskType | string | 否 | 执行类型，默认 "ui_automation" |
| deviceSerial | string | 否 | 设备序列号，默认 "" |
| caseIds | array | 否 | 用例 ID 列表，默认 [] |
| loopCount | integer | 否 | 循环轮数，默认 1 |
| intervalSeconds | integer | 否 | 轮间间隔秒，默认 5 |
| caseItems | array | 否 | 用例条目，默认 [] |
| stepStates | array | 否 | 步骤状态，默认 [] |
| overallPass | integer | 否 | 累计通过，默认 0 |
| overallFail | integer | 否 | 累计失败，默认 0 |
| logs | array | 否 | 日志（截留最近 200 条） |
| outcome | string | 否 | 终态结局，默认 "" |
| round | integer | 否 | 轮次，默认 0 |
| conclusion | string | 否 | 结论，默认 "" |
| bugTicket | string | 否 | 缺陷单，默认 "" |
| failedSteps | array | 否 | 失败步骤（截留最近 200 条） |
| currentCaseTitle | string | 否 | 当前用例标题，默认 "" |
| currentIteration | integer | 否 | 当前轮次，默认 0 |
| startAt | string | 否 | 计划开始时间，默认 "" |
| endAt | string | 否 | 计划结束时间，默认 "" |
| running | boolean | 否 | 是否执行中（仅新建时写入；后端状态机托管时忽略） |

> 状态机托管保护：当任务卡已处于 `done`/`running` 时，前端 3 秒自动保存**不会**覆盖 `status`/`outcome`/`case_items`/`overall_pass`/`overall_fail` 等托管字段。

#### 成功响应（200）

```json
{
  "status": true,       # 请求是否成功
  "id": "task-abc"      # 保存后的任务卡主键
}
```

#### 错误码与文案

| HTTP | message | 触发条件 |
|---|---|---|
| 400 | 任务ID不能为空 | 请求体 `id` 缺失或为纯空白 |
| 400 | task_id is required | 防御性兜底（`api.save_task_card` 内部校验，正常已被上层拦截） |

---

### 5.3 删除任务卡片接口：DELETE /api/runner/tasks/{task_id}

| 项 | 值 |
|---|---|
| 鉴权 | 需登录(Bearer) |
| 路径参数 | `task_id`（string，任务卡主键） |

#### 请求

无请求体。

#### 成功响应（200）

```json
{
  "status": true,    # 请求是否成功
  "message": "已删除"  # 删除结果文案（任务不存在时静默 no-op，仍返回成功）
}
```

---

## 6. 调试与监控

### 6.1 单步调试接口：POST /api/runner/run-step

| 项 | 值 |
|---|---|
| 鉴权 | 需登录(Bearer) |
| Content-Type | application/json |

#### 请求体

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| type | string | 否 | 步骤类型，默认 "click"；须在 `KNOWN_STEP_TYPES` 白名单内（含基础 UI 与 `adb_*` 新名 + 旧名兼容） |
| xpath | string | 否 | 主定位 xpath，默认 ""（start_app/kill_app 系列用作包名） |
| xpath2 | string | 否 | 次定位 xpath，默认 "" |
| timeout | number | 否 | 超时秒，默认 10 |
| expected_text | string | 否 | 期望文本，默认 "" |
| index | number | 否 | 元素索引，默认 0 |
| direction | string | 否 | 滑动方向，默认 "" |
| distance | number | 否 | 滑动距离，默认 500 |
| description | string | 否 | 步骤描述，默认取 step_type |
| device_serial | string | 否 | 目标设备序列号；缺省用当前调试设备 |

#### 成功响应（200）

```json
{
  "status": true,                       # 请求是否成功
  "result": "pass",                     # 执行结果：pass
  "message": "步骤「点击登录」执行成功",   # 结果文案
  "logs": ["open app", "click ..."]     # 执行日志列表
}
```

#### 失败响应（200，`status=false`）

```json
{
  "status": false,                       # 请求是否失败
  "result": "fail",                      # 执行结果（非 pass）
  "message": "步骤「点击登录」执行失败 (fail)",  # 失败文案
  "logs": ["..."]                        # 执行日志
}
```

#### 错误码与文案

| HTTP | message | 触发条件 |
|---|---|---|
| 200 | Unknown step type: {type} | `type` 不在白名单（未显式设状态码） |
| 200 | 请先在用例编辑页顶部选择调试设备 | 未指定 `device_serial` 且无当前调试设备 |
| 200 | 步骤执行异常: {str(e)} | 执行过程抛出异常 |

---

### 6.2 运行监控接口：GET /api/runner/monitor/{run_id}

> **预留端点**（TREP v1.0 协议健康监控），WS 断开时前端可降级轮询。

| 项 | 值 |
|---|---|
| 鉴权 | 需登录(Bearer) |
| 路径参数 | `run_id`（string，运行 ID） |

#### 请求

无请求体。

#### 成功响应 — 活跃运行（200）

```json
{
  "status": true,                       # 请求是否成功
  "run_id": "run_AB123_20260821_153000",
  "live": true,                         # 是否活跃（内存态）
  "status": "running",                  # run 态
  "is_running": true,                   # 是否运行中
  "device": {                           # 设备信息
    "serial": "AB123",                  # 设备序列号
    "status": "connected",              # connected / disconnected
    "resolution": "1080x2400",          # 分辨率（仅在线时返回）
    "sdk": "33",                        # SDK 版本（仅在线时返回）
    "battery": 87                       # 电量（仅在线时返回）
  },
  "selected_cases": [{"case_id": "TC-1", "title": "登录", "steps_data": []}],
  "loop_count": 3,
  "started_at": "2026-08-21T15:30:00",
  "log_tail": ["...", "..."]            # 最近 50 条日志
}
```

#### 成功响应 — 已完成/历史运行（从 DB，200）

```json
{
  "status": true,
  "run_id": "run_AB123_20260821_153000",
  "live": false,                        # 非活跃
  "status": "completed",                # run 态（DB 原始值）
  "device_serial": "AB123",
  "selected_cases": [{"case_id": "TC-1", "title": "登录", "steps_data": []}],
  "loop_count": 3,
  "summary": {"_perf": {"count": 10, "max": 1.2, "min": 0.8, "avg": 1.0, "median": 1.0}},  # 汇总（含性能统计）
  "started_at": "2026-08-21T15:30:00",
  "finished_at": "2026-08-21T15:31:20"
}
```

#### 错误码与文案

| HTTP | message | 触发条件 |
|---|---|---|
| 404 | run not found | 活跃运行与 DB 均不存在该 run_id |

---

### 6.3 运行快照接口：GET /api/runner/run/{run_id}/snapshot

> **预留端点**（TREP v1.0 状态快照，WS 降级兜底）。

| 项 | 值 |
|---|---|
| 鉴权 | 需登录(Bearer) |
| 路径参数 | `run_id`（string，运行 ID） |

#### 请求

无请求体。

#### 成功响应 — 活跃运行（200）

```json
{
  "status": true,                       # 请求是否成功
  "run_id": "run_AB123_20260821_153000",
  "live": true,
  "status": "running",                  # run 态
  "cases": [                            # 各用例结果（内存态，字段为 case_title/pass/fail/rate）
    {"case_title": "登录", "pass": 3, "fail": 0, "rate": "100%"}
  ],
  "client_task_id": "task-abc"          # 关联任务卡 ID（可能为空串）
}
```

#### 成功响应 — 已完成运行（从 DB，200）

```json
{
  "status": true,
  "run_id": "run_AB123_20260821_153000",
  "live": false,
  "status": "completed",                # run 态（DB 原始值）
  "cases": [                            # 各用例聚合（字段为 case_id/pass/fail/total）
    {"case_id": "TC-1", "pass": 3, "fail": 0, "total": 3}
  ],
  "client_task_id": "task-abc"
}
```

#### 错误码与文案

| HTTP | message | 触发条件 |
|---|---|---|
| 404 | run not found | 活跃运行与 DB 均不存在该 run_id |

---

## 7. 文件服务

### 7.1 步骤截图接口：GET /api/runner/step-screenshots/{filepath}

| 项 | 值 |
|---|---|
| 鉴权 | 公开（`PUBLIC_PREFIXES` 白名单，`<img src>` 无法带 Authorization 头） |
| 路径参数 | `filepath`（string，截图相对路径，可含子目录） |

#### 请求

无请求体；直接以 URL 作为 `<img src>`。

#### 成功响应（200）

**FileResponse，非 JSON**：`Content-Type: image/png`，二进制 PNG 流。

#### 错误码与文案

| HTTP | message | 触发条件 |
|---|---|---|
| 403 | invalid path | 规范化后的路径越出 `SCREENSHOT_DIR`（路径穿越防护） |
| 404 | not found | 文件不存在 |

---

## 8. WebSocket 通道 /ws/test-run/{run_id}

> 全项目仅 2 个 WS 生产点之一（真相源 `gateway/routing.py`）。消费者只推送，写库仍走 `api.py`。事件真相源 `callbacks.py`，**10 种 type 一个不能漏**。

### 8.1 连接握手

- 地址：`/ws/test-run/{run_id}?token=<access_token>`
- token 经 **query 参数**传入（WS 无法带 Authorization 头）；校验失败关闭码 `4001`。

| 关闭码 | reason | 触发条件 |
|---|---|---|
| 4001 | missing token | 未携带 token 参数 |
| 4001 | invalid token | token 校验返回空 |
| 4001 | token verification failed | token 校验抛异常 |

### 8.2 事件列表（每条消息均带 `run_id` 与递增 `seq`）

| type | 关键字段 | 说明 |
|---|---|---|
| `log` | `message` | 日志文本（计划、进度、提示等） |
| `heartbeat` | — | 心跳，每 5s 一次（前端 15s 无心跳判连接丢失） |
| `case_started` | `case_id`, `case_title`, `loop_count` | 用例开始 |
| `step_started` | `case_id`, `iteration`, `step_index`, `total_steps`, `step_type`, `description` | 步骤开始 |
| `step_result` | `case_id`, `iteration`, `step_index`, `total_steps`, `step_type`, `description`, `result` | 步骤结果 |
| `iteration_result` | `case_id`, `iteration`, `result`, `duration_ms` | 单轮迭代结果 |
| `case_finished` | `case_id`, `pass`, `fail`, `rate` | 用例结束汇总 |
| `run_finished` | `summary`, `log_path` | 整次运行结束（并清理 seq 计数与客户端集合） |
| `device_error` | `message` | 设备错误（错误文案） |
| `run_started` | — | 预检通过、正式进入执行（前端暂不消费，仍须推送） |

> `seq` 由 `callbacks._broadcast` 按 run_id 递增，前端检测 gap 触发对账；`run_finished` 后清除该 run_id 的 seq 与客户端集合。

### 8.3 事件报文示例

```json
{
  "type": "step_result",      # 事件类型
  "run_id": "run_AB123_20260821_153000",
  "case_id": "TC-1",          # 用例 ID
  "iteration": 2,             # 第几轮
  "step_index": 1,            # 步骤序号
  "total_steps": 5,           # 步骤总数
  "step_type": "click",       # 步骤类型
  "description": "点击登录",   # 步骤描述
  "result": "pass",           # 步骤结果
  "seq": 42                   # 递增序号（_broadcast 自动附加）
}
```
