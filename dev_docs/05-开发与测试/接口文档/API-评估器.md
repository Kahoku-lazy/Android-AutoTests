# API-评估器 — /api/evaluator/*

> 评估器域全集 **29 个可达端点**：DRF router 15 个（题库 banks / 评估运行 runs / 评估结果 results，信封 `{status,data}`）+ legacy 平铺 14 个（信封 `{status, banks|runs|...}`）。
> 真相源：`apps/evaluator/urls.py` + `views.py`（legacy 平铺）+ `views_api.py`（DRF ViewSet）+ `serializers.py` + `models.py` + `api.py`。
> 说明：`apps/evaluator/AGENTS.md` 中「14 端点」仅指 legacy 平铺集合，不含 DRF router 自动生成的 15 个标准端点。

## 1. 总览

| 接口 | 方法 | 鉴权 | 说明 |
|---|---|---|---|
| 题库列表接口（DRF） | GET /api/evaluator/banks/ | 需登录(Bearer) | 题库列表（含嵌套题目） |
| 创建题库接口（DRF） | POST /api/evaluator/banks/ | 需登录(Bearer) | 创建题库（含嵌套题目） |
| 题库详情接口（DRF） | GET /api/evaluator/banks/{id}/ | 需登录(Bearer) | 单题库详情（含嵌套题目） |
| 更新题库接口（DRF） | PUT /api/evaluator/banks/{id}/ | 需登录(Bearer) | 全量更新题库 |
| 部分更新题库接口（DRF） | PATCH /api/evaluator/banks/{id}/ | 需登录(Bearer) | 部分更新题库 |
| 删除题库接口（DRF） | DELETE /api/evaluator/banks/{id}/ | 需登录(Bearer) | 删除题库（级联删题） |
| 初始化默认题库接口（DRF） | POST /api/evaluator/banks/seed/ | 需登录(Bearer) | 创建默认 30 题试卷（幂等） |
| 运行列表接口（DRF） | GET /api/evaluator/runs/ | 需登录(Bearer) | 评估运行摘要列表（最多 50 条） |
| 创建运行接口（DRF） | POST /api/evaluator/runs/ | 需登录(Bearer) | 默认 create，落库不触发评估（非主流程） |
| 运行详情接口（DRF） | GET /api/evaluator/runs/{id}/ | 需登录(Bearer) | 单次运行详情（含逐题结果） |
| 删除运行接口（DRF） | DELETE /api/evaluator/runs/{id}/ | 需登录(Bearer) | 删除评估运行 |
| 启动评测接口（DRF） | POST /api/evaluator/runs/start/ | 需登录(Bearer) | 启动一次后台评估运行 |
| 结果列表接口（DRF） | GET /api/evaluator/results/ | 需登录(Bearer) | 逐题评分结果列表（只读） |
| 结果详情接口（DRF） | GET /api/evaluator/results/{id}/ | 需登录(Bearer) | 单条评分结果详情（只读） |
| 人工评分接口（DRF） | POST /api/evaluator/results/{id}/score/ | 需登录(Bearer) | 提交人工评分 |
| 题库列表接口（legacy） | GET /api/evaluator/banks | 需登录(Bearer) | 题库列表（平铺信封） |
| 创建题库接口（legacy） | POST /api/evaluator/banks/create | 需登录(Bearer) | 创建题库（平铺信封） |
| 初始化默认题库接口（legacy） | POST /api/evaluator/banks/seed | 需登录(Bearer) | 创建默认 30 题试卷（平铺信封） |
| 题库详情接口（legacy） | GET /api/evaluator/banks/{id} | 需登录(Bearer) | 单题库详情（平铺信封） |
| 更新题库接口（legacy） | POST /api/evaluator/banks/{id}/update | 需登录(Bearer) | 更新题库（平铺信封） |
| 删除题库接口（legacy） | POST /api/evaluator/banks/{id}/delete | 需登录(Bearer) | 删除题库（POST 触发，平铺信封） |
| 运行列表接口（legacy） | GET /api/evaluator/runs | 需登录(Bearer) | 运行摘要列表（平铺信封） |
| 启动评测接口（legacy） | POST /api/evaluator/runs/start | 需登录(Bearer) | 启动后台评估（平铺信封） |
| 运行详情接口（legacy） | GET /api/evaluator/runs/{id} | 需登录(Bearer) | 运行详情含逐题结果（平铺信封） |
| 删除运行接口（legacy） | POST /api/evaluator/runs/{id}/delete | 需登录(Bearer) | 删除运行（POST 触发，平铺信封） |
| 人工评分接口（legacy） | POST /api/evaluator/results/{id}/score | 需登录(Bearer) | 提交人工评分（平铺信封） |
| 框架列表接口 | GET /api/evaluator/frameworks | 需登录(Bearer) | 可用评估框架列表（平铺信封） |
| KB 检索接口 | POST /api/evaluator/kb-search | 需登录(Bearer) | 知识库检索测试（平铺信封） |
| KB 自测接口 | POST /api/evaluator/kb-self-test | 需登录(Bearer) | 知识库检索质量自测（平铺信封） |

## 2. 通用约定

- **基础路径**：`/api/evaluator/`（`config/urls.py` 第 31 行 `include("apps.evaluator.urls")`）。
- **尾斜杠**：DRF router 端点**带尾斜杠**（`/banks/`、`/runs/start/`）；legacy 平铺端点**不带尾斜杠**（`/banks`、`/runs/start`）。网关 `NormalizeTrailingSlashMiddleware` 会规范化尾斜杠，但本文以 urls.py 注册路径为准。
- **鉴权**：本模块**全部端点均需登录**。`/api/evaluator/*` 不在网关 `PUBLIC_PREFIXES` 白名单内，`JWTAuthenticationMiddleware` 对 `/api/*` 全局拦截；DRF ViewSet 另设 `IsAuthenticated`；部分 legacy 视图再加 `@require_auth` 防御性二次校验。携带 `Authorization: Bearer <access_token>`。
- **鉴权失败文案（网关层，gateway/middleware.py）**：无/格式错 Bearer → 401 `"请先登录"`；令牌无效或过期 → 401 `"登录已过期或令牌无效"`。
- **信封双口径**（区分要点）：
  - DRF router 端点：成功 `{status: true, data}`，失败 `{status: false, message}`（`EnvelopeJSONRenderer` 统一包裹）。
  - legacy 平铺端点：成功 `{status: true, banks|runs|run|bank|frameworks|...}`，失败 `{status: false, message}`（`JsonResponse` 平铺，无 `data` 包裹）。
- **字段命名**：snake_case。
- **评分维度**：relevance（相关性）/ accuracy（准确性）/ completeness（完整性）/ conciseness（简洁性），机器判卷 LLM 1–5 分；`effective_*` 口径为「人工分优先，缺省回落到机器分」（见 `EvalResult.effective_scores()`）。
- **运行状态**：`pending`（等待中）/ `running`（评测中）/ `completed`（已完成）/ `failed`（失败）。评估是后台线程任务（`_bg()` + `evaluator.run_evaluation` 判卷 LLM），进度经 **HTTP 轮询**（无 WS/SSE）。
- **无文件下载端点**：本模块无 FileResponse，全部返回 JSON。

---

## 3. 题库 DRF 端点（QuestionBankViewSet）

### 3.1 题库列表接口：GET /api/evaluator/banks/

| 项 | 值 |
|---|---|
| 鉴权 | 需登录(Bearer) |
| 查询参数 | 无 |

**成功响应（200）** — `data` 为题库数组，每项含嵌套 `questions`：

```json
{
  "status": true,                              # 请求是否成功，恒为 true
  "data": [
    {
      "id": 1,                                 # 题库 ID
      "name": "默认30题试卷",                    # 试卷名称
      "description": "内置 30 道评测问题",        # 描述
      "questions": [                           # 嵌套题目列表
        {
          "id": 1,                             # 题目 ID
          "content": "如何创建测试用例",          # 题干
          "expected_keywords": "用例,设计",       # 期望关键词（逗号分隔）
          "category": "平台功能",                # 类别
          "order": 0                           # 排序号
        }
      ],
      "question_count": 30,                    # 题目数（只读属性计算）
      "created_at": "2026-08-21T10:00:00",     # 创建时间
      "updated_at": "2026-08-21T10:00:00"      # 更新时间
    }
  ]
}
```

### 3.2 创建题库接口：POST /api/evaluator/banks/

| 项 | 值 |
|---|---|
| 鉴权 | 需登录(Bearer) |
| Content-Type | application/json |

**请求体字段**

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| name | string | 是 | 试卷名称（非空，≤200 字符） |
| description | string | 否 | 描述（可空） |
| questions | array | 是 | 嵌套题目列表（DRF 嵌套序列化默认必填） |
| questions[].content | string | 是 | 题干 |
| questions[].expected_keywords | string | 否 | 期望关键词（逗号分隔） |
| questions[].category | string | 否 | 类别（默认 "general"） |
| questions[].order | integer | 否 | 排序号（缺省按数组下标） |

**成功响应（201）** — `data` 为创建后的完整题库对象（同 3.1 单元素结构）。

**错误码与文案（校验顺序即优先级）**

| HTTP | message | 触发条件 |
|---|---|---|
| 400 | 该字段是必填项。 | name / questions 缺失（DRF 默认字段校验文案） |
| 400 | 该字段不能为空。 | name 为空串（DRF 默认字段校验文案） |

> 说明：字段级校验错误由 DRF 默认产生，`EnvelopeJSONRenderer` 取首个字段的首条错误作为 `message`；不同 locale 下文案可能不同。

### 3.3 题库详情接口：GET /api/evaluator/banks/{id}/

| 项 | 值 |
|---|---|
| 鉴权 | 需登录(Bearer) |
| 路径参数 | id — 题库 ID |

**成功响应（200）** — `data` 为单题库对象（同 3.1 单元素结构）。

**错误码与文案**

| HTTP | message | 触发条件 |
|---|---|---|
| 404 | 未找到。 | 题库不存在（DRF 默认 `Http404` 文案） |

### 3.4 更新题库接口：PUT /api/evaluator/banks/{id}/

| 项 | 值 |
|---|---|
| 鉴权 | 需登录(Bearer) |
| Content-Type | application/json |
| 路径参数 | id — 题库 ID |

**请求体字段** — 同 3.2 创建；`questions` 为**全量替换**（删除原题后按载荷重建，缺失则 400）。

**成功响应（200）** — `data` 为更新后的完整题库对象。

**错误码与文案** — 同 3.2 字段校验 + 404「未找到。」（题库不存在）。

### 3.5 部分更新题库接口：PATCH /api/evaluator/banks/{id}/

| 项 | 值 |
|---|---|
| 鉴权 | 需登录(Bearer) |
| Content-Type | application/json |
| 路径参数 | id — 题库 ID |

**请求体字段** — 同 3.2 但**全部可选**；仅传 `name`/`description` 时只改这两项；传 `questions` 时全量替换题目（不传则保持原题不变）。

**成功响应（200）** — `data` 为更新后的完整题库对象。

**错误码与文案** — 同 3.4。

### 3.6 删除题库接口：DELETE /api/evaluator/banks/{id}/

| 项 | 值 |
|---|---|
| 鉴权 | 需登录(Bearer) |
| 路径参数 | id — 题库 ID |

**成功响应（204）** — 无响应体；信封等价 `{"status": true, "data": null}`。级联删除题目。

**错误码与文案**

| HTTP | message | 触发条件 |
|---|---|---|
| 404 | 未找到。 | 题库不存在 |

### 3.7 初始化默认题库接口：POST /api/evaluator/banks/seed/

| 项 | 值 |
|---|---|
| 鉴权 | 需登录(Bearer) |
| Content-Type | application/json |
| 请求体 | 无（`{}`） |

**成功响应（200）** — 幂等：已存在返回 `message`，新建返回 `question_count`：

```json
{
  "status": true,                             # 请求是否成功，恒为 true
  "data": {
    "id": 1,                                  # 默认试卷 ID
    "question_count": 30                       # 题目数（新建时返回）
  }
}
```

已存在时 `data` 为 `{"id": 1, "message": "默认试卷已存在，直接返回"}`（无 `question_count`）。

---

## 4. 评估运行 DRF 端点（EvalRunViewSet）

> `http_method_names = ["get","post","delete","head","options"]`：**PUT / PATCH 已禁用**（`/runs/{id}/` 的 update/partial_update 返回 405）。

### 4.1 运行列表接口：GET /api/evaluator/runs/

| 项 | 值 |
|---|---|
| 鉴权 | 需登录(Bearer) |

**成功响应（200）** — `data` 为摘要数组（无嵌套 results，最多 50 条）：

```json
{
  "status": true,                              # 请求是否成功，恒为 true
  "data": [
    {
      "id": 1,                                 # 运行 ID
      "agent_id": 3,                           # 被评估 Agent ID
      "agent_name": "测试助手",                 # Agent 名称（不存在时为 "?"）
      "bank_id": 1,                            # 题库 ID
      "bank_name": "默认30题试卷",              # 题库名称（不存在时为 "?"）
      "framework": "self",                     # 框架：self/evalscope/deepeval/maseval
      "status": "running",                     # 状态：pending/running/completed/failed
      "total_questions": 30,                   # 题目总数
      "completed_questions": 12,               # 已完成题目数
      "total_score": 0.0,                      # 综合总分（1-5）
      "avg_relevance": 0.0,                    # 相关性均分
      "avg_accuracy": 0.0,                     # 准确性均分
      "avg_completeness": 0.0,                 # 完整性均分
      "avg_conciseness": 0.0,                  # 简洁性均分
      "created_at": "2026-08-21T10:00:00",     # 创建时间
      "finished_at": null                      # 完成时间（未完成时为 null）
    }
  ]
}
```

### 4.2 创建运行接口：POST /api/evaluator/runs/

| 项 | 值 |
|---|---|
| 鉴权 | 需登录(Bearer) |
| Content-Type | application/json |

> 说明：这是 ModelViewSet 自动生成的 create（因 `http_method_names` 含 post 而暴露），**仅落库一条 EvalRun 记录，不触发评估**。正常启动评估请用 `POST /runs/start/`（4.5）。

**请求体字段**（可写字段，均非必填）

| 字段 | 类型 | 说明 |
|---|---|---|
| agent_id | integer | 被评估 Agent ID |
| bank_id | integer | 题库 ID |
| framework | string | 框架（默认 "self"） |
| status | string | 状态（默认 "pending"） |
| judge_provider | string | 判卷 LLM 提供商（默认 "dashscope"） |
| judge_model | string | 判卷模型（默认 "qwen-max"） |

**成功响应（201）** — `data` 为创建的运行对象（含 `id` 等全部字段）。

### 4.3 运行详情接口：GET /api/evaluator/runs/{id}/

| 项 | 值 |
|---|---|
| 鉴权 | 需登录(Bearer) |
| 路径参数 | id — 运行 ID |

**成功响应（200）** — `data` 为单运行对象，比列表多 `judge_provider`/`judge_model`/`report_json` 与嵌套 `results`（逐题结果字段见 5.1）：

```json
{
  "status": true,                              # 请求是否成功，恒为 true
  "data": {
    "id": 1,                                   # 运行 ID
    "agent_id": 3,                             # 被评估 Agent ID
    "agent_name": "测试助手",                   # Agent 名称
    "bank_id": 1,                              # 题库 ID
    "bank_name": "默认30题试卷",                # 题库名称
    "framework": "self",                       # 评估框架
    "status": "completed",                     # 运行状态
    "total_questions": 30,                     # 题目总数
    "completed_questions": 30,                 # 已完成题目数
    "total_score": 4.25,                       # 综合总分
    "avg_relevance": 4.3,                      # 相关性均分
    "avg_accuracy": 4.1,                       # 准确性均分
    "avg_completeness": 4.4,                   # 完整性均分
    "avg_conciseness": 4.2,                    # 简洁性均分
    "judge_provider": "dashscope",             # 判卷 LLM 提供商
    "judge_model": "qwen-max",                 # 判卷模型
    "report_json": "{"framework":"self",...}", # 完整报告（JSON 字符串）
    "created_at": "2026-08-21T10:00:00",       # 创建时间
    "finished_at": "2026-08-21T10:05:00",      # 完成时间
    "results": [                              # 逐题结果（字段见 5.1）
      {
        "id": 1,
        "question_id": 1,
        "question_text": "如何创建测试用例",
        "agent_response": "……",
        "relevance_score": 4.5,
        "accuracy_score": 4.0,
        "completeness_score": 4.5,
        "conciseness_score": 4.0,
        "human_relevance": null,
        "human_accuracy": null,
        "human_completeness": null,
        "human_conciseness": null,
        "human_note": "",
        "effective_relevance": 4.5,
        "effective_accuracy": 4.0,
        "effective_completeness": 4.5,
        "effective_conciseness": 4.0,
        "judge_reasoning": "……"
      }
    ]
  }
}
```

**错误码与文案**

| HTTP | message | 触发条件 |
|---|---|---|
| 404 | 未找到。 | 运行不存在 |

### 4.4 删除运行接口：DELETE /api/evaluator/runs/{id}/

| 项 | 值 |
|---|---|
| 鉴权 | 需登录(Bearer) |
| 路径参数 | id — 运行 ID |

**成功响应（204）** — 无响应体（级联删除逐题结果）。

**错误码与文案**

| HTTP | message | 触发条件 |
|---|---|---|
| 404 | 未找到。 | 运行不存在 |

### 4.5 启动评测接口：POST /api/evaluator/runs/start/

| 项 | 值 |
|---|---|
| 鉴权 | 需登录(Bearer) |
| Content-Type | application/json |

**请求体字段**

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| agent_id | integer | 是 | 被评估 Agent ID |
| bank_id | integer | 是 | 题库 ID |
| framework | string | 否 | 框架，默认 "self"（self/evalscope/deepeval/maseval） |
| judge_provider | string | 否 | 判卷 LLM 提供商，默认 "dashscope" |
| judge_model | string | 否 | 判卷模型，默认 "qwen-max" |

**成功响应（200）**

```json
{
  "status": true,                              # 请求是否成功，恒为 true
  "data": {
    "run": {
      "id": 1                                  # 新建运行 ID
    },
    "message": "评测已开始，共 30 题"             # 提示文案（N 为题量）
  }
}
```

> 启动后立即返回，评估在**后台线程**异步执行；状态经 `GET /runs/{id}/` 或 `GET /runs/{id}` 轮询。

**错误码与文案（校验顺序即优先级）**

| HTTP | message | 触发条件 |
|---|---|---|
| 400 | agent_id and bank_id are required | agent_id 或 bank_id 缺失 |
| 404 | agent not found | Agent 不存在 |
| 404 | question bank not found | 题库不存在 |

---

## 5. 评估结果 DRF 端点（EvalResultViewSet）

### 5.1 结果列表接口：GET /api/evaluator/results/

| 项 | 值 |
|---|---|
| 鉴权 | 需登录(Bearer) |

**成功响应（200）** — `data` 为逐题评分结果数组：

```json
{
  "status": true,                              # 请求是否成功，恒为 true
  "data": [
    {
      "id": 1,                                 # 结果 ID
      "question_id": 1,                        # 题目 ID
      "question_text": "如何创建测试用例",        # 题干文本
      "agent_response": "……",                  # Agent 作答内容
      "relevance_score": 4.5,                  # 机器相关性分（1-5）
      "accuracy_score": 4.0,                   # 机器准确性分（1-5）
      "completeness_score": 4.5,               # 机器完整性分（1-5）
      "conciseness_score": 4.0,                # 机器简洁性分（1-5）
      "human_relevance": null,                 # 人工相关性分（未评时为 null）
      "human_accuracy": null,                  # 人工准确性分
      "human_completeness": null,              # 人工完整性分
      "human_conciseness": null,               # 人工简洁性分
      "human_note": "",                        # 人工评分备注
      "effective_relevance": 4.5,              # 有效相关性分（人工优先，否则机器）
      "effective_accuracy": 4.0,               # 有效准确性分
      "effective_completeness": 4.5,           # 有效完整性分
      "effective_conciseness": 4.0,            # 有效简洁性分
      "judge_reasoning": "……"                  # 判卷 LLM 评分理由
    }
  ]
}
```

### 5.2 结果详情接口：GET /api/evaluator/results/{id}/

| 项 | 值 |
|---|---|
| 鉴权 | 需登录(Bearer) |
| 路径参数 | id — 结果 ID |

**成功响应（200）** — `data` 为单条结果对象（同 5.1 单元素结构）。

**错误码与文案**

| HTTP | message | 触发条件 |
|---|---|---|
| 404 | 未找到。 | 结果不存在 |

### 5.3 人工评分接口：POST /api/evaluator/results/{id}/score/

| 项 | 值 |
|---|---|
| 鉴权 | 需登录(Bearer) |
| Content-Type | application/json |
| 路径参数 | id — 结果 ID |

**请求体字段**（全部可选；仅传入的字段会被更新）

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| human_relevance | number | 否 | 人工相关性分（1-5） |
| human_accuracy | number | 否 | 人工准确性分（1-5） |
| human_completeness | number | 否 | 人工完整性分（1-5） |
| human_conciseness | number | 否 | 人工简洁性分（1-5） |
| human_note | string | 否 | 人工评分备注 |

**成功响应（200）**

```json
{
  "status": true,                              # 请求是否成功，恒为 true
  "data": {
    "result_id": 1,                            # 被评分的结果 ID
    "scored": true                             # 是否已评分，恒为 true
  }
}
```

> 提交后后端会重算所属运行的四个维度均分与 `total_score`。

**错误码与文案**

| HTTP | message | 触发条件 |
|---|---|---|
| 404 | 未找到。 | 结果不存在（`get_object()` 抛 404） |

---

## 6. Legacy 平铺端点（views.py，无尾斜杠）

> 以下端点均返回**平铺信封**（无 `data` 包裹），由旧前端 `evaluator-api.ts` 消费。方法取自行内文档与前端实际调用。

### 6.1 题库列表接口：GET /api/evaluator/banks

| 项 | 值 |
|---|---|
| 鉴权 | 需登录(Bearer) |

**成功响应（200）**

```json
{
  "status": true,                              # 请求是否成功，恒为 true
  "banks": [
    {
      "id": 1,                                 # 题库 ID
      "name": "默认30题试卷",                    # 试卷名称
      "description": "内置 30 道评测问题",        # 描述
      "question_count": 30,                    # 题目数
      "created_at": "2026-08-21 10:00:00"      # 创建时间（str 格式化）
    }
  ]
}
```

### 6.2 创建题库接口：POST /api/evaluator/banks/create

| 项 | 值 |
|---|---|
| 鉴权 | 需登录(Bearer) |
| Content-Type | application/json |

**请求体字段**

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| name | string | 是 | 试卷名称（strip 后非空） |
| description | string | 否 | 描述，默认 "" |
| questions | array | 否 | 题目列表，每项 `{content, expected_keywords, category, order}` |

**成功响应（200）**

```json
{
  "status": true,                              # 请求是否成功，恒为 true
  "id": 2,                                     # 新建题库 ID
  "question_count": 30                         # 题目数
}
```

**错误码与文案**

| HTTP | message | 触发条件 |
|---|---|---|
| 400 | 试卷名称不能为空 | name 缺失或 strip 后为空 |

> 说明：请求体须为合法 JSON，否则 `json.loads` 抛 JSONDecodeError（未捕获，返回 500）。

### 6.3 初始化默认题库接口：POST /api/evaluator/banks/seed

| 项 | 值 |
|---|---|
| 鉴权 | 需登录(Bearer) |

**成功响应（200）** — 新建：`{"status": true, "id": 1, "question_count": 30}`；已存在：`{"status": true, "id": 1, "message": "默认试卷已存在，直接返回"}`。

### 6.4 题库详情接口：GET /api/evaluator/banks/{id}

| 项 | 值 |
|---|---|
| 鉴权 | 需登录(Bearer) |
| 路径参数 | id — 题库 ID |

**成功响应（200）**

```json
{
  "status": true,                              # 请求是否成功，恒为 true
  "bank": {
    "id": 1,                                   # 题库 ID
    "name": "默认30题试卷",                      # 试卷名称
    "description": "内置 30 道评测问题",          # 描述
    "questions": [                             # 题目列表
      {
        "id": 1,                               # 题目 ID
        "content": "如何创建测试用例",            # 题干
        "expected_keywords": "用例,设计",         # 期望关键词
        "category": "平台功能",                  # 类别
        "order": 0                             # 排序号
      }
    ]
  }
}
```

**错误码与文案**

| HTTP | message | 触发条件 |
|---|---|---|
| 404 | not found | 题库不存在 |

### 6.5 更新题库接口：POST /api/evaluator/banks/{id}/update

| 项 | 值 |
|---|---|
| 鉴权 | 需登录(Bearer) |
| Content-Type | application/json |
| 路径参数 | id — 题库 ID |

**请求体字段**

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| name | string | 否 | 试卷名称 |
| description | string | 否 | 描述 |
| questions | array | 否 | 题目列表（提供则全量替换题目，`order` 按数组下标重排） |

**成功响应（200）**

```json
{
  "status": true,                              # 请求是否成功，恒为 true
  "question_count": 30                         # 更新后题目数
}
```

**错误码与文案**

| HTTP | message | 触发条件 |
|---|---|---|
| 404 | not found | 题库不存在 |

### 6.6 删除题库接口：POST /api/evaluator/banks/{id}/delete

| 项 | 值 |
|---|---|
| 鉴权 | 需登录(Bearer) |
| 路径参数 | id — 题库 ID |

> 说明：legacy 用 **POST** 触发删除（非 DELETE 方法），幂等（`filter().delete()`），题库不存在也返回成功。

**成功响应（200）**

```json
{
  "status": true                               # 请求是否成功，恒为 true
}
```

### 6.7 运行列表接口：GET /api/evaluator/runs

| 项 | 值 |
|---|---|
| 鉴权 | 需登录(Bearer) |

**成功响应（200）** — `runs` 为摘要数组（最多 50 条，字段同 4.1，但 `created_at` 为 str 格式化）：

```json
{
  "status": true,                              # 请求是否成功，恒为 true
  "runs": [
    {
      "id": 1,                                 # 运行 ID
      "agent_id": 3,                           # 被评估 Agent ID
      "agent_name": "测试助手",                 # Agent 名称（不存在时为 "?"）
      "framework": "self",                     # 评估框架
      "bank_id": 1,                            # 题库 ID
      "bank_name": "默认30题试卷",              # 题库名称（不存在时为 "?"）
      "status": "running",                     # 运行状态
      "total_questions": 30,                   # 题目总数
      "completed_questions": 12,               # 已完成题目数
      "total_score": 0.0,                      # 综合总分
      "avg_relevance": 0.0,                    # 相关性均分
      "avg_accuracy": 0.0,                     # 准确性均分
      "avg_completeness": 0.0,                 # 完整性均分
      "avg_conciseness": 0.0,                  # 简洁性均分
      "created_at": "2026-08-21 10:00:00",     # 创建时间
      "finished_at": null                      # 完成时间（未完成时为 null）
    }
  ]
}
```

### 6.8 启动评测接口：POST /api/evaluator/runs/start

| 项 | 值 |
|---|---|
| 鉴权 | 需登录(Bearer) |
| Content-Type | application/json |

**请求体字段** — 同 4.5（agent_id/bank_id 必填，framework/judge_provider/judge_model 可选）。

**成功响应（200）**

```json
{
  "status": true,                              # 请求是否成功，恒为 true
  "run": {
    "id": 1                                    # 新建运行 ID
  },
  "message": "评测已开始，共 30 题"               # 提示文案
}
```

**错误码与文案** — 同 4.5：400「agent_id and bank_id are required」、404「agent not found」、404「question bank not found」。

### 6.9 运行详情接口：GET /api/evaluator/runs/{id}

| 项 | 值 |
|---|---|
| 鉴权 | 需登录(Bearer) |
| 路径参数 | id — 运行 ID |

**成功响应（200）** — `run` 为运行对象，字段同 4.3，但 `results` 中 `question_text`/`agent_response`/`judge_reasoning` 被截断（分别 200/500/300 字符），`report_json` 为 JSON 字符串：

```json
{
  "status": true,                              # 请求是否成功，恒为 true
  "run": {
    "id": 1,                                   # 运行 ID
    "agent_id": 3,                             # 被评估 Agent ID
    "agent_name": "测试助手",                   # Agent 名称
    "framework": "self",                       # 评估框架
    "bank_name": "默认30题试卷",                # 题库名称
    "status": "completed",                     # 运行状态
    "total_questions": 30,                     # 题目总数
    "completed_questions": 30,                 # 已完成题目数
    "total_score": 4.25,                       # 综合总分
    "avg_relevance": 4.3,                      # 相关性均分
    "avg_accuracy": 4.1,                       # 准确性均分
    "avg_completeness": 4.4,                   # 完整性均分
    "avg_conciseness": 4.2,                    # 简洁性均分
    "report_json": "{"framework":"self",...}", # 完整报告（JSON 字符串）
    "created_at": "2026-08-21 10:00:00",       # 创建时间
    "finished_at": "2026-08-21 10:05:00",      # 完成时间
    "results": [                              # 逐题结果（字段同 5.1，含截断）
      {
        "id": 1,                               # 结果 ID
        "question_id": 1,                      # 题目 ID
        "question_text": "如何创建测试用例",      # 题干（截断至 200 字符）
        "agent_response": "……",                # 作答（截断至 500 字符）
        "relevance_score": 4.5,                # 机器相关性分
        "accuracy_score": 4.0,                 # 机器准确性分
        "completeness_score": 4.5,             # 机器完整性分
        "conciseness_score": 4.0,              # 机器简洁性分
        "human_relevance": null,               # 人工相关性分
        "human_accuracy": null,                # 人工准确性分
        "human_completeness": null,            # 人工完整性分
        "human_conciseness": null,             # 人工简洁性分
        "human_note": "",                      # 人工评分备注
        "effective_relevance": 4.5,            # 有效相关性分
        "effective_accuracy": 4.0,             # 有效准确性分
        "effective_completeness": 4.5,         # 有效完整性分
        "effective_conciseness": 4.0,          # 有效简洁性分
        "judge_reasoning": "……"                # 判卷理由（截断至 300 字符）
      }
    ]
  }
}
```

**错误码与文案**

| HTTP | message | 触发条件 |
|---|---|---|
| 404 | not found | 运行不存在 |

### 6.10 删除运行接口：POST /api/evaluator/runs/{id}/delete

| 项 | 值 |
|---|---|
| 鉴权 | 需登录(Bearer) |
| 路径参数 | id — 运行 ID |

> 说明：legacy 用 **POST** 触发删除，幂等（`filter().delete()`），不存在也返回成功。

**成功响应（200）** — `{"status": true}`。

### 6.11 人工评分接口：POST /api/evaluator/results/{id}/score

| 项 | 值 |
|---|---|
| 鉴权 | 需登录(Bearer) |
| Content-Type | application/json |
| 路径参数 | id — 结果 ID |

**请求体字段** — 同 5.3（human_relevance/human_accuracy/human_completeness/human_conciseness/human_note 全部可选）。

**成功响应（200）**

```json
{
  "status": true                               # 请求是否成功，恒为 true
}
```

**错误码与文案**

| HTTP | message | 触发条件 |
|---|---|---|
| 404 | not found | 结果不存在 |

### 6.12 框架列表接口：GET /api/evaluator/frameworks

| 项 | 值 |
|---|---|
| 鉴权 | 需登录(Bearer) |

**成功响应（200）**

```json
{
  "status": true,                              # 请求是否成功，恒为 true
  "frameworks": [
    {
      "key": "deepeval",                       # 框架注册键（用于 runs/start 的 framework 参数）
      "name": "DeepEval",                      # 框架显示名
      "description": "……",                     # 框架说明
      "available": false                       # 是否可用（依赖包是否已安装）
    },
    {
      "key": "evalscope",
      "name": "EvalScope",
      "description": "……",
      "available": false
    },
    {
      "key": "maseval",
      "name": "MASEval",
      "description": "……",
      "available": false
    }
  ]
}
```

### 6.13 KB 检索接口：POST /api/evaluator/kb-search

| 项 | 值 |
|---|---|
| 鉴权 | 需登录(Bearer) |
| Content-Type | application/json |

**请求体字段**

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| query | string | 是 | 检索问题文本（strip 后非空） |
| top_k | integer | 否 | 返回文档条数，默认 5 |

**成功响应（200）**

```json
{
  "status": true,                              # 请求是否成功，恒为 true
  "query": "如何创建测试用例",                   # 回显检索问题
  "total": 3,                                  # 命中文档数
  "documents": [
    {
      "source": "dev_docs/xxx.md",             # 来源文件（缺失时为 "?"）
      "score": 0.8234,                         # 相似度得分（保留 4 位小数）
      "content": "……"                          # 文档内容（截断至 800 字符）
    }
  ]
}
```

**错误码与文案（校验顺序即优先级）**

| HTTP | message | 触发条件 |
|---|---|---|
| 400 | 无效的 JSON | 请求体非合法 JSON |
| 400 | query required | query 缺失或 strip 后为空 |

### 6.14 KB 自测接口：POST /api/evaluator/kb-self-test

| 项 | 值 |
|---|---|
| 鉴权 | 需登录(Bearer) |
| 请求体 | 无（固定内置 8 条检索问题） |

**成功响应（200）**

```json
{
  "status": true,                              # 请求是否成功，恒为 true
  "score": {
    "coverage": 87.5,                          # 覆盖率（%：有命中结果的查询占比）
    "avg_relevance": 0.712,                    # 平均最高相似度（保留 3 位小数）
    "total_queries": 8                         # 自测查询总数
  },
  "details": [                                # 逐查询明细
    {
      "query": "如何创建测试用例",               # 查询文本
      "total_hits": 3,                         # 命中条数
      "top_score": 0.8234,                     # 最高相似度
      "documents": [                           # 校验后的文档列表
        {
          "source": "dev_docs/xxx.md",         # 来源文件
          "score": 0.8234,                     # 相似度得分
          "content_preview": "……",             # 内容预览（截断至 200 字符）
          "content_length": 1024               # 内容长度
        }
      ]
    }
  ]
}
```

---

## 7. 附录：与代码不一致/易踩坑说明

1. **端点总数**：`apps/evaluator/AGENTS.md` 标注「14 端点」仅指 legacy 平铺集合；加上 DRF router 自动生成的 15 个标准端点，实际可达 29 个（不含已禁用的 PUT/PATCH `/runs/{id}/`）。
2. **鉴权口径**：本模块无「公开」端点——所有路径均落于 `/api/evaluator/*`，被网关中间件全局拦截（即使部分 legacy 视图未加 `@require_auth`）。
3. **`POST /runs/`（DRF create）**：因 `http_method_names` 含 post 而暴露，仅落库不触发评估，属迁移遗留；前端实际使用 `POST /runs/start` / `POST /runs/start/`。
4. **`banks/{id}/delete`（legacy）**：前端暂未消费（见 `apps/evaluator/AGENTS.md`），保留路由。
5. **legacy create/update 无 JSON 容错**：`create_bank`/`update_bank` 的 `json.loads` 未捕获 JSONDecodeError（与 `kb-search` 不同），非法 JSON 会 500。
6. **`report_json` 为字符串**：接口返回的是 JSON 字符串而非对象，前端需自行 `JSON.parse`。
7. **DRF 字段校验文案依赖 locale**：DRF 默认字段错误文案（如「该字段是必填项。」）随 `LANGUAGE_CODE=zh-hans` 生效，本文以中文标注，不同部署环境可能不同。
