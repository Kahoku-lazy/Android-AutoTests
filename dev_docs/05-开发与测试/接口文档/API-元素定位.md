# API-元素定位 — /api/elements/*

> 元素定位模块：系统三项目（Android / Web / API）→ 目录树 → 按域文件；另保留 legacy 叶子只读与部分平铺路径。
> 真相源：`apps/element_locator/urls.py` + `views*.py` + `models.py` + `api*.py`。
> 方案：`dev_docs/05-开发与测试/设计方案与报告/设计方案-元素定位项目化重构.md`

## 0. 项目化工作台（标准信封，优先）

| 接口 | 方法 | 说明 |
|---|---|---|
| `/api/elements/projects/` | GET | 固定三项目（缺则 seed） |
| `/api/elements/projects/{code}/` | GET | code=`android\|web\|api` |
| `/api/elements/projects/{code}/tree/` | GET | 目录+文件树（file.kind） |
| `/api/elements/directories/` | POST | `{project_code,name,parent_id?}` |
| `/api/elements/directories/{id}/` | PATCH/DELETE | 改名 / 级联删 |
| `/api/elements/move/` | POST | `{kind,id,parent_directory_id?}` |
| `/api/elements/files/batch-delete/` | POST | `{kind,ids}` |

- 项目 `POST/PATCH/DELETE` → **405**
- 分组写（web-groups / api-groups 创建改删/batch-move）→ **410**
- 叶子创建仍走 pages/web/api-endpoints，body 带 `directory_id`

## 1. 总览

> 信封口径：router 路径（带尾斜杠）走标准 `{status, data}`；legacy 路径（无尾斜杠）走平铺 `{status, pages|elements|groups|flows|endpoint|...}`。同一资产双路径共存，行为一致、信封不同。

### 1.1 DRF Router 端点（标准信封 {status, data}，路径带尾斜杠）

| 接口 | 方法 | 鉴权 | 说明 |
|---|---|---|---|
| Web 分组列表 | GET /api/elements/web-groups/ | 需登录(Bearer) | 顶层分组树（children 递归嵌套） |
| 创建 Web 分组 | POST /api/elements/web-groups/ | 需登录(Bearer) | 创建分组/目录 |
| Web 分组详情 | GET /api/elements/web-groups/{id}/ | 需登录(Bearer) | 单个分组 |
| 全量更新 Web 分组 | PUT /api/elements/web-groups/{id}/ | 需登录(Bearer) | 全量更新 |
| 部分更新 Web 分组 | PATCH /api/elements/web-groups/{id}/ | 需登录(Bearer) | 部分更新 |
| 删除 Web 分组 | DELETE /api/elements/web-groups/{id}/ | 需登录(Bearer) | 删除（后代元素归未分组） |
| 批量移动 Web 分组 | POST /api/elements/web-groups/batch-move/ | 需登录(Bearer) | 批量移动到目标父级 |
| Web 元素列表 | GET /api/elements/web/ | 需登录(Bearer) | 列表（search/locator_type/page_url/is_test_point/group_id 过滤） |
| 创建 Web 元素 | POST /api/elements/web/ | 需登录(Bearer) | 创建 Web 元素 |
| Web 元素详情 | GET /api/elements/web/{id}/ | 需登录(Bearer) | 单个元素 |
| 全量更新 Web 元素 | PUT /api/elements/web/{id}/ | 需登录(Bearer) | 全量更新 |
| 部分更新 Web 元素 | PATCH /api/elements/web/{id}/ | 需登录(Bearer) | 部分更新 |
| 删除 Web 元素 | DELETE /api/elements/web/{id}/ | 需登录(Bearer) | 删除元素 |
| 批量导入 Web 元素 | POST /api/elements/web/batch/ | 需登录(Bearer) | 批量导入（不写入 tags，见 3.2） |
| API 分组列表 | GET /api/elements/api-groups/ | 需登录(Bearer) | 顶层分组树 |
| 创建 API 分组 | POST /api/elements/api-groups/ | 需登录(Bearer) | 创建分组/目录 |
| API 分组详情 | GET /api/elements/api-groups/{id}/ | 需登录(Bearer) | 单个分组 |
| 全量更新 API 分组 | PUT /api/elements/api-groups/{id}/ | 需登录(Bearer) | 全量更新 |
| 部分更新 API 分组 | PATCH /api/elements/api-groups/{id}/ | 需登录(Bearer) | 部分更新 |
| 删除 API 分组 | DELETE /api/elements/api-groups/{id}/ | 需登录(Bearer) | 删除（后代端点归未分组） |
| 批量移动 API 分组 | POST /api/elements/api-groups/batch-move/ | 需登录(Bearer) | 批量移动到目标父级 |
| API 端点列表 | GET /api/elements/api-endpoints/ | 需登录(Bearer) | 列表（search/method/is_test_point/group_id 过滤） |
| 创建 API 端点 | POST /api/elements/api-endpoints/ | 需登录(Bearer) | 创建 API 端点 |
| API 端点详情 | GET /api/elements/api-endpoints/{id}/ | 需登录(Bearer) | 单个端点 |
| 全量更新 API 端点 | PUT /api/elements/api-endpoints/{id}/ | 需登录(Bearer) | 全量更新 |
| 部分更新 API 端点 | PATCH /api/elements/api-endpoints/{id}/ | 需登录(Bearer) | 部分更新 |
| 删除 API 端点 | DELETE /api/elements/api-endpoints/{id}/ | 需登录(Bearer) | 删除端点 |
| 页面流列表 | GET /api/elements/flows/ | 需登录(Bearer) | 页面跳转流列表 |
| 创建页面流 | POST /api/elements/flows/ | 需登录(Bearer) | 创建页面跳转流 |
| 页面流详情 | GET /api/elements/flows/{id}/ | 需登录(Bearer) | 单个页面流 |
| 删除页面流 | DELETE /api/elements/flows/{id}/ | 需登录(Bearer) | 删除页面流 |
| Web 流列表 | GET /api/elements/web-flows/ | 需登录(Bearer) | Web 页面流列表 |
| 创建 Web 流 | POST /api/elements/web-flows/ | 需登录(Bearer) | 创建 Web 页面流（校验非目录） |
| Web 流详情 | GET /api/elements/web-flows/{id}/ | 需登录(Bearer) | 单个 Web 流 |
| 删除 Web 流 | DELETE /api/elements/web-flows/{id}/ | 需登录(Bearer) | 删除 Web 流 |

### 1.2 Legacy 平铺端点（平铺信封，路径无尾斜杠）

| 接口 | 方法 | 鉴权 | 说明 |
|---|---|---|---|
| 页面列表 | GET /api/elements/pages | 需登录(Bearer) | 页面/目录平铺列表 |
| 创建页面 | POST /api/elements/pages/create | 需登录(Bearer) | 手动创建页面/目录 |
| 快照导入 | POST /api/elements/pages/import-snapshot | 需登录(Bearer) | 检查器/AI 保存（新端点，标准 {status,data} 信封） |
| 清空页面 | POST /api/elements/pages/clear | 需登录(Bearer) | 清空全部页面/元素/流 |
| 批量移动页面 | POST /api/elements/pages/batch-move | 需登录(Bearer) | 页面/目录批量移动 |
| 重命名页面 | PUT /api/elements/pages/{page_id} | 需登录(Bearer) | 重命名页面/目录 |
| 删除页面 | DELETE /api/elements/pages/{page_id} | 需登录(Bearer) | 删除页面 |
| 页面元素列表 | GET /api/elements/pages/{page_id}/items | 需登录(Bearer) | 页面元素（filter/分页） |
| 添加元素 | POST /api/elements/pages/{page_id}/elements | 需登录(Bearer) | 手动添加元素（upsert） |
| 批量保存元素 | POST /api/elements/pages/{page_id}/elements/batch | 需登录(Bearer) | 批量保存元素 |
| 更新元素 | PUT /api/elements/items/{el_id} | 需登录(Bearer) | 更新元素元数据 |
| 页面流列表 | GET /api/elements/flows | 需登录(Bearer) | 页面流列表（legacy） |
| 创建页面流 | POST /api/elements/flows | 需登录(Bearer) | 创建页面流（legacy） |
| 删除页面流 | DELETE /api/elements/flows/{flow_id} | 需登录(Bearer) | 删除页面流（legacy） |
| Web 元素列表 | GET /api/elements/web | 需登录(Bearer) | Web 元素列表（legacy） |
| 创建 Web 元素 | POST /api/elements/web/create | 需登录(Bearer) | 创建 Web 元素（legacy） |
| 批量导入 Web 元素 | POST /api/elements/web/batch | 需登录(Bearer) | 批量导入（legacy，写入 tags） |
| 更新 Web 元素 | PUT /api/elements/web/{el_id} | 需登录(Bearer) | 更新 Web 元素（legacy） |
| 删除 Web 元素 | DELETE /api/elements/web/{el_id} | 需登录(Bearer) | 删除 Web 元素（legacy） |
| Web 分组列表 | GET /api/elements/web-groups | 需登录(Bearer) | Web 分组平铺列表（legacy） |
| 创建 Web 分组 | POST /api/elements/web-groups/create | 需登录(Bearer) | 创建 Web 分组（legacy） |
| 批量移动 Web 分组 | POST /api/elements/web-groups/batch-move | 需登录(Bearer) | 批量移动（legacy） |
| 重命名 Web 分组 | PUT /api/elements/web-groups/{group_id} | 需登录(Bearer) | 重命名（legacy） |
| 删除 Web 分组 | DELETE /api/elements/web-groups/{group_id} | 需登录(Bearer) | 删除（legacy） |
| Web 流列表 | GET /api/elements/web-flows | 需登录(Bearer) | Web 流列表（legacy） |
| 创建 Web 流 | POST /api/elements/web-flows | 需登录(Bearer) | 创建 Web 流（legacy） |
| 删除 Web 流 | DELETE /api/elements/web-flows/{flow_id} | 需登录(Bearer) | 删除 Web 流（legacy） |
| API 分组列表 | GET /api/elements/api-groups | 需登录(Bearer) | API 分组平铺列表（legacy） |
| 创建 API 分组 | POST /api/elements/api-groups/create | 需登录(Bearer) | 创建 API 分组（legacy） |
| 批量移动 API 分组 | POST /api/elements/api-groups/batch-move | 需登录(Bearer) | 批量移动（legacy） |
| 重命名 API 分组 | PUT /api/elements/api-groups/{group_id} | 需登录(Bearer) | 重命名（legacy） |
| 删除 API 分组 | DELETE /api/elements/api-groups/{group_id} | 需登录(Bearer) | 删除（legacy） |
| API 端点列表 | GET /api/elements/api-endpoints | 需登录(Bearer) | API 端点列表（legacy） |
| 创建 API 端点 | POST /api/elements/api-endpoints/create | 需登录(Bearer) | 创建 API 端点（legacy） |
| 更新 API 端点 | PUT /api/elements/api-endpoints/{el_id} | 需登录(Bearer) | 更新 API 端点（legacy） |
| 删除 API 端点 | DELETE /api/elements/api-endpoints/{el_id} | 需登录(Bearer) | 删除 API 端点（legacy） |

## 2. 通用约定

- 路径前缀统一为 `/api/elements/`（`config/urls.py`：`path("api/elements/", include("apps.element_locator.urls"))`）。
- **鉴权**：本模块**全部端点均需登录（Bearer）**，无公开路径。`gateway.middleware.JWTAuthenticationMiddleware` 拦截所有 `/api/` 受保护路径并注入 `request.user_id`；DRF 端点另由 `JWTAuthentication` + `IsAuthenticated` 兜底。请求头：`Authorization: Bearer <access_token>`。
- **信封双口径**：
  - router 路径（带尾斜杠）→ `shared.renderers.EnvelopeJSONRenderer` 包裹：成功 `{status: true, data}`；失败（≥400）`{status: false, message}`。
  - legacy 路径（无尾斜杠）→ `views.py` 的 `JsonResponse` 平铺：`{status, pages|elements|groups|flows|endpoints|...}`。例外：`pages/import-snapshot` 为新端点，采用标准 `{status, data}` 信封（见 4.1）。
- **尾斜杠**：router 端点带尾斜杠；legacy 端点不带。二者路径字符串不同、可共存（`gateway.normalize_slash.NormalizeTrailingSlashMiddleware` 保证无尾斜杠请求命中 legacy 原样、带尾斜杠命中 router）。
- **Content-Type**：`application/json`（写操作）；字段名 snake_case。
- **DRF 删除**：`DELETE` 成功返回 `204 No Content`（无响应体）。
- **DRF 校验错误文案**：由 DRF 本地化（`LANGUAGE_CODE="zh-hans"`）产出，`message` 取首个字段错误（如缺少必填字段时为「该字段是必填项。」等）；本文按触发条件标注 HTTP 状态码与代表文案，实际以运行环境为准。

---

## 3. DRF Router 标准端点（{status, data}）

### 3.1 Web 元素分组 web-groups

**通用错误码（本组全部端点适用）**

| HTTP | message | 触发条件 |
|---|---|---|
| 401 | 请先登录 | 无 Authorization 头（中间件拦截） |
| 401 | 登录已过期或令牌无效 | 令牌无效/过期/类型非 access |
| 404 | 未找到 | 目标分组不存在（DRF Http404） |
| 400 | （DRF 首个字段错误） | 字段校验失败（如缺少 name / locator_type 非法等） |

---

**Web 分组列表接口：GET /api/elements/web-groups/**

仅返回顶层分组（`parent__isnull=True`），子分组通过 `children` 递归嵌套。

成功响应（200）

```json
{
  "status": true,                       # 请求是否成功，恒为 true
  "data": [                             # 顶层分组数组
    {
      "id": 1,                          # 分组 ID
      "name": "登录模块",               # 分组名称
      "parent_id": null,                # 父分组 ID，null=根
      "is_folder": true,                # 是否仅作目录（非页面）
      "sort_order": 0,                  # 排序权重
      "created_at": "2026-08-21T10:00:00Z",  # 创建时间
      "element_count": 3,               # 直属元素数量
      "children": [                     # 子分组（递归同构）
        {
          "id": 2,
          "name": "登录按钮",
          "parent_id": 1,
          "is_folder": false,
          "sort_order": 0,
          "created_at": "2026-08-21T10:01:00Z",
          "element_count": 1,
          "children": []
        }
      ]
    }
  ]
}
```

---

**创建 Web 分组接口：POST /api/elements/web-groups/**

请求体

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| name | string | 是 | 分组名称 |
| parent_id | integer | 否 | 父分组 ID，null/缺省=根 |
| is_folder | boolean | 否 | 是否仅作目录，默认 false |
| sort_order | integer | 否 | 排序权重，默认 0 |

成功响应（201）

```json
{
  "status": true,
  "data": {
    "id": 3,                            # 新建分组 ID
    "name": "订单模块",
    "parent_id": 1,
    "is_folder": false,
    "sort_order": 0,
    "created_at": "2026-08-21T11:00:00Z",
    "element_count": 0,                 # 新建无元素
    "children": []
  }
}
```

---

**Web 分组详情接口：GET /api/elements/web-groups/{id}/**

成功响应（200）

```json
{
  "status": true,
  "data": {
    "id": 1,                            # 分组 ID
    "name": "登录模块",
    "parent_id": null,
    "is_folder": true,
    "sort_order": 0,
    "created_at": "2026-08-21T10:00:00Z",
    "element_count": 3,
    "children": []                      # 子分组（递归）
  }
}
```

---

**全量更新 Web 分组接口：PUT /api/elements/web-groups/{id}/**

请求体同「创建 Web 分组」（`name` 必填；`parent_id`/`is_folder`/`sort_order` 可选，未传按 ModelSerializer 规则重置/用默认值）。成功响应（200）结构同「详情接口」。

---

**部分更新 Web 分组接口：PATCH /api/elements/web-groups/{id}/**

请求体为「创建 Web 分组」字段的任意子集（只更新传入字段）。成功响应（200）结构同「详情接口」。

---

**删除 Web 分组接口：DELETE /api/elements/web-groups/{id}/**

无请求体。成功返回 `204 No Content`（无响应体）。删除后其后代分组的元素 `group` 置空（归未分组）。

---

**批量移动 Web 分组接口：POST /api/elements/web-groups/batch-move/**

请求体

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| group_ids | array[int] | 是 | 待移动分组 ID 列表 |
| target_parent_id | integer | 否 | 目标父分组 ID，null/缺省=移动到根 |

成功响应（200）

```json
{
  "status": true,
  "data": {
    "moved": 2                          # 实际移动的分组数量
  }
}
```

错误码与文案

| HTTP | message | 触发条件 |
|---|---|---|
| 400 | group_ids is required | group_ids 为空列表/缺省 |
| 400 | 目标分组不存在 | target_parent_id 对应分组不存在 |

---

### 3.2 Web 元素 web

**通用错误码**：同 3.1 通用错误码（401/404/400），404 文案为「未找到」（元素不存在）。

---

**Web 元素列表接口：GET /api/elements/web/**

查询参数（均可选）

| 参数 | 类型 | 说明 |
|---|---|---|
| search | string | 名称/定位值模糊匹配（name、locator_value） |
| locator_type | string | 精确匹配定位方式 |
| page_url | string | 精确匹配页面 URL |
| is_test_point | string | true/1/yes 过滤测试点 |
| group_id | string | 数字，过滤所属分组 |

成功响应（200）

```json
{
  "status": true,
  "data": [                             # Web 元素数组
    {
      "id": 5,                          # 元素 ID
      "name": "登录按钮",               # 元素名称
      "group_id": 1,                    # 所属分组 ID（可为 null）
      "group_name": "登录模块",         # 所属分组名称（只读，可为 null）
      "locator_type": "css_selector",   # 定位方式（见 models choices）
      "locator_value": "#login-btn",    # 定位表达式
      "page_url": "https://x.com/login",# 页面 URL
      "description": "登录页提交按钮",  # 描述
      "tags": "冒烟,登录",              # 标签
      "is_test_point": true,            # 是否测试点
      "created_at": "2026-08-21T10:00:00Z",
      "updated_at": "2026-08-21T10:30:00Z"
    }
  ]
}
```

---

**创建 Web 元素接口：POST /api/elements/web/**

请求体

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| name | string | 是 | 元素名称 |
| group_id | integer | 否 | 所属分组 ID |
| locator_type | string | 否 | 定位方式，默认 css_selector（12 选 1，见 models） |
| locator_value | string | 否 | 定位表达式 |
| page_url | string | 否 | 页面 URL |
| description | string | 否 | 描述 |
| tags | string | 否 | 标签 |
| is_test_point | boolean | 否 | 是否测试点，默认 false |

> 注：DRF 序列化器仅校验 `name` 必填与 `locator_type` 合法（choices），**不强制 `locator_value` 非空**（与 legacy 创建口径不同，见 4.4）。

成功响应（201）

```json
{
  "status": true,
  "data": {
    "id": 6,
    "name": "登录按钮",
    "group_id": 1,
    "group_name": "登录模块",
    "locator_type": "css_selector",
    "locator_value": "#login-btn",
    "page_url": "https://x.com/login",
    "description": "",
    "tags": "",
    "is_test_point": false,
    "created_at": "2026-08-21T11:00:00Z",
    "updated_at": "2026-08-21T11:00:00Z"
  }
}
```

---

**Web 元素详情接口：GET /api/elements/web/{id}/**

成功响应（200）结构同「创建」的 data 对象。

---

**全量更新 Web 元素接口：PUT /api/elements/web/{id}/**

请求体同「创建 Web 元素」；`group_id` 用于改所属分组。成功响应（200）结构同「详情」。

---

**部分更新 Web 元素接口：PATCH /api/elements/web/{id}/**

请求体为「创建」字段的任意子集（只更新传入字段）。成功响应（200）结构同「详情」。

---

**删除 Web 元素接口：DELETE /api/elements/web/{id}/**

无请求体。成功返回 `204 No Content`。

---

**批量导入 Web 元素接口：POST /api/elements/web/batch/**

请求体：可直接传 JSON 数组，或 `{"items": [...]}`（`items` 为元素数组）。数组元素字段同「创建 Web 元素」的 `name`/`locator_type`/`locator_value`/`group_id`/`page_url`/`description`/`is_test_point`。

> 说明：本端点**不接收也不写入 `tags`**（代码未透传）；legacy 批量导入（4.4）则写入 tags。字段以实际代码为准。

成功响应（200）

```json
{
  "status": true,
  "data": {
    "created": 3                        # 实际创建的元素数量
  }
}
```

错误码与文案

| HTTP | message | 触发条件 |
|---|---|---|
| 400 | items is required | 既非数组也未提供 items 键 |

---

### 3.3 API 分组 api-groups

与 3.1 Web 分组结构完全同构，差异仅在字段名 `element_count` → `endpoint_count`、写库目标为 `el_api_groups`。以下列出全部端点与特有细节。

**API 分组列表接口：GET /api/elements/api-groups/**

仅顶层分组，`children` 递归。成功响应（200）

```json
{
  "status": true,
  "data": [
    {
      "id": 1,                          # 分组 ID
      "name": "用户中心",
      "parent_id": null,
      "is_folder": true,
      "sort_order": 0,
      "created_at": "2026-08-21T10:00:00Z",
      "endpoint_count": 2,              # 直属端点数量
      "children": []                    # 子分组（递归同构）
    }
  ]
}
```

**创建 API 分组接口：POST /api/elements/api-groups/**

请求体：`name`（string，必填）、`parent_id`（integer，否）、`is_folder`（boolean，否）、`sort_order`（integer，否）。成功响应（201）结构同列表项。

**API 分组详情接口：GET /api/elements/api-groups/{id}/**

成功响应（200）结构同列表项。

**全量更新 API 分组接口：PUT /api/elements/api-groups/{id}/**

请求体同「创建」；成功响应（200）结构同列表项。

**部分更新 API 分组接口：PATCH /api/elements/api-groups/{id}/**

请求体为「创建」字段子集；成功响应（200）结构同列表项。

**删除 API 分组接口：DELETE /api/elements/api-groups/{id}/**

无请求体。成功 `204 No Content`。删除后其后代分组的端点 `group` 置空。

**批量移动 API 分组接口：POST /api/elements/api-groups/batch-move/**

请求体：`group_ids`（array[int]，必填）、`target_parent_id`（integer，否）。成功响应（200）

```json
{
  "status": true,
  "data": {
    "moved": 2                          # 实际移动的分组数量
  }
}
```

错误码与文案

| HTTP | message | 触发条件 |
|---|---|---|
| 400 | group_ids is required | group_ids 为空/缺省 |
| 400 | 目标分组不存在 | target_parent_id 对应分组不存在 |

---

### 3.4 API 端点 api-endpoints

**通用错误码**：同 3.1（401/404/400）。

---

**API 端点列表接口：GET /api/elements/api-endpoints/**

查询参数（均可选）：`search`（name/url 模糊）、`method`（精确，如 GET）、`is_test_point`（true/1/yes）、`group_id`（数字）。

成功响应（200）

```json
{
  "status": true,
  "data": [
    {
      "id": 9,                          # 端点 ID
      "name": "查询用户",               # 接口名称
      "group_id": 1,                    # 所属分组 ID（可为 null）
      "group_name": "用户中心",         # 所属分组名称（只读）
      "method": "GET",                  # 请求方法（GET/POST/PUT/DELETE/PATCH）
      "url": "/api/user/{id}",          # 接口 URL
      "headers": {},                    # 请求头（JSON 对象）
      "request_body_schema": {},        # 请求体结构（JSON 对象）
      "response_body_schema": {},       # 响应体结构（JSON 对象）
      "description": "按 ID 查询用户",  # 描述
      "tags": "用户",                   # 标签
      "is_test_point": true,            # 是否测试点
      "created_at": "2026-08-21T10:00:00Z",
      "updated_at": "2026-08-21T10:00:00Z"
    }
  ]
}
```

---

**创建 API 端点接口：POST /api/elements/api-endpoints/**

请求体

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| name | string | 是 | 接口名称 |
| group_id | integer | 否 | 所属分组 ID |
| method | string | 否 | 请求方法，默认 GET（5 选 1） |
| url | string | 否 | 接口 URL |
| headers | object | 否 | 请求头，默认 {} |
| request_body_schema | object | 否 | 请求体结构，默认 {} |
| response_body_schema | object | 否 | 响应体结构，默认 {} |
| description | string | 否 | 描述 |
| tags | string | 否 | 标签 |
| is_test_point | boolean | 否 | 是否测试点，默认 false |

> 注：DRF 序列化器仅强制 `name` 必填与 `method` 合法（choices）；`url` 非必填（legacy 创建则强制 url 非空，见 4.8）。

成功响应（201）

```json
{
  "status": true,
  "data": {
    "id": 10,
    "name": "创建用户",
    "group_id": 1,
    "group_name": "用户中心",
    "method": "POST",
    "url": "/api/user",
    "headers": {},
    "request_body_schema": {},
    "response_body_schema": {},
    "description": "",
    "tags": "",
    "is_test_point": false,
    "created_at": "2026-08-21T11:00:00Z",
    "updated_at": "2026-08-21T11:00:00Z"
  }
}
```

---

**API 端点详情接口：GET /api/elements/api-endpoints/{id}/**

成功响应（200）结构同「创建」的 data 对象。

**全量更新 API 端点接口：PUT /api/elements/api-endpoints/{id}/**

请求体同「创建」；`group_id` 用于改所属分组。成功响应（200）结构同「详情」。

**部分更新 API 端点接口：PATCH /api/elements/api-endpoints/{id}/**

请求体为「创建」字段子集。成功响应（200）结构同「详情」。

**删除 API 端点接口：DELETE /api/elements/api-endpoints/{id}/**

无请求体。成功 `204 No Content`。

---

### 3.5 页面流 flows（Android 页面跳转）

**通用错误码**：同 3.1（401/404/400）。仅支持 get/post/delete（无 put/patch）。

---

**页面流列表接口：GET /api/elements/flows/**

成功响应（200）

```json
{
  "status": true,
  "data": [
    {
      "id": 7,                          # 流 ID
      "from_page_id": 10,               # 源页面 ID
      "to_page_id": 11,                 # 目标页面 ID
      "trigger_element_id": 20,         # 触发元素 ID（可为 null）
      "from_label": "首页",             # 源页面名称（只读）
      "to_label": "登录页",             # 目标页面名称（只读）
      "trigger_text": "登录",           # 触发元素文本（只读，可为 ""）
      "trigger_action": "click",        # 触发动作
      "created_at": "2026-08-21T10:00:00Z"
    }
  ]
}
```

---

**创建页面流接口：POST /api/elements/flows/**

请求体

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| from_page_id | integer | 是 | 源页面 ID |
| to_page_id | integer | 是 | 目标页面 ID |
| trigger_element_id | integer | 否 | 触发元素 ID |
| trigger_action | string | 否 | 触发动作，默认 click |

成功响应（201）

```json
{
  "status": true,
  "data": {
    "id": 8,
    "from_page_id": 10,
    "to_page_id": 11,
    "trigger_element_id": 20,
    "from_label": "首页",
    "to_label": "登录页",
    "trigger_text": "登录",
    "trigger_action": "click",
    "created_at": "2026-08-21T11:00:00Z"
  }
}
```

---

**页面流详情接口：GET /api/elements/flows/{id}/**

成功响应（200）结构同「创建」的 data 对象。

**删除页面流接口：DELETE /api/elements/flows/{id}/**

无请求体。成功 `204 No Content`。

---

### 3.6 Web 页面流 web-flows

**通用错误码**：同 3.1（401/404/400）。仅支持 get/post/delete。

---

**Web 流列表接口：GET /api/elements/web-flows/**

成功响应（200）

```json
{
  "status": true,
  "data": [
    {
      "id": 12,                         # 流 ID
      "from_group_id": 1,               # 源 Web 分组 ID
      "to_group_id": 2,                 # 目标 Web 分组 ID
      "trigger_element_id": 5,          # 触发 Web 元素 ID（可为 null）
      "from_name": "首页",              # 源分组名称（只读）
      "to_name": "登录页",              # 目标分组名称（只读）
      "trigger_action": "click",        # 触发动作
      "created_at": "2026-08-21T10:00:00Z"
    }
  ]
}
```

---

**创建 Web 流接口：POST /api/elements/web-flows/**

请求体

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| from_group_id | integer | 是 | 源 Web 分组 ID（须非目录） |
| to_group_id | integer | 是 | 目标 Web 分组 ID（须非目录） |
| trigger_element_id | integer | 否 | 触发 Web 元素 ID |
| trigger_action | string | 否 | 触发动作，默认 click |

成功响应（201）

```json
{
  "status": true,
  "data": {
    "id": 13,
    "from_group_id": 1,
    "to_group_id": 2,
    "trigger_element_id": 5,
    "from_name": "首页",
    "to_name": "登录页",
    "trigger_action": "click",
    "created_at": "2026-08-21T11:00:00Z"
  }
}
```

错误码与文案

| HTTP | message | 触发条件 |
|---|---|---|
| 400 | 源节点不能是目录 | from_group.is_folder=True |
| 400 | 目标节点不能是目录 | to_group.is_folder=True |

---

**Web 流详情接口：GET /api/elements/web-flows/{id}/**

成功响应（200）结构同「创建」的 data 对象。

**删除 Web 流接口：DELETE /api/elements/web-flows/{id}/**

无请求体。成功 `204 No Content`。

---

## 4. Legacy 平铺端点（平铺信封）

> 以下端点由 `views.py` 的 `JsonResponse` 直接返回平铺结构；成功 `status` 为 `true`，失败为 `false` + `message`。均需登录（Bearer）。

### 4.1 页面 pages

**页面列表接口：GET /api/elements/pages**

查询参数（可选）：`offset`、`limit`（分页，代码读取但当前返回全量列表）。成功响应（200）

```json
{
  "status": true,                       # 请求是否成功
  "pages": [                            # 页面数组（平铺，含目录节点）
    {
      "id": 10,                         # 页面 ID
      "device_id": 1,                   # 设备 ID
      "parent_id": null,                # 父节点 ID
      "is_folder": false,               # 是否目录
      "depth": 1,                       # 树深度（根=1）
      "label": "首页",                  # 名称
      "package": "com.example",         # 应用包名
      "activity": ".MainActivity",      # Activity
      "screenshot_path": "/media/xx.png", # 截图路径
      "ocr_json": null,                 # 页面级 OCR JSON（可为 null）
      "snapshot_id": 100,               # 来源检查器快照 ID（可为 null）
      "element_count": 3,               # 元素数量
      "created_at": "2026-08-21 10:00:00", # 创建时间
      "flow_out": 1,                    # 出边流数量
      "flow_in": 0                      # 入边流数量
    }
  ],
  "max_depth": 5                        # 目录最大嵌套层数
}
```

---

**创建页面接口：POST /api/elements/pages/create**

请求体

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| label | string | 是 | 名称（必填） |
| parent_id | integer | 否 | 父目录 ID（""/0/"0" 视为根） |
| is_folder | boolean | 否 | 是否目录，默认 false |
| package | string | 否 | 应用包名 |
| activity | string | 否 | Activity |

成功响应（200）

```json
{
  "status": true,
  "page": {
    "id": 14,
    "device_id": 1,
    "parent_id": null,
    "is_folder": false,
    "depth": 1,
    "label": "登录页",
    "package": "",
    "activity": "",
    "screenshot_path": "",
    "ocr_json": null,
    "snapshot_id": null,
    "element_count": 0,
    "created_at": "2026-08-21 11:00:00",
    "flow_out": 0,
    "flow_in": 0
  }
}
```

错误码与文案

| HTTP | message | 触发条件 |
|---|---|---|
| 405 | method not allowed | 非 POST |
| 400 | 名称(label)必填 | label 为空 |
| 400 | 目录最多嵌套 5 层 | 目录层级超限 |
| 404 | 父级目录不存在 | parent_id 对应节点不存在 |
| 400 | 只能在目录下创建子级 | 父节点不是目录 |
| 409 | 同级名称「{label}」已存在 | 同级重名 |
| 409 | 创建失败，名称「{label}」可能已存在 | 数据库唯一约束冲突 |

---

**快照导入接口：POST /api/elements/pages/import-snapshot**

> **新端点（v7.2），采用标准信封 `{status, data}`**（区别于其它 legacy 平铺端点）。供设备检查器 / AI 保存工具调用。

请求体

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| page_label | string | 条件 | 新建模式必填（已有模式用 page_id） |
| page_id | integer | 条件 | 已有页面 ID（二选一：新建 vs 已有） |
| folder_path | string | 否 | 目录路径，按「/」逐级查找或创建 |
| package | string | 否 | 应用包名 |
| activity | string | 否 | Activity |
| screenshot_path | string | 否 | 截图路径 |
| ocr_json | object | 否 | 页面级 OCR 结果 |
| snapshot_id | integer | 否 | 来源检查器快照 ID |
| elements | array | 是 | 元素数组（见下） |

元素对象字段：`alias`/`text`/`resource_id`/`class_name`/`content_desc`/`bounds`/`xpaths`/`x`/`y`/`width`/`height`/`depth`/`index`/`clickable`/`enabled`/`scrollable`/`checked`/`thumbnail_path`（元素按 `(page, resource_id, bounds)` upsert）。

成功响应（200）

```json
{
  "status": true,
  "data": {
    "saved": 2,                         # 新创建元素数
    "updated": 1,                       # upsert 更新元素数
    "skipped": 0,                       # 跳过数
    "page_id": 15                       # 目标页面 ID
  }
}
```

错误码与文案

| HTTP | message | 触发条件 |
|---|---|---|
| 400 | 无效的 JSON 请求体 | 请求体非合法 JSON |
| 400 | 元素数据不能为空 | elements 为空 |
| 400 | 目标页面不存在 | page_id 对应页面不存在/是目录 |
| 400 | 页面名称不能为空 | 新建模式 page_label 为空 |
| 409 | 同级页面「{label}」已存在 | 新建模式同级重名 |
| 409 | 目录最多嵌套 5 层 | 目录层级超限 |
| 409 | 同名节点「{segment}」不是目录 | folder_path 某段同名节点是页面 |
| 500 | 导入失败 | 其它异常 |

---

**清空页面接口：POST /api/elements/pages/clear**

无请求体。清空全部页面/元素/页面流。成功响应（200）

```json
{
  "status": true                        # 请求是否成功
}
```

---

**批量移动页面接口：POST /api/elements/pages/batch-move**

请求体

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| page_ids | array[int] | 是 | 待移动页面/目录 ID |
| parent_id | integer | 否 | 目标父目录 ID，null/""/0/"0"=移动到根 |

成功响应（200）

```json
{
  "status": true,
  "moved": 2,                           # 实际移动数量
  "errors": []                          # 逐项失败原因 [{id, reason}]
}
```

错误码与文案

| HTTP | message | 触发条件 |
|---|---|---|
| 405 | method not allowed | 非 POST |
| 400 | page_ids 不能为空 | page_ids 为空 |
| 404 | 目标目录不存在 | parent_id 对应节点不存在 |
| 400 | 目标必须是目录 | 目标非目录 |
| 400 | page_ids 格式无效 | page_ids 元素非整数 |

---

**重命名页面接口：PUT /api/elements/pages/{page_id}**

请求体

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| label | string | 是 | 新名称 |

成功响应（200）

```json
{
  "status": true
}
```

错误码与文案

| HTTP | message | 触发条件 |
|---|---|---|
| 400 | 页面名称不能为空 | label 为空 |
| 404 | 页面不存在 | page_id 不存在 |
| 409 | 同级名称「{new_label}」已存在 | 同级重名 |

---

**删除页面接口：DELETE /api/elements/pages/{page_id}**

无请求体。成功响应（200）

```json
{
  "status": true
}
```

> 注：删除不校验存在性（`api.delete_page` 静默删除），不存在也返回 status=true。

---

### 4.2 元素 items / pages/{id}/elements

**页面元素列表接口：GET /api/elements/pages/{page_id}/items**

查询参数（可选）：`filter`（all 默认 / clickable / text / testpoint）、`offset`、`limit`（上限 500）。成功响应（200）

```json
{
  "status": true,
  "elements": [                         # 元素数组
    {
      "id": 20,                         # 元素 ID
      "page_id": 10,                    # 所属页面 ID
      "class_name": "android.widget.Button", # 类名
      "text_val": "登录",               # 文本
      "content_desc": "",               # content-desc
      "resource_id": "com.example:id/btn_login", # resource-id
      "bounds": "[0,0][100,50]",        # 位置 bounds
      "x": 0,                           # 坐标 x
      "y": 0,                           # 坐标 y
      "width": 100,                     # 宽
      "height": 50,                     # 高
      "depth": 2,                       # 树深度
      "index": "0",                     # 兄弟索引
      "scrollable": false,              # 可滚动
      "checked": false,                 # 勾选态
      "thumbnail_path": "",             # 缩略图路径
      "xpath_candidates": "[{"type":"manual","xpath":"..."}]", # XPath 候选（JSON 字符串）
      "clickable": true,                # 可点击
      "enabled": true,                  # 可用
      "alias": "登录按钮",              # 别名
      "tags": "",                       # 标签
      "is_test_point": false,           # 是否测试点
      "notes": "",                      # 备注
      "created_at": "2026-08-21 10:00:00"
    }
  ],
  "total": 1                            # 总数（分页前）
}
```

---

**添加元素接口：POST /api/elements/pages/{page_id}/elements**

请求体

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| alias | string | 是 | 元素名称 |
| xpath | string | 否 | 手动 XPath（无 xpath_candidates 时使用） |
| xpath_candidates | array | 否 | XPath 候选列表（优先） |
| class_name | string | 否 | 类名 |
| text_val / text | string | 否 | 文本（text 为兼容别名） |
| content_desc | string | 否 | content-desc |
| resource_id | string | 否 | resource-id |
| bounds | string | 否 | 位置 |
| clickable | boolean | 否 | 可点击，默认 false |
| enabled | boolean | 否 | 可用，默认 true |
| notes | string | 否 | 备注 |

成功响应（200）

```json
{
  "status": true,
  "updated": false,                     # 是否命中已有元素（upsert 更新）
  "element": {
    "id": 21,                           # 元素 ID
    "page_id": 10,
    "alias": "登录按钮",
    "class_name": "android.widget.Button",
    "text_val": "登录",
    "content_desc": "",
    "resource_id": "com.example:id/btn_login",
    "clickable": true,
    "enabled": true,
    "scrollable": false,
    "checked": false,
    "bounds": "[0,0][100,50]",
    "x": 0,
    "y": 0,
    "width": 100,
    "height": 50,
    "depth": 0,
    "index": "",
    "thumbnail_path": "",
    "xpath_candidates": "[]",
    "is_test_point": false,
    "notes": ""
  }
}
```

错误码与文案

| HTTP | message | 触发条件 |
|---|---|---|
| 404 | 页面不存在 | page_id 不存在 |
| 400 | 目录节点不能添加元素，请选择子页面 | 目标节点是目录 |
| 400 | 元素名称(alias)必填 | alias 为空 |
| 409 | 该元素已在当前页面中（相同 resource-id 与位置），请到「元素管理」查看 | 唯一约束冲突 |
| 500 | 保存元素失败，请稍后重试 | 其它异常（含 detail） |

---

**批量保存元素接口：POST /api/elements/pages/{page_id}/elements/batch**

请求体

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| elements | array | 是 | 元素数组（字段同「添加元素」+ xpath_type/xpath_count） |

成功响应（200）

```json
{
  "status": true,
  "saved": 2,                           # 新建数量
  "updated": 1,                         # 更新数量
  "skipped": 0,                         # 跳过数量
  "errors": []                          # 错误摘要（最多 5 条）
}
```

错误码与文案

| HTTP | message | 触发条件 |
|---|---|---|
| 400 | 页面不存在 | page_id 不存在 |
| 400 | 目录节点不能添加元素 | 目标节点是目录 |
| 400 | elements 不能为空 | elements 为空 |

---

**更新元素接口：PUT /api/elements/items/{el_id}**

请求体（字段任选，只更新传入字段）

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| alias | string | 否 | 别名 |
| tags | string | 否 | 标签 |
| notes | string | 否 | 备注 |
| is_test_point | boolean | 否 | 是否测试点（bool 化） |

成功响应（200）

```json
{
  "status": true
}
```

> 注：不校验元素存在性，不存在也返回 status=true（`api.update_element` 静默更新 0 行）。

---

### 4.3 页面流 flows（legacy）

**页面流列表接口：GET /api/elements/flows**

成功响应（200）

```json
{
  "status": true,
  "flows": [                            # 页面流数组
    {
      "id": 7,                          # 流 ID
      "from_page_id": 10,               # 源页面 ID
      "to_page_id": 11,                 # 目标页面 ID
      "trigger_element_id": 20,         # 触发元素 ID（可为 null）
      "trigger_action": "click",        # 触发动作
      "created_at": "2026-08-21 10:00:00",
      "from_label": "首页",             # 源页面名称
      "to_label": "登录页",             # 目标页面名称
      "trigger_text": "登录",           # 触发元素文本
      "trigger_rid": "com.example:id/btn_login" # 触发元素 resource-id
    }
  ]
}
```

---

**创建页面流接口：POST /api/elements/flows**

请求体

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| from_page_id | integer | 是 | 源页面 ID |
| to_page_id | integer | 是 | 目标页面 ID |
| trigger_element_id | integer | 否 | 触发元素 ID |
| trigger_action | string | 否 | 触发动作，默认 click |

成功响应（200）

```json
{
  "status": true
}
```

> 注：缺少 from_page_id/to_page_id 会抛 KeyError（HTTP 500），无友好文案。

---

**删除页面流接口：DELETE /api/elements/flows/{flow_id}**

无请求体。成功响应（200）

```json
{
  "status": true
}
```

---

### 4.4 Web 元素 web（legacy）

**Web 元素列表接口：GET /api/elements/web**

查询参数（可选）：`search`（name/locator_value/description/tags 模糊）、`locator_type`、`page_url`、`is_test_point`（"1"/"true"）、`group_id`（""/"null"=未分组）。成功响应（200）

```json
{
  "status": true,
  "elements": [                         # Web 元素数组
    {
      "id": 5,                          # 元素 ID
      "name": "登录按钮",               # 名称
      "locator_type": "css_selector",   # 定位方式
      "locator_value": "#login-btn",    # 定位表达式
      "page_url": "https://x.com/login",# 页面 URL
      "description": "登录页提交按钮",  # 描述
      "tags": "冒烟",                   # 标签
      "is_test_point": true,            # 是否测试点
      "group_id": 1,                    # 所属分组 ID（可为 null）
      "created_at": "2026-08-21 10:00:00",
      "updated_at": "2026-08-21 10:30:00"
    }
  ],
  "total": 1                            # 元素总数
}
```

---

**创建 Web 元素接口：POST /api/elements/web/create**

请求体

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| name | string | 是 | 元素名称 |
| locator_type | string | 否 | 定位方式，默认 css_selector（12 选 1） |
| locator_value | string | 是 | 定位表达式（非空） |
| page_url | string | 否 | 页面 URL |
| description | string | 否 | 描述 |
| tags | string | 否 | 标签 |
| is_test_point | boolean | 否 | 是否测试点，默认 false |
| group_id | integer | 否 | 所属分组 ID |

成功响应（200）

```json
{
  "status": true,
  "element": {
    "id": 6,
    "name": "登录按钮",
    "locator_type": "css_selector",
    "locator_value": "#login-btn",
    "page_url": "https://x.com/login",
    "description": "",
    "tags": "",
    "is_test_point": false,
    "group_id": 1,
    "created_at": "2026-08-21 11:00:00",
    "updated_at": "2026-08-21 11:00:00"
  }
}
```

错误码与文案

| HTTP | message | 触发条件 |
|---|---|---|
| 400 | invalid JSON | 请求体非合法 JSON |
| 400 | 元素名称(name)必填 | name 为空 |
| 400 | 无效的定位方式, 必须是: css_selector, xpath, id, class_name, name, tag_name, link_text, partial_link_text, text, test_id, role, placeholder | locator_type 非法 |
| 400 | 定位值(locator_value)必填 | locator_value 为空 |
| 500 | 创建失败: {e} | 其它异常 |

---

**批量导入 Web 元素接口：POST /api/elements/web/batch**

请求体

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| elements | array | 是 | 元素数组（字段同「创建 Web 元素」，含 tags） |

成功响应（200）

```json
{
  "status": true,
  "saved": 2,                           # 成功创建数量
  "skipped": 1,                         # 跳过数量
  "errors": []                          # 错误摘要（最多 5 条）
}
```

错误码与文案

| HTTP | message | 触发条件 |
|---|---|---|
| 400 | invalid JSON | 请求体非合法 JSON |
| 400 | elements 不能为空 | elements 为空 |

---

**更新 Web 元素接口：PUT /api/elements/web/{el_id}**

请求体（字段任选，只更新传入字段）

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| name | string | 否 | 名称（非空） |
| locator_type | string | 否 | 定位方式（合法 12 选 1） |
| locator_value | string | 否 | 定位表达式 |
| page_url | string | 否 | 页面 URL |
| description | string | 否 | 描述 |
| tags | string | 否 | 标签 |
| is_test_point | boolean | 否 | 是否测试点 |
| group_id | integer | 否 | 所属分组（null/""/"null"=未分组） |

成功响应（200）

```json
{
  "status": true,
  "element": {
    "id": 6,
    "name": "登录按钮",
    "locator_type": "css_selector",
    "locator_value": "#login-btn",
    "page_url": "https://x.com/login",
    "description": "",
    "tags": "",
    "is_test_point": false,
    "group_id": 1,
    "created_at": "2026-08-21 11:00:00",
    "updated_at": "2026-08-21 11:05:00"
  }
}
```

错误码与文案

| HTTP | message | 触发条件 |
|---|---|---|
| 404 | 元素不存在 | el_id 不存在 |
| 400 | invalid JSON | 请求体非合法 JSON |
| 400 | 名称不能为空 | name 存在且为空 |
| 400 | 无效的定位方式 | locator_type 非法 |
| 405 | method not allowed | 非 PUT/DELETE |

---

**删除 Web 元素接口：DELETE /api/elements/web/{el_id}**

无请求体。成功响应（200）

```json
{
  "status": true
}
```

错误码：404 元素不存在（el_id 不存在）。

---

### 4.5 Web 分组 web-groups（legacy）

**Web 分组列表接口：GET /api/elements/web-groups**

成功响应（200）

```json
{
  "status": true,
  "groups": [                           # 平铺分组数组（含目录）
    {
      "id": 1,                          # 分组 ID
      "name": "登录模块",               # 名称
      "parent_id": null,                # 父分组 ID
      "is_folder": true,                # 是否目录
      "sort_order": 0,                  # 排序权重
      "element_count": 3,               # 直属元素数量
      "child_count": 1,                 # 子分组数量
      "created_at": "2026-08-21 10:00:00"
    }
  ]
}
```

---

**创建 Web 分组接口：POST /api/elements/web-groups/create**

请求体：`name`（string，必填）、`parent_id`（integer，否）、`is_folder`（boolean，否）、`sort_order`（integer，否）。成功响应（200）

```json
{
  "status": true,
  "group": {
    "id": 3,
    "name": "订单模块",
    "parent_id": 1,
    "is_folder": false,
    "sort_order": 0,
    "element_count": 0,
    "child_count": 0,
    "created_at": "2026-08-21 11:00:00"
  }
}
```

错误码与文案

| HTTP | message | 触发条件 |
|---|---|---|
| 400 | invalid JSON | 请求体非合法 JSON |
| 400 | 分组名称必填 | name 为空 |
| 400 | 只能将分组添加在目录下 | 父节点非目录 |
| 404 | 父级分组不存在 | parent_id 不存在 |
| 500 | 创建失败: {e} | 其它异常 |

---

**批量移动 Web 分组接口：POST /api/elements/web-groups/batch-move**

请求体：`group_ids`（array[int]，必填）、`parent_id`（integer，否，""/0/"0"/"__root__"=根）。成功响应（200）

```json
{
  "status": true,
  "moved": 2                            # 移动数量
}
```

错误码与文案

| HTTP | message | 触发条件 |
|---|---|---|
| 400 | invalid JSON | 请求体非合法 JSON |
| 400 | group_ids 不能为空 | group_ids 为空 |
| 400 | 目标必须是目录 | 目标非目录 |
| 404 | 目标分组不存在 | parent_id 不存在 |

---

**重命名 Web 分组接口：PUT /api/elements/web-groups/{group_id}**

请求体：`name`（string，必填，非空）。成功响应（200）返回 `{status: true, group: {...}}`（仅 name 已更新）。错误码：404 分组不存在 / 400 invalid JSON / 400 名称不能为空。

**删除 Web 分组接口：DELETE /api/elements/web-groups/{group_id}**

无请求体。成功响应（200）`{status: true}`。错误码：404 分组不存在。

---

### 4.6 Web 流 web-flows（legacy）

**Web 流列表接口：GET /api/elements/web-flows**

成功响应（200）

```json
{
  "status": true,
  "flows": [
    {
      "id": 12,                         # 流 ID
      "from_group_id": 1,               # 源分组 ID
      "to_group_id": 2,                 # 目标分组 ID
      "trigger_element_id": 5,          # 触发元素 ID（可为 null）
      "trigger_action": "click",        # 触发动作
      "created_at": "2026-08-21 10:00:00",
      "from_label": "首页",             # 源分组名称
      "to_label": "登录页",             # 目标分组名称
      "trigger_name": "登录按钮"        # 触发元素名称
    }
  ]
}
```

---

**创建 Web 流接口：POST /api/elements/web-flows**

请求体

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| from_group_id | integer | 是 | 源 Web 分组 ID（须非目录） |
| to_group_id | integer | 是 | 目标 Web 分组 ID（须非目录） |
| trigger_element_id | integer | 否 | 触发元素 ID（须属于源/目标分组） |
| trigger_action | string | 否 | 触发动作，默认 click |

成功响应（200）

```json
{
  "status": true
}
```

错误码与文案

| HTTP | message | 触发条件 |
|---|---|---|
| 400 | from_group_id 和 to_group_id 必填 | 任一缺失 |
| 400 | 分组不存在，只能使用 Web 元素分组（el_web_groups） | 分组不存在 |
| 400 | 目录节点不能作为流的端点，请选择具体的页面（非目录） | 端点是目录 |
| 400 | 触发元素必须属于源页面或目标页面 | 触发元素不属于两端 |
| 400 | 触发元素不存在 | trigger_element_id 不存在 |
| 405 | method not allowed | 非 GET/POST |

---

**删除 Web 流接口：DELETE /api/elements/web-flows/{flow_id}**

无请求体。成功响应（200）`{status: true}`。

---

### 4.7 API 分组 api-groups（legacy）

与 4.5 Web 分组结构同构，差异：字段 `element_count` → `endpoint_count`、写库目标 `el_api_groups`。

**API 分组列表接口：GET /api/elements/api-groups**

成功响应（200）

```json
{
  "status": true,
  "groups": [
    {
      "id": 1,
      "name": "用户中心",
      "parent_id": null,
      "is_folder": true,
      "sort_order": 0,
      "endpoint_count": 2,              # 直属端点数量
      "child_count": 0,                 # 子分组数量
      "created_at": "2026-08-21 10:00:00"
    }
  ]
}
```

**创建 API 分组接口：POST /api/elements/api-groups/create**

请求体：`name`（必填）、`parent_id`（否）、`is_folder`（否）、`sort_order`（否）。成功响应（200）`{status: true, group: {...}}`。错误码同 4.5 创建 Web 分组（400 invalid JSON / 400 分组名称必填 / 400 只能将分组添加在目录下 / 404 父级分组不存在 / 500 创建失败）。

**批量移动 API 分组接口：POST /api/elements/api-groups/batch-move**

请求体：`group_ids`（必填）、`parent_id`（否，""/0/"0"/"__root__"=根）。成功响应（200）`{status: true, moved: N}`。错误码同 4.5 批量移动。

**重命名 API 分组接口：PUT /api/elements/api-groups/{group_id}**

请求体：`name`（必填）。成功响应（200）`{status: true, group: {...}}`。错误码：404 分组不存在 / 400 invalid JSON / 400 名称不能为空。

**删除 API 分组接口：DELETE /api/elements/api-groups/{group_id}**

无请求体。成功响应（200）`{status: true}`。错误码：404 分组不存在。

---

### 4.8 API 端点 api-endpoints（legacy）

**API 端点列表接口：GET /api/elements/api-endpoints**

查询参数（可选）：`search`（name/url/description/tags 模糊）、`method`（大写精确）、`is_test_point`（"1"/"true"）、`group_id`（""/"null"=未分组）。成功响应（200）

```json
{
  "status": true,
  "endpoints": [
    {
      "id": 9,                          # 端点 ID
      "name": "查询用户",               # 接口名称
      "method": "GET",                  # 请求方法
      "url": "/api/user/{id}",          # 接口 URL
      "headers": {},                    # 请求头（JSON 对象）
      "request_body_schema": {},        # 请求体结构（JSON 对象）
      "response_body_schema": {},       # 响应体结构（JSON 对象）
      "description": "按 ID 查询用户",  # 描述
      "tags": "用户",                   # 标签
      "is_test_point": true,            # 是否测试点
      "group_id": 1,                    # 所属分组 ID（可为 null）
      "created_at": "2026-08-21 10:00:00",
      "updated_at": "2026-08-21 10:00:00"
    }
  ],
  "total": 1                            # 端点总数
}
```

---

**创建 API 端点接口：POST /api/elements/api-endpoints/create**

请求体

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| name | string | 是 | 接口名称 |
| method | string | 否 | 请求方法，默认 GET（5 选 1） |
| url | string | 是 | 接口 URL（非空） |
| headers | object | 否 | 请求头，默认 {} |
| request_body_schema | object | 否 | 请求体结构，默认 {} |
| response_body_schema | object | 否 | 响应体结构，默认 {} |
| description | string | 否 | 描述 |
| tags | string | 否 | 标签 |
| is_test_point | boolean | 否 | 是否测试点，默认 false |
| group_id | integer | 否 | 所属分组 ID |

成功响应（200）

```json
{
  "status": true,
  "endpoint": {
    "id": 10,
    "name": "创建用户",
    "method": "POST",
    "url": "/api/user",
    "headers": {},
    "request_body_schema": {},
    "response_body_schema": {},
    "description": "",
    "tags": "",
    "is_test_point": false,
    "group_id": 1,
    "created_at": "2026-08-21 11:00:00",
    "updated_at": "2026-08-21 11:00:00"
  }
}
```

错误码与文案

| HTTP | message | 触发条件 |
|---|---|---|
| 400 | invalid JSON | 请求体非合法 JSON |
| 400 | 接口名称必填 | name 为空 |
| 400 | 无效的请求方法 | method 非 GET/POST/PUT/DELETE/PATCH |
| 400 | 接口 URL 必填 | url 为空 |
| 500 | {e} | 其它异常 |

---

**更新 API 端点接口：PUT /api/elements/api-endpoints/{el_id}**

请求体（字段任选，只更新传入字段，同「创建」字段 + `group_id`）。成功响应（200）`{status: true, endpoint: {...}}`。错误码：404 接口不存在 / 400 invalid JSON / 405 method not allowed。

**删除 API 端点接口：DELETE /api/elements/api-endpoints/{el_id}**

无请求体。成功响应（200）`{status: true}`。错误码：404 接口不存在 / 405 method not allowed。

---

## 5. 字段/口径差异备注（router vs legacy）

| 维度 | router（标准信封） | legacy（平铺信封） |
|---|---|---|
| 路径尾斜杠 | 带 | 不带 |
| 成功信封 | {status: true, data} | {status: true, <资源键>} |
| 失败信封 | {status: false, message} | {status: false, message}（部分端点 500 无 message） |
| 删除成功 | 204 No Content | 200 {status: true} |
| Web 元素创建校验 | 仅 name 必填 + locator_type 合法 | name/locator_value 必填 + locator_type 合法 |
| Web 元素批量导入 | 不写入 tags；返回 {created} | 写入 tags；返回 {saved, skipped, errors} |
| API 端点创建校验 | 仅 name 必填 + method 合法 | name/url 必填 + method 合法 |
| 分组批量移动字段 | target_parent_id | parent_id |
| 分组列表形态 | 顶层树（children 递归） | 平铺数组 |
| 快照导入 | —（无此端点） | 标准 {status, data} 信封（新端点特例） |

> 本文以实际代码为准：字段名、文案均取自 `views.py`/`views_drf.py`/`serializers.py`/`api.py`/`page_tree.py`/`api_snapshot.py` 原文。
