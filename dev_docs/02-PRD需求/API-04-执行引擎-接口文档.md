# API-04 — 执行引擎接口文档

> 模块：`apps/test_runner/` `apps/report_generator/` · 端点：20 个 · 基础路径：`/api/runner` `/api/reports`
> 关联：[PRD-04-执行引擎](./PRD-04-执行引擎.md) · [PRD-04-执行引擎-业务功能](./PRD-04-执行引擎-业务功能.md)
> 版本：v1.0 · 日期：2026-07-29

---

## 0. 通用约定

### 请求头

| Header | 值 | 必填 | 说明 |
|--------|------|:--:|------|
| `Authorization` | `Bearer <JWT>` | ✅ | 登录获取，前端存入 localStorage |
| `Content-Type` | `application/json` | ✅ | 所有 POST 请求 |

> 以下端点免鉴权：`/api/runner/run/{id}/status`、`/api/runner/runs`、`/api/runner/step-screenshots/*`、所有 `/api/reports/*`

### 响应格式

```json
// 成功
{"status": true, "data": {...}}

// 失败
{"status": false, "message": "具体错误描述"}
```

### 错误码速查

| HTTP 状态码 | 含义 | 触发场景 |
|:--:|------|----------|
| 400 | 请求参数错误 | 缺少必填字段、类型错误、校验失败 |
| 401 | 未登录或 Token 过期 | Authorization 头缺失或无效 |
| 404 | 资源不存在 | run_id / task_id 未找到 |
| 409 | 状态冲突 | 设备正忙、任务已结束不可操作 |
| 500 | 服务器内部错误 | 未捕获异常 |

### 字段命名转换

| 层 | 规范 | 示例 |
|----|------|------|
| HTTP JSON 请求/响应 | `snake_case` | `loop_count`, `device_serial`, `client_task_id` |
| 前端 JS | `camelCase` | `loopCount`, `deviceSerial`, `clientTaskId` |
| 数据库列 | `snake_case` | `loop_count`, `device_serial`, `client_task_id` |

> 前端 `api.js` 封装层自动处理 snake_case ↔ camelCase 转换。

---

## 一、执行引擎 API（`/api/runner/`）

共 13 个端点，覆盖任务卡片 CRUD、执行控制、运行监控三大功能域。

---

### 1.1 执行控制

#### POST `/api/runner/run`

启动测试执行。支持 UI 自动化、API 测试、Web 自动化三种类型。支持定时执行和排队。

| 参数 | 类型 | 必填 | 约束 |
|------|------|:--:|------|
| `case_ids` | string[] | ✅ | 至少 1 个，从用例库选取 |
| `task_type` | string | ✅ | 枚举：`ui_automation` / `api_testing` / `web_automation` |
| `device_serial` | string | UI 必填 | 设备序列号，API/Web 类型不传 |
| `device_serials` | string[] | 否 | 多设备并行时使用，与 device_serial 二选一 |
| `loop_count` | integer | 否 | 默认 1，范围 1~10000 |
| `interval_seconds` | integer | 否 | 默认 5，最小 5 秒 |
| `package_name` | string | 否 | Android 目标包名，不传使用默认 |
| `client_task_id` | string | 否 | 前端任务 ID，用于关联 TaskCard |
| `start_at` | string | 否 | ISO 时间戳，定时执行启动时间 |
| `end_at` | string | 否 | ISO 时间戳，定时执行截止时间 |

**请求体示例**：

```json
{
  "case_ids": ["TC-001", "TC-002"],
  "task_type": "ui_automation",
  "device_serials": ["ABCD1234", "EFGH5678"],
  "loop_count": 3,
  "interval_seconds": 5,
  "client_task_id": "ID-001"
}
```

**响应** `200`：

```json
{
  "status": true,
  "runs": [
    {"run_id": "run_ABCD1234_20260729_143000", "serial": "ABCD1234"}
  ],
  "queued": ["EFGH5678"],
  "case_count": 2,
  "loop_count": 3,
  "parallel": 1
}
```

> `runs`：立即启动的运行列表；`queued`：设备忙时进入排队的设备列表。当 `runs` 为空且 `queued` 为空时说明没有可用设备。

**所有错误场景**：

| 传值错误 | HTTP | 响应体 |
|----------|:--:|------|
| 缺 `case_ids` | 400 | `{"status":false,"message":"case_ids required"}` |
| UI 类型缺设备 | 400 | `{"status":false,"message":"device_serial is required for UI automation tasks"}` |
| 无用例定义 | 200 | `{"status":false,"message":"no enabled test cases found"}` |
| 无可用设备 | 400 | `{"status":false,"message":"没有可用设备，请确认设备已连接且状态为在线"}` |

---

#### POST `/api/runner/run/{run_id}/stop`

停止正在执行的任务。支持两种场景：运行中（设置停止标志，当前迭代完成后结束）和前置检查阶段（阻止启动，释放设备）。

| URL 参数 | 类型 | 必填 | 说明 |
|----------|------|:--:|------|
| `run_id` | string | ✅ | 运行 ID |

**请求体**：无

**响应** `200`：

```json
// 运行中
{"status": true, "message": "stop requested"}

// 前置检查阶段
{"status": true, "message": "stopping (pre-flight)"}
```

**所有错误场景**：

| 传值错误 | HTTP | 响应体 |
|----------|:--:|------|
| run_id 不存在或已结束 | 200 | `{"status":false,"message":"run not found or already finished"}` |

---

#### POST `/api/runner/queue/cancel`

取消排队中的任务。从内存队列移除并重置 TaskCard 状态。

| 参数 | 类型 | 必填 | 说明 |
|------|------|:--:|------|
| `client_task_id` | string | ✅ | 前端任务 ID |
| `device_serial` | string | ✅ | 排队设备序列号 |

**请求体示例**：

```json
{
  "client_task_id": "ID-001",
  "device_serial": "ABCD1234"
}
```

**响应** `200`：

```json
{"status": true, "message": "已取消排队任务（5 个用例）"}
```

**所有错误场景**：

| 传值错误 | HTTP | 响应体 |
|----------|:--:|------|
| 缺少必填字段 | 400 | `{"status":false,"message":"需要提供 client_task_id 和 device_serial"}` |
| 不在队列或已执行 | 404 | `{"status":false,"message":"未找到该排队任务，可能已经开始执行"}` |

---

### 1.2 任务卡片 CRUD

#### GET `/api/runner/tasks`

列出全部任务卡片（最近 200 条，按创建时间倒序）。同时触发惰性恢复：修复孤儿运行状态、修复排队终端飘逸。

**请求体**：无

**响应** `200`：

```json
{
  "status": true,
  "tasks": [
    {
      "id": "ID-001",
      "name": "登录回归测试",
      "mode": "immediate",
      "taskType": "ui_automation",
      "deviceSerial": "ABCD1234",
      "caseIds": ["TC-001", "TC-002"],
      "loopCount": 3,
      "intervalSeconds": 5,
      "running": true,
      "runId": "run_ABCD1234_20260729_143000",
      "caseItems": [
        {
          "id": "TC-001",
          "title": "登录流程",
          "total": 3,
          "pass": 2,
          "fail": 1,
          "rate": 66,
          "status": "done",
          "steps": [
            {"type": "click", "description": "点击登录按钮", "xpath": "//..."}
          ]
        }
      ],
      "stepStates": [
        {"index": 0, "total": 3, "type": "click", "desc": "...", "result": "pass"}
      ],
      "overallPass": 5,
      "overallFail": 1,
      "logs": [
        {"time": "14:30:01", "text": "开始执行", "level": "info"}
      ],
      "createdAt": "2026-07-29 14:29:00+00:00",
      "creator": "admin",
      "currentCaseTitle": "登录流程",
      "currentIteration": 2,
      "failedSteps": [
        {"caseTitle": "登录流程", "iteration": 2, "failedStepIndex": 2, "failedResult": {...}}
      ],
      "status": "running",
      "outcome": "",
      "round": 1,
      "startAt": "",
      "endAt": "",
      "perfStats": {},
      "step_details": [
        {"step_index": 0, "step_type": "click", "result": "pass", "screenshot": "/path/to/img.png"}
      ]
    }
  ]
}
```

> 响应中的字段名已转换为 camelCase（前端 api.js 封装层处理）。

---

#### POST `/api/runner/tasks/save`

创建或更新任务卡片。以 `id` 为唯一键，存在则更新，不存在则创建。

| 参数 | 类型 | 必填 | 说明 |
|------|------|:--:|------|
| `id` | string | ✅ | 任务唯一 ID（前端生成，如 ID-001） |
| `name` | string | 否 | 任务名称 |
| `creator` | string | 否 | 创建人 |
| `mode` | string | 否 | `immediate` 或 `scheduled` |
| `taskType` | string | 否 | `ui_automation` / `api_testing` / `web_automation` |
| `deviceSerial` | string | 否 | 目标设备 |
| `caseIds` | string[] | 否 | 用例 ID 列表 |
| `caseItems` | object[] | 否 | 用例详细信息（含步骤） |
| `loopCount` | integer | 否 | 循环次数 |
| `intervalSeconds` | integer | 否 | 轮间间隔（秒） |
| `overallPass` | integer | 否 | 通过总数 |
| `overallFail` | integer | 否 | 失败总数 |
| `logs` | object[] | 否 | 日志记录 |
| `failedSteps` | object[] | 否 | 失败步骤详情 |
| `outcome` | string | 否 | 终态结果 |
| `startAt` | string | 否 | 定时启动时间 |
| `endAt` | string | 否 | 定时截止时间 |

> 创建时 `status` 自动设为 `idle`，`running` 自动设为 `false`。

**请求体示例**：

```json
{
  "id": "ID-001",
  "name": "登录回归测试",
  "creator": "admin",
  "mode": "immediate",
  "taskType": "ui_automation",
  "deviceSerial": "ABCD1234",
  "caseIds": ["TC-001", "TC-002"],
  "caseItems": [],
  "loopCount": 3,
  "intervalSeconds": 5,
  "logs": [],
  "failedSteps": [],
  "outcome": "",
  "startAt": "",
  "endAt": ""
}
```

**响应** `200`：

```json
{"status": true, "id": "ID-001"}
```

**所有错误场景**：

| 传值错误 | HTTP | 响应体 |
|----------|:--:|------|
| 缺少 id | 400 | `{"status":false,"message":"任务ID不能为空"}` |

---

#### DELETE `/api/runner/tasks/{task_id}`

删除任务卡片。不存在时无操作。

| URL 参数 | 类型 | 必填 | 说明 |
|----------|------|:--:|------|
| `task_id` | string | ✅ | 任务 ID |

**请求体**：无

**响应** `200`：

```json
{"status": true, "message": "已删除"}
```

---

### 1.3 运行监控

#### GET `/api/runner/active`

列出所有当前活跃的运行（内存中存在）。同时触发惰性恢复：从 DB 重建排队队列，触发停滞设备的出队。

**请求体**：无

**响应** `200`：

```json
{
  "status": true,
  "active": [
    {
      "run_id": "run_ABCD1234_20260729_143000",
      "status": "RUNNING",
      "selected_cases": [
        {"case_id": 1, "title": "登录流程", "steps_data": [...]}
      ],
      "loop_count": 3,
      "started_at": "2026-07-29T14:30:00",
      "device_serial": "ABCD1234",
      "client_task_id": "ID-001"
    }
  ]
}
```

---

#### GET `/api/runner/run/{run_id}/status`

查询运行状态。优先查内存活跃运行，未找到则查 DB 历史记录。

| URL 参数 | 类型 | 必填 | 说明 |
|----------|------|:--:|------|
| `run_id` | string | ✅ | 运行 ID |

**请求体**：无

**响应** `200`（运行中）：

```json
{
  "status": true,
  "run_id": "run_ABCD1234_20260729_143000",
  "status": "RUNNING",
  "is_running": true,
  "selected_cases": [...],
  "loop_count": 3,
  "started_at": "2026-07-29T14:30:00"
}
```

**响应** `200`（已结束，来自 DB）：

```json
{
  "status": true,
  "run_id": "run_ABCD1234_20260729_143000",
  "status": "COMPLETED",
  "total_iterations": 6,
  "passed": 5,
  "failed": 1,
  "selected_cases": [...],
  "loop_count": 3,
  "started_at": "2026-07-29T14:30:00",
  "finished_at": "2026-07-29T14:32:00"
}
```

**所有错误场景**：

| 传值错误 | HTTP | 响应体 |
|----------|:--:|------|
| run_id 不存在 | 404 | `{"status":false,"message":"run not found"}` |

---

#### GET `/api/runner/runs`

运行历史列表（最近 50 条），含聚合统计。

**请求体**：无

**响应** `200`：

```json
{
  "status": true,
  "runs": [
    {
      "run_id": "run_ABCD1234_20260729_143000",
      "status": "COMPLETED",
      "device_serial": "ABCD1234",
      "loop_count": 3,
      "total": 6,
      "passed": 5,
      "failed": 1,
      "started_at": "2026-07-29T14:30:00",
      "finished_at": "2026-07-29T14:32:00",
      "selected_cases": [...]
    }
  ]
}
```

---

#### GET `/api/runner/monitor/{run_id}`

TREP v1.0 运行健康监控。返回设备信息、最近日志。用于 WebSocket 断连时的 HTTP 轮询兜底。

| URL 参数 | 类型 | 必填 | 说明 |
|----------|------|:--:|------|
| `run_id` | string | ✅ | 运行 ID |

**请求体**：无

**响应** `200`（运行中）：

```json
{
  "status": true,
  "run_id": "run_ABCD1234_20260729_143000",
  "live": true,
  "status": "RUNNING",
  "is_running": true,
  "device": {
    "serial": "ABCD1234",
    "status": "connected",
    "resolution": "1080x2400",
    "sdk": "33",
    "battery": "85"
  },
  "selected_cases": [...],
  "loop_count": 3,
  "started_at": "2026-07-29T14:30:00",
  "log_tail": ["最近 50 条日志..."]
}
```

**响应** `200`（已结束）：

```json
{
  "status": true,
  "run_id": "...",
  "live": false,
  "status": "COMPLETED",
  "device_serial": "ABCD1234",
  "selected_cases": [...],
  "loop_count": 3,
  "summary": {...},
  "started_at": "...",
  "finished_at": "..."
}
```

---

#### GET `/api/runner/run/{run_id}/snapshot`

TREP v1.0 进度快照。返回每用例通过/失败统计。

| URL 参数 | 类型 | 必填 | 说明 |
|----------|------|:--:|------|
| `run_id` | string | ✅ | 运行 ID |

**请求体**：无

**响应** `200`（运行中）：

```json
{
  "status": true,
  "run_id": "run_ABCD1234_20260729_143000",
  "live": true,
  "status": "RUNNING",
  "cases": [
    {"case_title": "登录流程", "pass": 3, "fail": 0, "rate": "100%"},
    {"case_title": "退出登录", "pass": 2, "fail": 1, "rate": "66%"}
  ],
  "client_task_id": "ID-001"
}
```

**所有错误场景**：

| 传值错误 | HTTP | 响应体 |
|----------|:--:|------|
| run_id 不存在 | 404 | `{"status":false,"message":"run not found"}` |

---

### 1.4 单步调试

#### POST `/api/runner/run-step`

在已连接的调试设备上执行单个步骤，不入库。用于用例编写时的快速验证。

| 参数 | 类型 | 必填 | 说明 |
|------|------|:--:|------|
| `type` | string | ✅ | 步骤类型（click / wait / swipe 等 16 种） |
| `xpath` | string | 否 | 目标元素 XPath |
| `description` | string | 否 | 步骤描述 |
| `timeout` | integer | 否 | 超时秒数，默认 10 |
| `expected_text` | string | 否 | 期望文本（verify_text 类型用） |
| `index` | integer | 否 | 元素索引（click_indexed 用），默认 0 |
| `direction` | string | 否 | 滑动方向（swipe 用）：up/down/left/right |
| `distance` | integer | 否 | 滑动距离（像素），默认 500 |
| `device_serial` | string | 否 | 指定设备，不传使用调试设备 |

**请求体示例**：

```json
{
  "type": "click",
  "xpath": "//android.widget.Button[@text='确定']",
  "timeout": 10,
  "description": "点击确定按钮",
  "device_serial": "ABCD1234"
}
```

**响应** `200`：

```json
{
  "status": true,
  "result": "pass",
  "message": "步骤「点击确定按钮」执行成功",
  "logs": ["14:30:01 [INFO] 查找元素...", "14:30:02 [INFO] 点击成功"]
}
```

**所有错误场景**：

| 传值错误 | HTTP | 响应体 |
|----------|:--:|------|
| 未知步骤类型 | 200 | `{"status":false,"message":"Unknown step type: xxx"}` |
| 未选择调试设备 | 200 | `{"status":false,"message":"请先在用例编辑页顶部选择调试设备"}` |
| 步骤执行失败 | 200 | `{"status":false,"result":"fail","message":"步骤「xxx」执行失败"}` |

---

### 1.5 截图服务

#### GET `/api/runner/step-screenshots/{filepath}`

获取执行步骤的标注截图。路径校验：确保解析后路径在截图目录内，防止目录穿越攻击。

| URL 参数 | 类型 | 必填 | 说明 |
|----------|------|:--:|------|
| `filepath` | path | ✅ | 截图相对路径 |

**请求体**：无

**响应**：PNG 图片二进制流（`Content-Type: image/png`）

**所有错误场景**：

| 传值错误 | HTTP | 响应体 |
|----------|:--:|------|
| 非法路径（目录穿越） | 403 | `{"status":false,"message":"invalid path"}` |
| 文件不存在 | 404 | `{"status":false,"message":"not found"}` |

---

## 二、测试报告 API（`/api/reports/`）

共 6 个端点，覆盖报告列表、用例分析、运行报告、任务报告、文件下载。

> 报告端点全部免鉴权。

### 2.1 报告列表

#### GET `/api/reports/`

运行报告列表，含 KPI 汇总、缺陷摘要、每日趋势数据。

| 查询参数 | 类型 | 必填 | 说明 |
|----------|------|:--:|------|
| `start_date` | string | 否 | 起始日期 ISO |
| `end_date` | string | 否 | 截止日期 ISO |
| `run_id` | string | 否 | 按运行 ID 模糊匹配 |
| `task_name` | string | 否 | 按任务名称模糊匹配 |
| `device_serial` | string | 否 | 按设备模糊匹配 |
| `creator` | string | 否 | 按创建人模糊匹配 |
| `chart_range` | integer | 否 | 趋势天数：7/30/90，默认 30 |

**请求体**：无

**响应** `200`：

```json
{
  "status": true,
  "summary": {
    "total_runs": 10,
    "total_iterations": 60,
    "total_pass": 55,
    "total_fail": 5,
    "pass_rate": 91.7
  },
  "bug_summary": {
    "unique_issues": 2,
    "total_occurrences": 5,
    "affected_cases": 2
  },
  "trend": {
    "range_days": 30,
    "dates": ["2026-06-30", "2026-07-01", "..."],
    "labels": ["06-30", "07-01", "..."],
    "pass": [0, 5, "..."],
    "fail": [0, 1, "..."],
    "rate": [0, 83.3, "..."]
  },
  "runs": [
    {
      "run_id": "run_ABCD1234_20260729_143000",
      "status": "COMPLETED",
      "device_serial": "ABCD1234",
      "loop_count": 3,
      "case_count": 2,
      "total": 6,
      "passed": 5,
      "failed": 1,
      "rate": 83,
      "duration": "2m30s",
      "started_at": "...",
      "finished_at": "...",
      "task_name": "登录回归测试",
      "creator": "admin",
      "outcome": "completed"
    }
  ]
}
```

---

### 2.2 用例分析

#### GET `/api/reports/cases`

按通过/失败维度分层展示用例统计。失败维度额外包含缺陷去重摘要。

| 查询参数 | 类型 | 必填 | 说明 |
|----------|------|:--:|------|
| `result` | string | ✅ | `pass` 或 `fail` |
| （其余同 `list_reports`） | | 否 | 日期、运行 ID 等过滤器 |

**请求体**：无

**响应** `200`（result=pass）：

```json
{
  "status": true,
  "result_type": "pass",
  "total": 55,
  "case_count": 3,
  "groups": [
    {
      "case_title": "登录流程",
      "case_id": "TC-001",
      "count": 15,
      "tasks": [
        {"task_id": "ID-001", "task_name": "登录回归测试", "run_id": "...", "count": 15}
      ]
    }
  ]
}
```

**响应** `200`（result=fail）：

```json
{
  "status": true,
  "result_type": "fail",
  "total": 5,
  "case_count": 2,
  "groups": [...],
  "bug_summary": {
    "unique_issues": 2,
    "total_occurrences": 5,
    "affected_cases": 2,
    "cases": [
      {
        "case_title": "登录流程",
        "case_id": "TC-001",
        "issue_count": 1,
        "total_occurrences": 3,
        "issues": [
          {
            "step_type": "click",
            "description": "点击登录按钮",
            "result": "fail",
            "count": 3,
            "task_count": 1,
            "task_ids": ["ID-001"]
          }
        ]
      }
    ]
  }
}
```

**所有错误场景**：

| 传值错误 | HTTP | 响应体 |
|----------|:--:|------|
| result 不是 pass 或 fail | 400 | `{"status":false,"message":"result 必须为 pass 或 fail"}` |

---

### 2.3 运行报告

#### GET `/api/reports/run/{run_id}`

单次运行的完整报告，含用例明细、迭代详情、最近运行趋势。

| URL 参数 | 类型 | 必填 | 说明 |
|----------|------|:--:|------|
| `run_id` | string | ✅ | 运行 ID |

**请求体**：无

**响应** `200`：

```json
{
  "status": true,
  "run": {
    "run_id": "run_ABCD1234_20260729_143000",
    "status": "COMPLETED",
    "device_serial": "ABCD1234",
    "loop_count": 3,
    "selected_cases": [...],
    "started_at": "2026-07-29T14:30:00",
    "finished_at": "2026-07-29T14:32:00",
    "duration": "2m0s",
    "total_iterations": 6,
    "total_pass": 5,
    "total_fail": 1,
    "pass_rate": 83.3,
    "case_count": 2,
    "cases": [
      {
        "case_id": "TC-001",
        "case_title": "登录流程",
        "planned": 3,
        "actual": 3,
        "pass": 3,
        "fail": 0,
        "rate": 100,
        "iterations": [
          {"iteration": 1, "result": "pass", "duration_ms": 1500.0, "detail": ""},
          {"iteration": 2, "result": "pass", "duration_ms": 1450.0, "detail": ""},
          {"iteration": 3, "result": "pass", "duration_ms": 1480.0, "detail": ""}
        ]
      }
    ],
    "recent_runs": [
      {"run_id": "...", "started_at": "...", "total": 6, "passed": 5, "failed": 1, "rate": 83}
    ],
    "client_task_id": "ID-001",
    "task_name": "登录回归测试",
    "task_creator": "admin",
    "task_outcome": "completed",
    "task_failed_steps": [...]
  }
}
```

**所有错误场景**：

| 传值错误 | HTTP | 响应体 |
|----------|:--:|------|
| run_id 不存在 | 404 | `{"status":false,"message":"run not found"}` |

---

### 2.4 任务报告

#### GET `/api/reports/task/{task_id}`

从任务卡片视角查看完整报告。含任务元信息、用例明细、关联运行记录列表（最近 10 次）。

| URL 参数 | 类型 | 必填 | 说明 |
|----------|------|:--:|------|
| `task_id` | string | ✅ | 任务 ID |

**请求体**：无

**响应** `200`：

```json
{
  "status": true,
  "task": {
    "task_id": "ID-001",
    "name": "登录回归测试",
    "creator": "admin",
    "mode": "immediate",
    "device_serial": "ABCD1234",
    "loop_count": 3,
    "interval_seconds": 5,
    "status": "done",
    "outcome": "completed",
    "round": 1,
    "conclusion": "",
    "failed_steps": [...],
    "case_ids": ["TC-001", "TC-002"],
    "case_items": [
      {
        "id": "TC-001",
        "title": "登录流程",
        "total": 3,
        "pass": 3,
        "fail": 0,
        "rate": 100,
        "steps": [...]
      }
    ],
    "overall_pass": 5,
    "overall_fail": 1,
    "pass_rate": 83.3,
    "created_at": "2026-07-29 14:29:00+00:00",
    "updated_at": "2026-07-29 14:32:00+00:00",
    "linked_runs": [
      {
        "run_id": "run_ABCD1234_20260729_143000",
        "status": "COMPLETED",
        "total": 6,
        "passed": 5,
        "failed": 1,
        "rate": 83,
        "started_at": "2026-07-29T14:30:00",
        "finished_at": "2026-07-29T14:32:00"
      }
    ],
    "step_details": [...]
  }
}
```

**所有错误场景**：

| 传值错误 | HTTP | 响应体 |
|----------|:--:|------|
| task_id 不存在 | 404 | `{"status":false,"message":"task not found"}` |

---

### 2.5 文件服务

#### GET `/api/reports/{filename}`

下载报告文件（CSV / Markdown / 日志）。

| URL 参数 | 类型 | 必填 | 说明 |
|----------|------|:--:|------|
| `filename` | string | ✅ | 文件名（仅取基础名，防路径穿越） |

**请求体**：无

**响应**：文件下载（`Content-Disposition: attachment`），Content-Type 按扩展名设置。

**所有错误场景**：

| 传值错误 | HTTP | 响应体 |
|----------|:--:|------|
| 文件不存在 | 404 | `{"status":false,"message":"not found"}` |

---

#### GET `/api/reports/{filename}/content`

获取报告文件内容（行内预览）。CSV 文件自动解析为结构化行和表头。

| URL 参数 | 类型 | 必填 | 说明 |
|----------|------|:--:|------|
| `filename` | string | ✅ | 文件名 |

**请求体**：无

**响应** `200`（CSV）：

```json
{
  "status": true,
  "name": "report_20260729.csv",
  "type": "csv",
  "size": 12345,
  "content": "原始文本...",
  "rows": [{"列1": "值1", "列2": "值2"}],
  "headers": ["列1", "列2"]
}
```

**响应** `200`（Markdown）：

```json
{
  "status": true,
  "name": "report_20260729.md",
  "type": "md",
  "size": 5678,
  "content": "# 测试报告\n\n...",
  "rows": [],
  "headers": []
}
```

---

## 三、WebSocket API

### WS `/ws/test-run/{run_id}?token={JWT}`

**协议**：TREP v1.0

**鉴权**：JWT token 作为查询参数传递，连接时验证。无效 token 关闭连接（code 4001）。

**消息格式**：每条 JSON 消息含 `seq`（单调递增序号）和 `run_id`。

#### 服务端推送事件（10 种）

| 事件类型 | 触发时机 | 频率 | 关键字段 |
|----------|----------|:--:|------|
| `heartbeat` | 每 5 秒 | 定时 | — |
| `log` | 任意日志输出 | 高频 | `message` |
| `run_started` | 前置检查通过 | 1 次/运行 | — |
| `case_started` | 每个用例开始 | 1 次/用例 | `case_id`, `case_title`, `loop_count` |
| `step_started` | 每个步骤开始 | 1 次/步骤 | `step_index`, `total_steps`, `step_type`, `description` |
| `step_result` | 每个步骤结束 | 1 次/步骤 | `step_index`, `result` |
| `iteration_result` | 每次迭代结束 | 1 次/迭代 | `iteration`, `result`, `duration_ms` |
| `case_finished` | 用例全部迭代完成 | 1 次/用例 | `pass`, `fail`, `rate` |
| `run_finished` | 全部用例完成或停止 | 1 次/运行 | `summary`, `log_path` |
| `device_error` | 设备连接异常 | 异常时 | `error` |

**心跳机制**：服务端每 5 秒发送 `heartbeat`。前端超过 15 秒未收到心跳 → 判定断连，自动重连（指数退避 1s→2s→4s→8s→16s，最多 5 次）。

**Seq 序号**：每条消息的 `seq` 单调递增。前端检测序号跳跃（如 3→7）→ 标记缺失，触发 HTTP 监控端点做状态重同步。

**客户端消息**：消费者不处理入站消息（`receive` 为空操作，仅维持连接）。

---

## 四、API 业务流

### 参数来源标记

| 标记 | 含义 | 示例 |
|:--:|------|------|
| 🖊️ | 用户输入（表单字段） | 任务名称、循环次数、设备选择 |
| 🔗 | 上一接口响应传递 | `run_id` ← POST /run 返回 |
| 🤖 | 后端自动生成 | `created_at`、`run_id`（后端生成） |
| 🔐 | JWT 自动注入 | Authorization header |
| 📋 | 页面/路由参数 | URL 中的 `taskId` |
| 💾 | localStorage | 用户偏好（视图模式） |

### 场景 1：创建任务 → 立即执行 → 实时监控 → 查看报告

```
┌─ 步骤 1：保存任务卡片 ────────────────────────────────────────┐
│ POST /api/runner/tasks/save                                    │
│                                                                │
│ 请求体:                                                        │
│   id          ← 🖊️ 前端生成 "ID-001"                          │
│   name        ← 🖊️ 用户输入 "登录回归测试"                     │
│   taskType    ← 🖊️ 用户选择 "ui_automation"                   │
│   deviceSerial← 🖊️ 用户选择 "ABCD1234"                        │
│   caseIds     ← 🖊️ 用户在用例树中多选 ["TC-001","TC-002"]     │
│   loopCount   ← 🖊️ 用户输入 3                                 │
│                                                                │
│ 响应: {ok, id: "ID-001"}                                      │
│                                                                │
│ 产出参数: taskId = "ID-001" ← 🔗 供步骤2使用                   │
└────────────────────────────────────────────────────────────────┘

┌─ 步骤 2：启动执行 ────────────────────────────────────────────┐
│ POST /api/runner/run                                            │
│                                                                │
│ 请求体:                                                        │
│   case_ids       ← 🖊️ 用户选择的用例 ["TC-001","TC-002"]      │
│   task_type      ← 🖊️ "ui_automation"                         │
│   device_serials ← 🖊️ ["ABCD1234"]                            │
│   loop_count     ← 🖊️ 3                                       │
│   client_task_id ← 🔗 "ID-001"（步骤1产出）                    │
│                                                                │
│ 响应: {ok, runs: [{run_id:"run_...",serial:"ABCD1234"}]}       │
│                                                                │
│ 产出参数:                                                      │
│   run_id = "run_ABCD1234_..." ← 🔗 供步骤3/4使用              │
│                                                                │
│ ⚠️ 若设备忙 → runs=[], queued=["ABCD1234"]                    │
│    任务自动进入排队，前端显示"等待中"                           │
│ ⚠️ 若无可用设备 → 400 "没有可用设备"                           │
└────────────────────────────────────────────────────────────────┘

┌─ 步骤 3：WebSocket 实时监控 ───────────────────────────────────┐
│ WS /ws/test-run/{run_id}?token={JWT}                           │
│                                                                │
│ token ← 🔐 JWT（登录时存入 localStorage）                       │
│ run_id ← 🔗 步骤2响应                                          │
│                                                                │
│ 事件流:                                                        │
│   run_started → case_started → step_started → step_result     │
│   → iteration_result → case_finished → run_finished            │
│                                                                │
│ 前端处理:                                                      │
│   • step_started → 更新步骤状态为"执行中"                       │
│   • step_result  → 更新步骤结果为"通过/失败"                    │
│   • log          → 追加到日志面板                               │
│   • case_finished→ 用例卡片标记完成，更新通过率                 │
│   • run_finished → 全部完成，显示"查看报告"按钮                 │
│                                                                │
│ ⚠️ 心跳超时 15s → 前端判定断连 → 自动重连（最多5次）           │
│ ⚠️ 重连失败 → 降级到 HTTP 轮询 /api/runner/monitor/{run_id}   │
└────────────────────────────────────────────────────────────────┘

┌─ 步骤 4：查看报告 ────────────────────────────────────────────┐
│ GET /api/reports/task/ID-001                                   │
│                                                                │
│ task_id ← 🔗 步骤1产出                                         │
│                                                                │
│ 响应: {ok, task: {..., linked_runs: [...], case_items: [...]}} │
│                                                                │
│ 前端展示:                                                      │
│   • 任务信息卡片：名称、设备、循环次数                          │
│   • 用例汇总：每个用例通过率 + 迭代明细                        │
│   • 关联运行记录列表（最后一次在最前）                          │
│   • 步骤截图（Web 用例含标注截图）                              │
└────────────────────────────────────────────────────────────────┘
```

**参数流转链**：

```
tasks/save POST ──→ taskId ──→ /run POST ──→ run_id ──→ WS connect
                                                    │
                                                    ├──→ /monitor/{run_id} GET（WS 断连兜底）
                                                    ├──→ /snapshot GET（进度快照）
                                                    └──→ /reports/run/{run_id} GET（查看报告）

tasks/save POST ──→ taskId ──→ /reports/task/{taskId} GET（任务视角报告）
```

### 场景 2：定时执行 → 等待 → 自动启停

```
┌─ 步骤 1：创建定时任务 ────────────────────────────────────────┐
│ POST /api/runner/tasks/save                                    │
│                                                                │
│ 请求体:                                                        │
│   mode    ← 🖊️ "scheduled"                                    │
│   startAt ← 🖊️ "2026-07-30T10:00:00"                         │
│   endAt   ← 🖊️ "2026-07-30T12:00:00"                         │
│   （其余同场景1）                                               │
│                                                                │
│ 响应: {ok, id: "ID-002"}                                      │
└────────────────────────────────────────────────────────────────┘

┌─ 步骤 2：提交定时执行 ────────────────────────────────────────┐
│ POST /api/runner/run                                            │
│   start_at ← 🔗 "2026-07-30T10:00:00"（步骤1字段）             │
│   end_at   ← 🔗 "2026-07-30T12:00:00"                         │
│                                                                │
│ 后端行为:                                                      │
│   1. 锁定设备（防止被其他任务占用）                              │
│   2. 后台协程挂起，sleep 到 start_at                            │
│   3. 同时启动 auto_stop 协程，sleep 到 end_at                   │
│   4. 到达 start_at → 执行同立即执行流程                        │
│   5. 到达 end_at → 自动调用 stop_run                           │
│                                                                │
│ ⚠️ 挂起期间用户可调用 /stop 取消                               │
│ ⚠️ 挂起超过 24h → 任务自动失败                                 │
└────────────────────────────────────────────────────────────────┘
```

### 场景 3：执行中停止 → 排队任务自动出队

```
用户A: admin（创建并执行任务）        用户B: tester（提交排队任务）
══════════════════════                ══════════════════════

POST /run                              POST /run
  device_serials: ["ABCD1234"]           device_serials: ["ABCD1234"]
  client_task_id: "ID-001"              client_task_id: "ID-002"
  → runs: [{run_id:"...",serial:"ABCD1234"}]  → runs: [], queued: ["ABCD1234"]
  → 任务A 开始执行                      → 任务B 进入等待队列

WS 实时监控中...                       GET /api/runner/tasks
                                        → task "ID-002" status: "queued"

POST /run/{run_id}/stop                GET /api/runner/active
  → "stop requested"                    → 设备释放后，任务B 自动出队
  → 任务A 状态 → done/stopped           → task "ID-002" status: "running"
  → 设备释放
  → 🔓 触发出队：任务B 开始执行
```

### 场景 4：重跑任务

```
GET /api/reports/task/ID-001
  → task.outcome: "completed"

用户点击「重跑」
  → 复用已有配置（用例、设备、循环次数不变）
  → POST /api/runner/run（参数同首次执行）
  → client_task_id = "ID-001"（同一张任务卡片）
  → 新建 TestRunRecord（新的 run_id）
  → TaskCard.run 指向新记录（旧记录保留在 DB）
  → linked_runs 数组新增一条（最近10条）
```

---

## 五、数据库表

### 5.1 表关联总览

```
tr_task_cards (任务卡片)
  │  task_id (主键，如 "ID-001")
  │  run ──FK(SET_NULL)──→ tr_test_runs (运行记录)
  │                            │  run_id (唯一，如 "run_ABCD1234_...")
  │                            │
  │                            └── results ──FK(CASCADE)──→ tr_test_results (测试结果)
  │                                                           │  case_id (索引)
  │                                                           │  iteration
  │                                                           │  result (pass/fail/stopped)
  │                                                           │  duration_ms
  │                                                           └  step_details (JSON，含截图路径)

tr_test_sop (AI SOP 会话)
  │  sop_id (唯一，独立表，无 FK 关系)
  │  run_id (字符串引用，不对应 FK)
  └  (存储 AI 四阶段工作流的会话状态)

rg_reports (报告文件)
  └  run_id (字符串引用，索引)
```

### 5.2 任务卡片 `tr_task_cards`

核心业务表，一张任务卡片 = 一次测试计划。

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `task_id` | CharField(50) PK | — | 前端生成的唯一 ID（如 ID-001），非自增 |
| `name` | CharField(200) | `""` | 任务名称 |
| `creator` | CharField(200) | `""` | 创建人用户名 |
| `task_type` | CharField(32) | `"ui_automation"` | 任务类型：ui_automation / api_testing / web_automation |
| `mode` | CharField(20) | `"immediate"` | 执行方式：immediate / scheduled |
| `device_serial` | CharField(200) | `""` | 目标设备序列号 |
| `case_ids` | JSONField | `[]` | 选中的用例 ID 列表 |
| `loop_count` | IntegerField | 1 | 每用例执行轮数 |
| `interval_seconds` | IntegerField | 5 | 轮间等待秒数 |
| `status` | CharField(20) | `"idle"` | 状态：idle / queued / running / done |
| `running` | BooleanField | False | 是否正在执行（冗余标志） |
| `outcome` | CharField(20) | `""` | 终态结果：completed / stopped / interrupted / error |
| `run` | FK(TestRunRecord) | null | 关联的当前运行记录（SET_NULL） |
| `case_items` | JSONField | `[]` | 用例详细信息快照（含步骤） |
| `step_states` | JSONField | `[]` | 每步骤状态追踪（供 UI 渲染） |
| `overall_pass` | IntegerField | 0 | 累计通过次数 |
| `overall_fail` | IntegerField | 0 | 累计失败次数 |
| `logs` | JSONField | `[]` | 执行日志（最多 1000 条） |
| `failed_steps` | JSONField | `[]` | 失败步骤详情 |
| `current_case_title` | CharField(500) | `""` | 当前执行的用例标题 |
| `current_iteration` | IntegerField | 0 | 当前迭代轮次 |
| `round` | IntegerField | 0 | 已完成轮数 |
| `conclusion` | TextField | `""` | 执行结论 |
| `bug_ticket` | TextField | `""` | 关联缺陷单 |
| `start_at` | CharField(100) | `""` | 定时启动时间 ISO |
| `end_at` | CharField(100) | `""` | 定时截止时间 ISO |
| `created_at` | DateTimeField | auto | 创建时间 |
| `updated_at` | DateTimeField | auto | 更新时间 |

**索引**：`status`、`device_serial`、`(status, device_serial)` 联合索引。默认排序：`-created_at`。

---

### 5.3 运行记录 `tr_test_runs`

每次执行的不可变审计快照。

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `run_id` | CharField(200) UNIQUE | — | 唯一运行标识（含设备序列号和时间戳） |
| `client_task_id` | CharField(50) | `""` | 关联的任务卡片 ID |
| `status` | CharField(50) | `"PENDING"` | 运行状态：PENDING / RUNNING / COMPLETED / FAILED / STOPPED |
| `device_serial` | CharField(200) | `""` | 执行设备 |
| `selected_cases` | JSONField | `[]` | 用例快照（冻结执行时的步骤定义） |
| `loop_count` | IntegerField | 1 | 循环次数 |
| `summary` | JSONField | `{}` | 通过率汇总：`{case_id: {pass, fail, rate}}` |
| `started_at` | CharField(100) | `""` | 启动时间 ISO |
| `finished_at` | CharField(100) | `""` | 结束时间 ISO |
| `csv_path` | CharField(1000) | `""` | CSV 报告文件路径 |
| `log_path` | CharField(1000) | `""` | 日志文件路径 |

---

### 5.4 测试结果 `tr_test_results`

每次迭代的细粒度结果，一用例循环 3 次 = 3 行。

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `run` | FK(TestRunRecord) | null | 所属运行记录（CASCADE 删除） |
| `case_id` | CharField(200) | null | 用例 ID 字符串（支持 TC-xxx / API-xxx / WEB-xxx） |
| `case_type` | CharField(32) | `"ui_automation"` | 用例类型区分 |
| `iteration` | IntegerField | — | 迭代序号（1-based） |
| `result` | CharField(50) | — | 结果：pass / fail / stopped |
| `duration_ms` | FloatField | 0.0 | 执行耗时（毫秒） |
| `detail` | TextField | `""` | 错误详情 |
| `step_details` | JSONField | `[]` | 每步详情（含标注截图路径） |
| `created_at` | DateTimeField | auto | 创建时间 |

**索引**：`result`、`(case_type, case_id)` 联合索引、`case_id` 单列索引。

---

### 5.5 AI SOP 会话 `tr_test_sop`

AI 驱动的四阶段测试工作流会话记录。独立表，无 FK。

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `sop_id` | CharField(50) UNIQUE | — | 会话唯一标识 |
| `conv_id` | IntegerField | 0 | 关联对话 ID |
| `phase` | IntegerField | 1 | 当前阶段（1-4） |
| `status` | CharField(20) | `"active"` | 会话状态 |
| `requirement` | TextField | `""` | 用户需求原文 |
| `case_design` | JSONField | `[]` | 用例设计方案（阶段 2 产出） |
| `element_mapping` | JSONField | `[]` | 元素映射（阶段 3 产出） |
| `element_gaps` | JSONField | `[]` | 缺失元素记录 |
| `debug_notes` | JSONField | `[]` | 调试备注 |
| `case_ids` | JSONField | `[]` | 最终选中的用例 ID 列表 |
| `run_id` | CharField(200) | `""` | 关联运行 ID（字符串引用） |
| `run_results` | JSONField | `{}` | 执行结果汇总 |
| `created_at` | DateTimeField | auto | — |
| `updated_at` | DateTimeField | auto | — |

---

### 5.6 内存模型（不持久化）

执行期间使用的 Python dataclass，运行时存在于 `_active_runs` 字典中：

| 类 | 用途 | 关键字段 |
|------|------|------|
| `TestRun` | 一次运行的完整内存表示 | `run_id`, `status`, `case_results`, `perf_results`, `summary` |
| `TestCaseDef` | 单个用例的运行时定义 | `id`, `title`, `steps_data` (list[TestStep]), `watchers`, `extra_data` |
| `TestResult` | 单次迭代的运行时结果 | `case_id`, `iteration`, `result`, `duration_ms`, `step_details` |
| `TestRunStatus` | 运行状态枚举 | `PENDING` / `RUNNING` / `STOPPED` / `COMPLETED` |

> 执行完成后，`TestRun.case_results` 批量写入 `tr_test_results` 表，`summary` 写入 `tr_test_runs` 表。

---

## 六、汇总

### 端点总览

| # | 方法 | 路径 | 鉴权 | 所属 |
|:--:|:--:|------|:--:|------|
| 1 | POST | `/api/runner/run` | ✅ | 执行控制 |
| 2 | POST | `/api/runner/run/{id}/stop` | ✅ | 执行控制 |
| 3 | POST | `/api/runner/queue/cancel` | ✅ | 执行控制 |
| 4 | GET | `/api/runner/tasks` | ✅ | 任务 CRUD |
| 5 | POST | `/api/runner/tasks/save` | ✅ | 任务 CRUD |
| 6 | DELETE | `/api/runner/tasks/{id}` | ✅ | 任务 CRUD |
| 7 | GET | `/api/runner/active` | ✅ | 运行监控 |
| 8 | GET | `/api/runner/run/{id}/status` | — | 运行监控 |
| 9 | GET | `/api/runner/runs` | — | 运行监控 |
| 10 | GET | `/api/runner/monitor/{id}` | ✅ | 运行监控 |
| 11 | GET | `/api/runner/run/{id}/snapshot` | ✅ | 运行监控 |
| 12 | POST | `/api/runner/run-step` | ✅ | 单步调试 |
| 13 | GET | `/api/runner/step-screenshots/*` | — | 截图服务 |
| 14 | GET | `/api/reports/` | — | 报告列表 |
| 15 | GET | `/api/reports/cases` | — | 用例分析 |
| 16 | GET | `/api/reports/run/{id}` | — | 运行报告 |
| 17 | GET | `/api/reports/task/{id}` | — | 任务报告 |
| 18 | GET | `/api/reports/{filename}` | — | 文件下载 |
| 19 | GET | `/api/reports/{filename}/content` | — | 文件预览 |
| WS | WS | `/ws/test-run/{id}?token={jwt}` | JWT | 实时推送 |

### 数据表总览

| 表名 | 行数特征 | 写入频率 | 说明 |
|------|:---:|:---:|------|
| `tr_task_cards` | 较少（用户创建） | 低 | 任务计划，一张卡片可多次执行 |
| `tr_test_runs` | 中等（每次执行 1 条） | 中 | 运行审计快照，不可变 |
| `tr_test_results` | 较多（每迭代 1 条） | 高（执行中批量写入） | 细粒度迭代结果 |
| `tr_test_sop` | 较少（每次 AI 会话 1 条） | 低 | AI 工作流状态 |
