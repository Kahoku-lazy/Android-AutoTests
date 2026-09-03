# API-测试报告 — /api/reports/*

> 测试报告模块（report_generator）6 个只读端点：报告列表 / 用例分解 / 运行报告 / 任务报告 / 报告内容查看 / 报告下载。
> 真相源：`apps/report_generator/urls.py` + `views.py` + `api.py`（本 App 无 serializers.py / views_drf.py / views_api.py，全部为函数式视图）。
> 本 App 为 legacy 平铺信封特例（ARCH-07），非全局 `{status, data}` 信封。

## 1. 总览

| 接口 | 方法 | 鉴权 | 说明 |
|---|---|---|---|
| 报告列表接口 | GET /api/reports/ | 需登录(Bearer) | 执行运行列表 + KPI 汇总 + 趋势，支持多条件过滤 |
| 用例分解接口 | GET /api/reports/cases | 需登录(Bearer) | 当前过滤条件下按用例聚合 pass/fail 分解 |
| 运行报告接口 | GET /api/reports/run/{run_id} | 需登录(Bearer) | 单次执行（run）的完整聚合报告 |
| 任务报告接口 | GET /api/reports/task/{task_id} | 需登录(Bearer) | 任务卡（TaskCard）视角的综合报告 |
| 报告内容查看接口 | GET /api/reports/{filename}/content | 需登录(Bearer) | 返回报告文件原始文本，供前端内联查看 |
| 报告下载接口 | GET /api/reports/{filename} | 需登录(Bearer) | 下载报告文件（FileResponse，非 JSON） |

## 2. 通用约定

- **尾斜杠**：仅「报告列表接口」为 `/api/reports/`（带尾斜杠）；其余 5 个端点路径**均不带尾斜杠**（以 urls.py 为准）。
- **响应信封特例（legacy 平铺）**：本 App 全部响应为**平铺** `{status, ...}`，非全局 `{status, data}`；失败为 `{status: false, message}`。前端按平铺读取，**禁止改造成信封式**。
- **下载端点走 FileResponse**（非 JSON），前端用 `fetch().text()` 消费；`{filename}/content` 端点返回的是 JSON（平铺），其中 `content` 为文件原始文本，供前端内联查看（本端点并非 FileResponse，也不是 HTML 文档——README/AGENTS 中的「HTML 内容查看」指前端内联展示用途）。
- **鉴权**：`/api/reports/*` 不在中间件公开白名单内，全部需登录；携带 `Authorization: Bearer <access_token>`。
- **无请求体**：6 个端点均为 GET，无请求体；筛选条件经 Query 参数、路径参数（`run_id` / `task_id` / `filename`）传入。
- **只读**：本 App 无 ORM 写；报告文件由 test_runner 落盘于 `settings.LOG_DIR`（`<项目根>/logs`），本 App 只读盘 + 查询聚合。
- **路径穿越防护**：`{filename}` 一律经 `Path(filename).name` 取 basename 后再拼到 `LOG_DIR` 下，目录部分被剥离；文件不存在返回 404，不落盘、不泄漏。
- 所有视图均加 `@csrf_exempt`（依赖 JWT，关闭 CSRF 校验）。

### 通用错误（中间件层，适用于全部 6 端点）

| HTTP | message | 触发条件 |
|---|---|---|
| 401 | 请先登录 | 未携带 `Authorization: Bearer` 头，或头不以 `Bearer ` 开头 |
| 401 | 登录已过期或令牌无效 | token 校验失败（无效 / 过期 / 非 access 类型） |

---

## 3. 报告列表接口：GET /api/reports/

| 项 | 值 |
|---|---|
| 鉴权 | 需登录(Bearer) |
| 方法 | GET |
| 信封 | legacy 平铺 `{status, ...}` |

### 查询参数

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| start_date | string | 否 | 起始日期，ISO 格式（如 2026-07-01）；按 `started_at__gte` 过滤 |
| end_date | string | 否 | 结束日期，ISO 格式（如 2026-07-13）；按 `started_at__lt`（含 +1 天）过滤，非法值静默忽略 |
| run_id | string | 否 | 运行 ID，部分匹配（icontains） |
| task_name | string | 否 | 任务名，关联 TaskCard.name 部分匹配（icontains） |
| device_serial | string | 否 | 设备序列号，部分匹配（icontains） |
| creator | string | 否 | 创建者，关联 TaskCard.creator 部分匹配（icontains） |
| chart_range | string | 否 | 趋势图窗口天数，仅接受 7/30/90，默认 30；非法值回退 30 |

### 成功响应（200）

```json
{
  "status": true,                             # 请求是否成功，恒为 true
  "summary": {                                # KPI 汇总（对过滤后的 runs 聚合）
    "total_runs": 12,                         # 运行总数
    "total_iterations": 480,                  # 总迭代数（pass + fail）
    "total_pass": 460,                        # 总通过数
    "total_fail": 20,                         # 总失败数
    "pass_rate": 95.8                         # 总通过率（%），无迭代时为 0.0
  },
  "bug_summary": {                            # 缺陷汇总（已剔除 cases 明细，仅保留 3 个汇总值）
    "unique_issues": 3,                       # 去重后的缺陷种类数
    "total_occurrences": 8,                   # 缺陷总出现次数
    "affected_cases": 2                       # 受影响的用例数
  },
  "trend": {                                  # 每日趋势（按 chart_range 补零填充）
    "range_days": 30,                         # 实际使用的窗口天数
    "dates": ["2026-07-14", "..."],           # 每个日期的 ISO 字符串数组
    "labels": ["07-14", "..."],               # 每个日期的 MM-DD 标签数组
    "pass": [10, 12],                         # 每日通过数数组
    "fail": [0, 1],                           # 每日失败数数组
    "rate": [100.0, 92.3]                     # 每日通过率数组（%）
  },
  "runs": [                                   # 运行列表（按 id 倒序）
    {
      "run_id": "run_20260713001",            # 运行 ID
      "status": "completed",                  # 运行状态（透传 DB 原始值）
      "device_serial": "emulator-5554",       # 设备序列号
      "loop_count": 40,                       # 计划轮次（有 TaskCard 时取 tc.loop_count）
      "case_count": 12,                       # 用例数（取 TaskCard.case_ids 长度或 selected_cases 长度）
      "total": 480,                           # 总迭代数
      "passed": 460,                          # 通过数
      "failed": 20,                           # 失败数
      "rate": 96,                             # 通过率（%，取整）
      "duration": "25m30s",                   # 耗时（人类可读，如 45s / 2m30s，缺起止时间为空串）
      "started_at": "2026-07-13T10:00:00",    # 开始时间（ISO 字符串）
      "finished_at": "2026-07-13T10:25:30",   # 结束时间（ISO 字符串）
      "client_task_id": "task_001",           # 关联任务卡 ID（无则为空串 ""）
      "task_name": "冰箱制冷用例",             # 任务名（无 TaskCard 时为 null）
      "creator": "admin",                     # 创建者用户名（数字 ID 已解析为用户名；无 TaskCard 时为 null）
      "outcome": "completed"                  # 任务结局（无 TaskCard 时为 null）
    }
  ]
}
```

### 错误码与文案

| HTTP | message | 触发条件 |
|---|---|---|
| 401 | 请先登录 / 登录已过期或令牌无效 | 见「通用错误」 |

> 本端点无业务失败分支，过滤条件非法（如 end_date 解析失败、chart_range 非法）均静默回退，不返回错误。

---

## 4. 用例分解接口：GET /api/reports/cases

| 项 | 值 |
|---|---|
| 鉴权 | 需登录(Bearer) |
| 方法 | GET |
| 信封 | legacy 平铺 `{status, ...}` |

### 查询参数

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| result | string | **是** | 分解口径，仅接受 `pass` 或 `fail`（不区分大小写） |
| start_date | string | 否 | 同「报告列表接口」 |
| end_date | string | 否 | 同「报告列表接口」 |
| run_id | string | 否 | 同「报告列表接口」 |
| task_name | string | 否 | 同「报告列表接口」 |
| device_serial | string | 否 | 同「报告列表接口」 |
| creator | string | 否 | 同「报告列表接口」 |

### 成功响应（200，result=fail 时多出 bug_summary）

```json
{
  "status": true,                             # 请求是否成功，恒为 true
  "result_type": "fail",                      # 本次分解口径（pass / fail）
  "total": 20,                                # 该口径下总计数（fail 时为失败总数）
  "case_count": 2,                            # 命中用例数（groups 长度）
  "groups": [                                 # 按用例聚合的分组（按 case_title 排序）
    {
      "case_title": "制冰机出冰用例",          # 用例标题
      "case_id": "case_001",                  # 用例 ID
      "count": 12,                            # 该用例在本口径下的计数
      "tasks": [                              # 该用例下关联的任务（按 task_id 排序）
        {
          "task_id": "task_001",              # 任务 ID
          "task_name": "制冰机回归",           # 任务名（无 TaskCard 时退化为 task_id）
          "run_id": "run_20260713001",        # 运行 ID
          "count": 12,                        # 该任务下该用例的计数
          "failed_steps": [                   # 失败步骤明细（仅 result=fail 时存在；result=pass 时该字段被移除）
            {
              "caseTitle": "制冰机出冰用例",    # 用例标题
              "caseId": "case_001",            # 用例 ID
              "iteration": 1,                  # 轮次
              "stepIndex": 3,                  # 步骤序号（无明细回退时为 -1）
              "stepType": "assert",            # 步骤类型（无明细回退时为 "iteration"）
              "description": "断言失败",        # 步骤/失败描述
              "result": "fail"                 # 结果
            }
          ]
        }
      ]
    }
  ],
  "bug_summary": {                            # 缺陷汇总（仅 result=fail 时返回）
    "unique_issues": 3,                       # 去重后的缺陷种类数
    "total_occurrences": 8,                   # 缺陷总出现次数
    "affected_cases": 2,                      # 受影响的用例数
    "cases": [                                # 按用例聚合的缺陷明细
      {
        "case_title": "制冰机出冰用例",        # 用例标题
        "case_id": "case_001",                # 用例 ID
        "issue_count": 2,                     # 该用例去重后缺陷种类数
        "total_occurrences": 5,               # 该用例缺陷总出现次数
        "issues": [                           # 去重合并后的缺陷列表（按 count 降序、description 升序）
          {
            "step_type": "assert",            # 步骤类型
            "description": "断言失败",         # 缺陷描述
            "result": "fail",                 # 结果
            "count": 3,                       # 该缺陷出现次数
            "task_count": 2,                  # 涉及任务数
            "task_ids": ["task_001", "task_002"] # 涉及的任务 ID 列表
          }
        ]
      }
    ]
  }
}
```

### 错误码与文案

| HTTP | message | 触发条件 |
|---|---|---|
| 400 | result 必须为 pass 或 fail | `result` 缺失或不是 pass/fail |
| 401 | 请先登录 / 登录已过期或令牌无效 | 见「通用错误」 |

---

## 5. 运行报告接口：GET /api/reports/run/{run_id}

| 项 | 值 |
|---|---|
| 鉴权 | 需登录(Bearer) |
| 方法 | GET |
| 信封 | legacy 平铺 `{status, ...}` |

### 路径参数

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| run_id | string | 是 | 运行 ID（`TestRunRecord.run_id`） |

### 成功响应（200）

```json
{
  "status": true,                             # 请求是否成功，恒为 true
  "run": {                                    # 运行报告主体
    "run_id": "run_20260713001",              # 运行 ID
    "status": "completed",                    # 运行状态（透传 DB 原始值）
    "device_serial": "emulator-5554",         # 设备序列号
    "loop_count": 40,                         # 计划轮次
    "selected_cases": [                       # 执行前用例快照（数组）
      {"case_id": "case_001", "title": "制冰机出冰用例"}
    ],
    "started_at": "2026-07-13T10:00:00",      # 开始时间
    "finished_at": "2026-07-13T10:25:30",     # 结束时间
    "duration": "25m30s",                     # 耗时（人类可读，缺起止时间为空串）
    "total_iterations": 480,                  # 总迭代数（pass + fail）
    "total_pass": 460,                        # 总通过数
    "total_fail": 20,                         # 总失败数
    "pass_rate": 95.8,                        # 通过率（%）
    "case_count": 12,                         # 用例数（cases 长度）
    "cases": [                                # 用例级聚合（失败优先，再按 case_id 排序）
      {
        "case_id": "case_001",                # 用例 ID
        "case_title": "制冰机出冰用例",        # 用例标题
        "planned": 40,                        # 计划轮次（TaskCard.loop_count 或 run.loop_count）
        "actual": 40,                         # 实际执行轮次（pass + fail）
        "pass": 38,                           # 通过轮次
        "fail": 2,                            # 失败轮次
        "rate": 95,                           # 该用例通过率（%）
        "iterations": [                       # 逐轮明细
          {
            "iteration": 1,                   # 轮次
            "result": "pass",                 # 结果
            "duration_ms": 1200.5,            # 耗时（毫秒，保留 1 位；无值为 0）
            "detail": ""                      # 详情（失败时含错误信息）
          }
        ]
      }
    ],
    "recent_runs": [                          # 最近 10 次运行趋势（按 id 倒序取 10 后反转为时间正序）
      {
        "run_id": "run_20260712001",          # 运行 ID
        "started_at": "2026-07-12T09:00:00",  # 开始时间
        "total": 400,                         # 总迭代数
        "passed": 380,                        # 通过数
        "failed": 20,                         # 失败数
        "rate": 95                            # 通过率（%）
      }
    ],
    "client_task_id": "task_001",             # 关联任务卡 ID（无则为空串 ""）
    "task_name": "冰箱制冷用例",              # 任务名（无 TaskCard 时为 null）
    "task_creator": "admin",                  # 创建者用户名（数字 ID 已解析；无 TaskCard 时为 null）
    "task_outcome": "completed",              # 任务结局（无 TaskCard 时为 null）
    "task_conclusion": "回归通过",             # 任务结论（无 TaskCard 时为 null）
    "task_bug_ticket": "BUG-001",             # 缺陷单号（无 TaskCard 时为 null）
    "task_failed_steps": [                    # 任务级失败步骤明细（无 TaskCard 时为 null）
      {"caseTitle": "制冰机出冰用例", "iteration": 1, "stepIndex": 3, "stepType": "assert", "description": "断言失败", "result": "fail"}
    ],
    "task_round": 1,                          # 任务轮次（无 TaskCard 时为 null）
    "step_details": [                         # 步骤级执行明细（含截图，逐条补充 caseId/caseTitle/_date）
      {
        "caseId": "case_001",                 # 用例 ID（本 App 补齐）
        "caseTitle": "制冰机出冰用例",         # 用例标题（本 App 补齐）
        "_date": "2026-07-13 10:00:01"        # 落库时间（本 App 补齐，取 created_at 前 19 位）
      }
    ]
  }
}
```

### 错误码与文案

| HTTP | message | 触发条件 |
|---|---|---|
| 404 | run not found | `run_id` 对应的 `TestRunRecord` 不存在 |
| 401 | 请先登录 / 登录已过期或令牌无效 | 见「通用错误」 |

---

## 6. 任务报告接口：GET /api/reports/task/{task_id}

| 项 | 值 |
|---|---|
| 鉴权 | 需登录(Bearer) |
| 方法 | GET |
| 信封 | legacy 平铺 `{status, ...}` |

### 路径参数

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| task_id | string | 是 | 任务卡 ID（`TaskCard.task_id`） |

### 成功响应（200）

```json
{
  "status": true,                             # 请求是否成功，恒为 true
  "task": {                                   # 任务报告主体
    "task_id": "task_001",                    # 任务 ID
    "name": "制冰机回归",                     # 任务名
    "creator": "admin",                       # 创建者用户名（数字 ID 已解析）
    "mode": "scheduled",                      # 执行模式
    "device_serial": "emulator-5554",         # 设备序列号
    "loop_count": 40,                         # 计划轮次
    "interval_seconds": 5,                    # 轮次间隔（秒）
    "status": "done",                         # 任务状态
    "outcome": "completed",                   # 任务结局
    "round": 1,                               # 任务轮次
    "conclusion": "回归通过",                 # 任务结论
    "bug_ticket": "BUG-001",                  # 缺陷单号
    "failed_steps": [                         # 失败步骤明细
      {"caseTitle": "制冰机出冰用例", "iteration": 1, "stepIndex": 3, "stepType": "assert", "description": "断言失败", "result": "fail"}
    ],
    "case_ids": ["case_001"],                 # 关联用例 ID 列表
    "case_items": [                           # 用例聚合明细
      {
        "id": "case_001",                     # 用例 ID
        "title": "制冰机出冰用例",            # 用例标题
        "pass": 38,                           # 通过轮次
        "fail": 2                             # 失败轮次
      }
    ],
    "overall_pass": 460,                      # 总通过数
    "overall_fail": 20,                       # 总失败数
    "pass_rate": 95.8,                        # 通过率（%），无迭代时为 0.0
    "created_at": "2026-07-13 09:00:00",      # 任务创建时间（字符串化）
    "updated_at": "2026-07-13 10:25:30",      # 任务更新时间（字符串化）
    "linked_runs": [                          # 关联运行摘要（最近 10 次，按 id 倒序）
      {
        "run_id": "run_20260713001",          # 运行 ID
        "status": "completed",                # 运行状态
        "device_serial": "emulator-5554",     # 设备序列号
        "loop_count": 40,                     # 计划轮次
        "total": 480,                         # 总迭代数
        "passed": 460,                        # 通过数
        "failed": 20,                         # 失败数
        "rate": 96,                           # 通过率（%）
        "started_at": "2026-07-13T10:00:00",  # 开始时间
        "finished_at": "2026-07-13T10:25:30", # 结束时间
        "duration": "25m30s"                  # 耗时（人类可读）
      }
    ],
    "step_details": [                         # 步骤级执行明细（含截图，逐条补充 caseId/caseTitle/_date）
      {
        "caseId": "case_001",                 # 用例 ID（本 App 补齐）
        "caseTitle": "制冰机出冰用例",         # 用例标题（本 App 补齐）
        "_date": "2026-07-13 10:00:01"        # 落库时间（本 App 补齐）
      }
    ]
  }
}
```

### 错误码与文案

| HTTP | message | 触发条件 |
|---|---|---|
| 404 | task not found | `task_id` 对应的 `TaskCard` 不存在 |
| 401 | 请先登录 / 登录已过期或令牌无效 | 见「通用错误」 |

---

## 7. 报告内容查看接口：GET /api/reports/{filename}/content

| 项 | 值 |
|---|---|
| 鉴权 | 需登录(Bearer) |
| 方法 | GET |
| 信封 | legacy 平铺 `{status, ...}`（JSON；本端点不是 FileResponse） |

### 路径参数

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| filename | string | 是 | 报告文件名；经 `Path(filename).name` 取 basename（防路径穿越），在 `LOG_DIR` 下查找 |

### 成功响应（200）

```json
{
  "status": true,                             # 请求是否成功，恒为 true
  "name": "制冰机出冰用例.csv",               # 实际文件名（basename，非 JSON 转义后）
  "type": "csv",                              # 文件类型：csv / md / log（按扩展名判定，其余为 log）
  "size": 2048,                               # 文件大小（字节）
  "content": "用例名称,测试步骤,计划轮次,实际执行,通过,失败,成功率,时间\n...", # 文件原始文本（utf-8-sig → utf-8 → latin-1 逐级回退解码）
  "rows": [                                   # CSV 解析行（仅 .csv 时非空；md/log 为空数组）
    {"用例名称": "制冰机出冰用例", "通过": "38"}
  ],
  "headers": ["用例名称", "测试步骤", "计划轮次", "实际执行", "通过", "失败", "成功率", "时间"] # CSV 表头（仅 .csv 时非空）
}
```

> `rows` 仅在 `.csv` 且列数与表头一致时逐行映射为对象；`headers` 取 `content` 首行按逗号切分（仅 `.csv`）。

### 错误码与文案

| HTTP | message | 触发条件 |
|---|---|---|
| 404 | not found | `LOG_DIR` 下不存在该文件 |
| 401 | 请先登录 / 登录已过期或令牌无效 | 见「通用错误」 |

---

## 8. 报告下载接口：GET /api/reports/{filename}

| 项 | 值 |
|---|---|
| 鉴权 | 需登录(Bearer) |
| 方法 | GET |
| 响应 | **FileResponse（非 JSON）**，前端用 `fetch().text()` 消费 |

### 路径参数

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| filename | string | 是 | 报告文件名；经 `Path(filename).name` 取 basename（防路径穿越），在 `LOG_DIR` 下查找 |

### 成功响应（200，文件流）

- `Content-Type`：按扩展名判定 —— `.csv` → `text/csv`；`.md` → `text/markdown`；其余 → `text/plain`。
- `Content-Disposition`: `attachment; filename="<safe_name>"`（触发浏览器下载）。
- 响应体为文件原始字节流，**不是 JSON 信封**，改形状前端解析即崩。

### 错误码与文案

| HTTP | message | 触发条件 |
|---|---|---|
| 404 | not found | `LOG_DIR` 下不存在该文件（此时返回 JSON，非文件流） |
| 401 | 请先登录 / 登录已过期或令牌无效 | 见「通用错误」 |

> 下载端点仅成功时为 FileResponse；文件不存在时回退为 JSON `{"status": false, "message": "not found"}`。

---

## 9. 附：本 App 相关模型（只读查询来源，无写）

| 模型 | 表 | 用途 |
|---|---|---|
| `Report` | `rg_reports` | 报告记录（本模块自身 ORM，6 个端点未直接读取） |
| `ReportTemplate` | `rg_report_templates` | 报告模板（本模块自身 ORM，6 个端点未直接读取） |

> 6 个端点均不读写 `rg_reports` / `rg_report_templates`；数据来自跨 App 只读查询 `apps.test_runner.models.TestRunRecord` / `TestResult` / `TaskCard` 与 `LOG_DIR` 文件。
