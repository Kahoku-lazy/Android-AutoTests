# API-仪表盘 — /api/dashboard/* · /api/devices/stats/ · /api/cases/stats/

> 仪表盘聚合域全集 4 个端点：平台统计 / 平台活动 / 设备统计 / 用例统计。
> 真相源：`apps/dashboard/urls.py` + `views.py` + `ai_usage.py`（纯只读聚合，无 models、无 api.py、无 serializers）。

## 1. 总览

| 接口 | 方法 | 鉴权 | 说明 |
|---|---|---|---|
| 平台统计接口 | GET /api/dashboard/stats/ | 需登录(Bearer) | 平台级聚合：设备/用例/元素/工作流/运行/智能体/AI 用量/趋势图/最近任务 |
| 平台活动接口 | GET /api/dashboard/activities/ | 需登录(Bearer) | 平台最近动态（测试执行 + 智能体更新），最多 10 条 |
| 设备统计接口 | GET /api/devices/stats/ | 需登录(Bearer) | 设备池在线/忙碌/离线/断开汇总 |
| 用例统计接口 | GET /api/cases/stats/ | 需登录(Bearer) | 用例总数/启用/禁用（含可见性过滤） |

## 2. 通用约定

- **路由前缀特例**：本 App 是唯一挂载在 `/api/` 根下而非 `/api/{app}/` 的 App（`config/urls.py` 第 18 行 `path("api/", include("apps.dashboard.urls"))`）。故路径为 `/api/dashboard/stats/`、`/api/dashboard/activities/`、`/api/devices/stats/`、`/api/cases/stats/`。
- **尾斜杠**：urls.py 中路径**均带尾斜杠**（保留尾斜杠）。无尾斜杠请求由 `NormalizeTrailingSlashMiddleware` 自动补斜杠（不触发 301、不丢 Authorization 头），二者均可访问。
- **响应信封**：标准 `{status, data}`。成功 2xx → `{status: true, data}`；失败 ≥400 → `{status: false, message}`（`EnvelopeJSONRenderer` 统一包裹）。**特例**：`activities` 端点的 `data` 是**数组**而非对象。
- **鉴权**：全部端点「需登录(Bearer)」。视图未覆盖 `permission_classes`，继承 DRF 全局默认 `IsAuthenticated` + `shared.auth.drf_auth.JWTAuthentication`；同时路径不在中间件 `PUBLIC_PREFIXES` 内，由 `JWTAuthenticationMiddleware` 先行拦截。
- **纯只读**：本 App 无 models、无 api.py，聚合各 App 数据只读查询，不产生任何写操作。
- **请求**：4 个端点均为 GET，**无请求体、无查询参数**（视图仅使用 `request.user` 取当前用户做可见性过滤）。

---

## 3. 平台统计接口：GET /api/dashboard/stats/

| 项 | 值 |
|---|---|
| 鉴权 | 需登录（IsAuthenticated，Bearer Token） |

### 请求

无请求体、无查询参数；携带 `Authorization: Bearer <access_token>`。

### 成功响应（200）

```json
{
  "status": true,                       # 请求是否成功，恒为 true
  "data": {
    "devices": {
      "online": 2,                      # 在线设备数（状态为 ONLINE 或 BUSY）
      "total": 3                        # 可见设备总数（排除 OFFLINE/DISCONNECTED）
    },
    "cases": {
      "total": 42,                      # 用例总数（四类用例之和）
      "enabled": 38,                    # 启用用例数
      "breakdown": [                    # 按类型拆分
        {"type": "ui_automation", "label": "Android", "total": 20, "enabled": 18},  # Android 用例
        {"type": "web_automation", "label": "Web", "total": 8, "enabled": 7},       # Web 用例
        {"type": "api_testing", "label": "API", "total": 10, "enabled": 9},         # API 用例
        {"type": "storage", "label": "功能业务", "total": 4, "enabled": 4}          # 功能业务用例
      ]
    },
    "elements": {
      "total": 120,                     # 元素总数（Android/Web/API 三类之和）
      "pages": 15,                      # 页面数量
      "type_breakdown": [               # 按类型拆分
        {"type": "android", "label": "Android元素", "total": 80},
        {"type": "web", "label": "Web元素", "total": 30},
        {"type": "api", "label": "API接口", "total": 10}
      ]
    },
    "workflow": {
      "total": 5                        # 工作流文档总数
    },
    "runs": {
      "total": 66,                      # 执行记录总数
      "active": 1                       # 运行中（status=RUNNING）执行数
    },
    "agents": {
      "total": 4,                       # 当前用户可见智能体总数
      "active": 3                       # 其中状态为 active 的数量
    },
    "ai_usage": {                       # AI 用量（今日/累计两组口径）
      "task_count": {"today": 3, "total": 120},        # 任务数量
      "input_tokens": {"today": 5000, "total": 200000},  # 输入 token
      "output_tokens": {"today": 1200, "total": 45000},  # 输出 token
      "total_tokens": {"today": 6200, "total": 245000},  # 输入+输出 token
      "cache_hit_tokens": {"today": 800, "total": 30000},  # 缓存命中 token
      "cache_hit_rate": {"today": 16.0, "total": 15.0},   # 缓存命中率（%，1 位小数）
      "avg_tokens_per_task": {"today": 2066, "total": 2041},  # 平均每任务 token（取整）
      "deepseek_cost": {"today": 0.0028, "total": 0.1125}   # DeepSeek 费用（元，4 位小数）
    },
    "charts": {
      "execution": {                    # 近 12 天执行趋势
        "labels": ["01/01", "01/02", "01/03", "01/04", "01/05", "01/06", "01/07", "01/08", "01/09", "01/10", "01/11", "01/12"],  # 日期标签（MM/DD）
        "success": [5, 3, 0, 8, 2, 0, 4, 6, 1, 0, 2, 7],   # 每日成功执行数
        "failed": [1, 0, 2, 1, 0, 0, 1, 0, 2, 1, 0, 0]     # 每日失败执行数
      },
      "ai_tokens": {                    # 近 12 天 AI token 趋势
        "labels": ["01/01", "01/02", "01/03", "01/04", "01/05", "01/06", "01/07", "01/08", "01/09", "01/10", "01/11", "01/12"],
        "total_tokens": [1200, 900, 0, 1500, 0, 800, 2000, 0, 600, 1100, 0, 1300],  # 每日总 token
        "cache_tokens": [300, 200, 0, 400, 0, 150, 500, 0, 120, 280, 0, 310]        # 每日缓存命中 token
      },
      "deepseek_cost": {                # 近 12 天 DeepSeek 费用趋势
        "labels": ["01/01", "01/02", "01/03", "01/04", "01/05", "01/06", "01/07", "01/08", "01/09", "01/10", "01/11", "01/12"],
        "cost": [0.0012, 0.0009, 0.0, 0.0015, 0.0, 0.0008, 0.002, 0.0, 0.0006, 0.0011, 0.0, 0.0013]  # 每日费用（元，4 位小数）
      }
    },
    "execution_summary": {
      "passed": 55,                     # 通过测试结果数（result ∈ pass/passed）
      "failed": 11                      # 失败测试结果数（result ∈ fail/failed）
    },
    "recent_tasks": [                   # 最近任务（执行中运行 + 最近用例执行摘要，最多 8 条）
      {
        "id": 12,                       # 用例 ID（最近用例项）或 run_id（执行中项）
        "title": "登录流程验证",          # 用例标题（缺失时回退为 id）
        "status": "partial",            # idle / success / failed / partial / running
        "passed": 2,                    # 近 2 小时窗口内通过数
        "failed": 1,                    # 近 2 小时窗口内失败数
        "total": 3,                     # passed + failed
        "time": "2026-01-12 14:30",     # 最近执行时间（YYYY-MM-DD HH:MM）
        "cases": [                      # 用例明细（单元素数组）
          {"title": "登录流程验证", "status": "partial", "passed": 2, "failed": 1}
        ]
      },
      {
        "id": "run_abc123",             # 执行中的运行 ID
        "title": "执行中 · SERIAL001",   # 执行中任务标题
        "status": "running",            # 固定 running
        "passed": 0,                    # 执行中未产出结果，恒 0
        "failed": 0,                    # 恒 0
        "total": 0,                     # 恒 0
        "time": "2026-01-12 14:50",     # 开始时间
        "cases": [                      # 该运行选中的用例（均 running）
          {"title": "首页冒烟", "status": "running", "passed": 0, "failed": 0}
        ]
      }
    ],
    "last_updated": "2026-01-12 14:50",  # 聚合计算时间（YYYY-MM-DD HH:MM）
    "system_status": "normal"            # normal（有在线设备或设备总数为 0）/ no_devices（有设备但全部离线）
  }
}
```

> 说明：`cases.breakdown` 的 total/enabled 为该端点 `cases.total`/ `cases.enabled` 的唯一来源（`sum(breakdown)`），不存在重复计数。
> `recent_tasks` 中「执行中」条目（`status=running`）来自 `test_runner.api.get_active_runs_info()`；「最近用例」条目来自 `TestResult` 按最近执行分组，近 2 小时窗口统计通过/失败。

### 错误码与文案

| HTTP | message | 触发条件 |
|---|---|---|
| 401 | 请先登录 | 未携带 `Authorization: Bearer` 头（中间件拦截） |
| 401 | 登录已过期或令牌无效 | 令牌无效 / 过期 / 已进黑名单（中间件拦截） |
| 401 | 用户不存在或已删除 | 令牌有效但对应用户已被删除（DRF 认证） |
| 500 | （无自定义文案） | 聚合查询触发服务器内部错误（未包裹 `_safe_count` 的计数） |

> 本视图不返回自定义业务错误文案；上述 401 为中间件/认证层统一文案，500 为 DRF 默认处理。

---

## 4. 平台活动接口：GET /api/dashboard/activities/

| 项 | 值 |
|---|---|
| 鉴权 | 需登录（IsAuthenticated，Bearer Token） |

### 请求

无请求体、无查询参数；携带 `Authorization: Bearer <access_token>`。

### 成功响应（200）

> **信封特例**：本端点 `data` 为**数组**（其余端点为对象）。数组元素为最近 5 条执行记录 + 最近 3 个智能体，按 `time` 倒序后取前 10 条。

```json
{
  "status": true,                       # 请求是否成功，恒为 true
  "data": [                             # 活动数组（最多 10 条）
    {
      "type": "run",                    # 活动类型：run=测试执行 / agent=智能体更新
      "action": "测试执行: run_abc123",   # 动作描述
      "detail": "设备: SERIAL001 · 状态: RUNNING",  # 明细
      "time": "2026-01-12 14:50"        # 时间（归一化为 YYYY-MM-DD HH:MM，16 字符）
    },
    {
      "type": "agent",                  # 智能体更新
      "action": "智能体更新: 用例评审助手", # 动作描述
      "detail": "模型: deepseek/deepseek-v4-pro",  # 模型提供方/模型名
      "time": "2026-01-12 13:20"        # 更新时间（YYYY-MM-DD HH:MM）
    }
  ]
}
```

> 说明：`run` 条目取 `TestRunRecord` 按 `-id` 倒序前 5 条；`agent` 条目取当前用户可见智能体按 `-updated_at` 倒序前 3 条；最终按 `time` 字符串倒序排序并截断前 10 条。

### 错误码与文案

| HTTP | message | 触发条件 |
|---|---|---|
| 401 | 请先登录 | 未携带 `Authorization: Bearer` 头（中间件拦截） |
| 401 | 登录已过期或令牌无效 | 令牌无效 / 过期 / 已进黑名单（中间件拦截） |
| 401 | 用户不存在或已删除 | 令牌有效但对应用户已被删除（DRF 认证） |
| 500 | （无自定义文案） | 聚合查询触发服务器内部错误 |

---

## 5. 设备统计接口：GET /api/devices/stats/

| 项 | 值 |
|---|---|
| 鉴权 | 需登录（IsAuthenticated，Bearer Token） |

### 请求

无请求体、无查询参数；携带 `Authorization: Bearer <access_token>`。

### 成功响应（200）

```json
{
  "status": true,                       # 请求是否成功，恒为 true
  "data": {
    "online": 2,                        # 在线设备数（状态为 ONLINE 或 BUSY）
    "busy": 1,                          # 忙碌设备数（状态为 BUSY）
    "offline": 1,                       # 离线设备数（状态为 OFFLINE）
    "disconnected": 0,                  # 断开设备数（状态为 DISCONNECTED）
    "total": 3                          # 可见设备总数（排除 OFFLINE/DISCONNECTED）
  }
}
```

> 口径说明（对齐设备池 UI「隐藏陈旧 OFFLINE/DISCONNECTED」约定）：
> - `online` = 状态 ∈ `{ONLINE, BUSY}` 的设备数（故含忙碌设备）。
> - `busy` = 状态 = `BUSY` 的设备数。
> - `total` = 排除 `OFFLINE` / `DISCONNECTED` 后的设备总数。
> - `offline` / `disconnected` 为独立计数（不参与 total），供前端展示完整分布。

### 错误码与文案

| HTTP | message | 触发条件 |
|---|---|---|
| 401 | 请先登录 | 未携带 `Authorization: Bearer` 头（中间件拦截） |
| 401 | 登录已过期或令牌无效 | 令牌无效 / 过期 / 已进黑名单（中间件拦截） |
| 401 | 用户不存在或已删除 | 令牌有效但对应用户已被删除（DRF 认证） |
| 500 | （无自定义文案） | 聚合查询触发服务器内部错误 |

---

## 6. 用例统计接口：GET /api/cases/stats/

| 项 | 值 |
|---|---|
| 鉴权 | 需登录（IsAuthenticated，Bearer Token） |

### 请求

无请求体、无查询参数；携带 `Authorization: Bearer <access_token>`。

### 成功响应（200）

```json
{
  "status": true,                       # 请求是否成功，恒为 true
  "data": {
    "total": 42,                        # 可见用例总数（四类用例之和）
    "enabled": 38,                      # 启用用例数（enabled=True）
    "disabled": 4                       # 禁用用例数（enabled=False）
  }
}
```

> 说明：四类用例 = `TestDefinition`(ui_automation) + `StorageTestCase`(storage) + `ApiTestCase`(api_testing) + `WebTestCase`(web_automation)，均经可见性过滤 `_visibility_q(user_id)`：`visibility=public` 或 `created_by=当前用户` 或（`visibility=restricted` 且 `permitted_users` 含当前用户）；未认证用户仅见 `public` 或 `created_by=""`。`enabled + disabled` 应等于 `total`。

### 错误码与文案

| HTTP | message | 触发条件 |
|---|---|---|
| 401 | 请先登录 | 未携带 `Authorization: Bearer` 头（中间件拦截） |
| 401 | 登录已过期或令牌无效 | 令牌无效 / 过期 / 已进黑名单（中间件拦截） |
| 401 | 用户不存在或已删除 | 令牌有效但对应用户已被删除（DRF 认证） |
| 500 | （无自定义文案） | 聚合查询触发服务器内部错误 |
