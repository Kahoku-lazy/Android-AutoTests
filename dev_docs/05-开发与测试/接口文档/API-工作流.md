# API-工作流 — /api/workflow/*

> 工作流模块（apps/workflow）REST 接口文档：编排目录 / 文档（VueFlow 画布数据）CRUD、导入导出、移动。
> 真相源：`apps/workflow/urls.py` + `views.py`（legacy 平铺）+ `views_api.py`（DRF router）+ `serializers.py` + `api.py` + `models.py`。
> 本模块无 `views_drf.py`；DRF 端点集中在 `views_api.py`，legacy 端点集中在 `views.py`。

## 1. 总览

| 接口 | 方法 | 鉴权 | 说明 |
|---|---|---|---|
| 目录列表接口 | GET /api/workflow/directories/ | 需登录(Bearer) | 同时返回 flat 列表 + 递归树 |
| 目录创建接口 | POST /api/workflow/directories/ | 需登录(Bearer) | 新建目录 |
| 目录详情接口 | GET /api/workflow/directories/{id}/ | 需登录(Bearer) | 目录详情 |
| 目录更新接口 | PUT/PATCH /api/workflow/directories/{id}/ | 需登录(Bearer) | 更新目录 |
| 目录删除接口 | DELETE /api/workflow/directories/{id}/ | 需登录(Bearer) | 级联删除目录及其文档 |
| 目录移动接口 | POST /api/workflow/directories/{id}/move/ | 需登录(Bearer) | 移动目录（禁止移入自身/子孙） |
| 文档列表接口 | GET /api/workflow/documents/ | 需登录(Bearer) | 页面流文档列表（不含 config） |
| 文档创建接口 | POST /api/workflow/documents/ | 需登录(Bearer) | 新建文档（自动生成 doc_id） |
| 文档导入接口 | POST /api/workflow/documents/_import/ | 需登录(Bearer) | 导入 envelope JSON（注意下划线路径） |
| 文档详情接口 | GET /api/workflow/documents/{doc_id}/ | 需登录(Bearer) | 文档详情（含 config） |
| 文档更新接口 | PUT/PATCH /api/workflow/documents/{doc_id}/ | 需登录(Bearer) | 更新文档 |
| 文档删除接口 | DELETE /api/workflow/documents/{doc_id}/ | 需登录(Bearer) | 删除文档 |
| 文档导出接口 | GET /api/workflow/documents/{doc_id}/export/ | 需登录(Bearer) | 导出 envelope JSON，可附件下载 |
| 文档移动接口 | POST /api/workflow/documents/{doc_id}/move/ | 需登录(Bearer) | 移动文档到目录 |
| 目录列表接口(legacy) | GET /api/workflow/directories | 需登录(Bearer) | 平铺信封，flat + tree |
| 目录创建接口(legacy) | POST /api/workflow/directories/create | 需登录(Bearer) | 平铺信封 |
| 目录移动接口(legacy) | POST /api/workflow/directories/{dir_id}/move | 需登录(Bearer) | 平铺信封 |
| 目录更新/删除接口(legacy) | POST /api/workflow/directories/{dir_id} | 需登录(Bearer) | 平铺信封，action=update/delete |
| 文档列表接口(legacy) | GET /api/workflow/documents | 需登录(Bearer) | 平铺信封，?directory_id=&doc_type= |
| 文档创建/更新接口(legacy) | POST /api/workflow/documents/create | 需登录(Bearer) | 平铺信封，传 doc_id 且存在则更新 |
| 文档导入接口(legacy) | POST /api/workflow/documents/import | 需登录(Bearer) | 平铺信封，?overwrite=1 |
| 文档导出接口(legacy) | GET /api/workflow/documents/{doc_id}/export | 需登录(Bearer) | 平铺信封 / 附件下载 |
| 文档移动接口(legacy) | POST /api/workflow/documents/{doc_id}/move | 需登录(Bearer) | 平铺信封 |
| 文档详情接口(legacy) | GET /api/workflow/documents/{doc_id} | 需登录(Bearer) | 平铺信封 |
| 文档更新接口(legacy) | PUT /api/workflow/documents/{doc_id} | 需登录(Bearer) | 平铺信封 |
| 文档删除接口(legacy) | DELETE /api/workflow/documents/{doc_id} | 需登录(Bearer) | 平铺信封 |

## 2. 通用约定

- **基础路径**：`/api/workflow/`（`config/urls.py` 挂载 `apps.workflow.urls`）。
- **尾斜杠**：DRF router 路径**带尾斜杠**（如 `/directories/`、`/documents/{doc_id}/`）；legacy 路径**不带尾斜杠**（如 `/directories`、`/documents/{doc_id}`）。二者并存、行为一致（见 `apps/workflow/AGENTS.md`）。
- **响应信封（双口径，本模块特例 ARCH-09）**：
  - router 路径（`directories` / `documents` ViewSet）走全局标准信封：成功 `{status: true, data}`，失败 `{status: false, message}`（`EnvelopeJSONRenderer` 包裹，错误取 DRF `detail` 或首个字段错误）。
  - legacy 平铺路径为**平铺**信封：`{status, directory|document|documents|directories|tree|envelope, ...}`，**无 `data` 层**。禁止新增/改造（已登记 ARCH-09）。
- **鉴权**：全部端点需登录。`JWTAuthenticationMiddleware` 校验 `Authorization: Bearer <access_token>`；未带/无效令牌返回 401 `{status: false, message: "请先登录"}` 或 `{status: false, message: "登录已过期或令牌无效"}`。DRF 层另有 `IsAuthenticated` + `shared.auth.drf_auth.JWTAuthentication`。
- **无分页**：`REST_FRAMEWORK` 未配置分页，router 列表返回完整数组。
- **doc_type 仅支持 `page_flow`**：`test_case` 已下线（历史值，常量仅供清库/兼容）；新建/导入 `test_case` 被拒绝，`GET /documents` 显式请求 `doc_type=test_case` 返回空列表。
- **Content-Type**：`application/json`；请求体为 JSON。

---

## 3. 目录（router 标准端点，信封 `{status, data}`）

### 3.1 目录列表接口：GET /api/workflow/directories/

| 项 | 值 |
|---|---|
| 鉴权 | 需登录(Bearer) |
| Content-Type | 无需请求体 |

无请求体。同时返回 `directories`（flat 列表）与 `tree`（递归树）。

#### 成功响应（200）

```json
{
  "status": true,                                # 恒为 true
  "data": {
    "directories": [                             # flat 列表（含根与子目录）
      {
        "id": 1,                                 # 目录 ID
        "name": "登录模块",                       # 目录名
        "parent_id": null,                       # 父目录 ID；null 表示根
        "sort_order": 0,                         # 排序值
        "created_at": "2026-09-02T17:20:48.150265",  # 创建时间（ISO）
        "updated_at": "2026-09-02T17:20:48.150295",  # 更新时间（ISO）
        "doc_count": 3                           # 该目录直接文档数
      }
    ],
    "tree": [                                    # 递归目录树（仅根节点为顶层）
      {
        "id": 1,                                 # 目录 ID
        "name": "登录模块",                       # 目录名
        "parent_id": null,                       # 父目录 ID
        "sort_order": 0,                         # 排序值
        "doc_count": 3,                          # 该目录直接文档数
        "created_at": "2026-09-02T17:20:48.150265",
        "updated_at": "2026-09-02T17:20:48.150295",
        "children": [                            # 子目录（递归同结构）
          {
            "id": 2,
            "name": "子目录",
            "parent_id": 1,
            "sort_order": 0,
            "doc_count": 1,
            "created_at": "2026-09-02T17:20:48.150265",
            "updated_at": "2026-09-02T17:20:48.150295",
            "children": [],
            "documents": [                       # 该目录下的页面流文档摘要
              {
                "doc_id": "WF-PF-20260902-172048-ABCD",  # 文档业务 ID
                "title": "登录流程",                       # 文档标题
                "doc_type": "page_flow",                  # 文档类型
                "updated_at": "2026-09-02T17:20:48.150295" # 更新时间（ISO）
              }
            ]
          }
        ],
        "documents": []                          # 根目录直接文档摘要（同上结构）
      }
    ]
  }
}
```

#### 错误码与文案

| HTTP | message | 触发条件 |
|---|---|---|
| 401 | 请先登录 | 无 Bearer 令牌（中间件） |
| 401 | 登录已过期或令牌无效 | 令牌无效/过期 |

---

### 3.2 目录创建接口：POST /api/workflow/directories/

| 项 | 值 |
|---|---|
| 鉴权 | 需登录(Bearer) |
| Content-Type | application/json |

#### 请求体

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| name | string | 是 | 目录名（非空；同级唯一，`unique_together(parent, name)`） |
| parent_id | int | 否 | 父目录 ID；缺省为根目录 |
| sort_order | int | 否 | 排序值，默认 0 |

#### 成功响应（201）

```json
{
  "status": true,                                # 恒为 true
  "data": {
    "id": 3,                                     # 新目录 ID
    "name": "支付模块",                           # 目录名
    "parent_id": 1,                              # 父目录 ID；null 为根
    "parent_name": "登录模块",                    # 父目录名（无父目录时不返回）
    "sort_order": 0,                             # 排序值
    "created_at": "2026-09-02T17:20:48.150265",  # 创建时间（ISO）
    "updated_at": "2026-09-02T17:20:48.150295"   # 更新时间（ISO）
  }
}
```

> 注意：`WorkflowDirectorySerializer` 声明了 `doc_count`，但模型无该属性/注解，实际响应中**不返回** `doc_count`（详见 §7 已知差异）。

#### 错误码与文案

| HTTP | message | 触发条件 |
|---|---|---|
| 400 | 该字段是必填项。 | name 缺省（DRF serializer） |
| 400 | 这个字段不能为空。 | name 为空串（DRF serializer） |
| 400 | 目录名不能为空 | name 去空格后为空（api.py） |
| 400 | 父目录不存在 | parent_id 对应目录不存在（api.py） |
| 400 | 同级已存在目录「{name}」 | 同级已存在同名目录（api.py） |

---

### 3.3 目录详情接口：GET /api/workflow/directories/{id}/

| 项 | 值 |
|---|---|
| 鉴权 | 需登录(Bearer) |

路径参数 `{id}` 为目录主键。无请求体。

#### 成功响应（200）

```json
{
  "status": true,
  "data": {
    "id": 3,                                     # 目录 ID
    "name": "支付模块",                           # 目录名
    "parent_id": 1,                              # 父目录 ID；null 为根
    "parent_name": "登录模块",                    # 父目录名（无父目录时不返回）
    "sort_order": 0,                             # 排序值
    "created_at": "2026-09-02T17:20:48.150265",
    "updated_at": "2026-09-02T17:20:48.150295"
  }
}
```

#### 错误码与文案

| HTTP | message | 触发条件 |
|---|---|---|
| 404 | 没有找到。 | 目录不存在（DRF get_object 默认） |

---

### 3.4 目录更新接口：PUT/PATCH /api/workflow/directories/{id}/

| 项 | 值 |
|---|---|
| 鉴权 | 需登录(Bearer) |
| Content-Type | application/json |

#### 请求体

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| name | string | 否(PATCH)/是(PUT) | 目录名（非空；同级唯一） |
| parent_id | int/null | 否 | 父目录 ID；传 `null` 移到根 |
| sort_order | int | 否 | 排序值 |

#### 成功响应（200）

同 §3.3 目录详情响应（`data` 为更新后的目录，字段一致，`parent_name` 仅在有父目录时返回）。

#### 错误码与文案

| HTTP | message | 触发条件 |
|---|---|---|
| 404 | 没有找到。 | 目录不存在 |
| 400 | 这个字段不能为空。 | name 为空串（DRF serializer） |
| 400 | 父目录不存在 | parent_id 对应目录不存在（api.py） |
| 400 | 同级目录名冲突 | 移动导致同级同名（api.py） |

---

### 3.5 目录删除接口：DELETE /api/workflow/directories/{id}/

| 项 | 值 |
|---|---|
| 鉴权 | 需登录(Bearer) |

路径参数 `{id}` 为目录主键。无请求体。级联删除子目录内文档（`api.delete_directory`）。

#### 成功响应（204）

无响应体（HTTP 204 No Content，不套信封）。

#### 错误码与文案

| HTTP | message | 触发条件 |
|---|---|---|
| 404 | 没有找到。 | 目录不存在 |

---

### 3.6 目录移动接口：POST /api/workflow/directories/{id}/move/

| 项 | 值 |
|---|---|
| 鉴权 | 需登录(Bearer) |
| Content-Type | application/json |

#### 请求体

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| parent_id | int/null | 否 | 目标父目录 ID；`null`/`""`/`"null"` 表示移到根 |

#### 成功响应（200）

```json
{
  "status": true,
  "data": {
    "id": 2,                                     # 目录 ID
    "name": "子目录",                             # 目录名
    "parent_id": null,                           # 移动后的父目录 ID
    "sort_order": 0,                             # 排序值
    "created_at": "2026-09-02T17:20:48.150265",
    "updated_at": "2026-09-02T17:20:48.150295",
    "doc_count": 1                               # 该目录直接文档数（本端点含此字段）
  }
}
```

> 移动端点返回 `serialize_directory`（**含 `doc_count`**），与 §3.2~§3.4 的 serializer 输出（不含 `doc_count`）不一致，以实际为准。

#### 错误码与文案

| HTTP | message | 触发条件 |
|---|---|---|
| 400 | 目录不存在 | 待移动目录不存在 |
| 400 | 不能将目录移入自身 | parent_id 等于自身 |
| 400 | 目标目录不存在 | 目标父目录不存在 |
| 400 | 不能将目录移入其子目录 | 目标为其子孙目录 |
| 400 | 同级目录名冲突 | 移动后同级同名 |

---

## 4. 文档（router 标准端点，信封 `{status, data}`）

文档以 `doc_id`（业务唯一 ID，格式 `WF-PF-YYYYMMDD-HHMMSS-XXXX`）为 natural key。router 详情/更新/删除/移动/导出的路径参数为 `{doc_id}`。

### 4.1 文档列表接口：GET /api/workflow/documents/

| 项 | 值 |
|---|---|
| 鉴权 | 需登录(Bearer) |

#### 查询参数

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| directory_id | int | 否 | 目录 ID；缺省返回全部（含孤儿） |
| doc_type | string | 否 | 仅 `page_flow`；传 `test_case` 或其他值返回空列表 |

#### 成功响应（200）

```json
{
  "status": true,
  "data": [                                      # 文档列表数组（无分页）
    {
      "id": 9,                                   # 文档主键 ID
      "doc_id": "WF-PF-20260902-172048-ABCD",    # 文档业务唯一 ID
      "title": "登录流程",                        # 标题
      "doc_type": "page_flow",                   # 文档类型
      "directory_id": 3,                         # 所属目录 ID；null 为未分类
      "description": "登录页面流",                # 描述
      "created_at": "2026-09-02T17:21:49.393585", # 创建时间（ISO）
      "updated_at": "2026-09-02T17:21:49.393618"  # 更新时间（ISO）
    }
  ]
}
```

> 列表序列化器（`WorkflowDocumentListSerializer`）**不含 `config`**（体积大）。

#### 错误码与文案

| HTTP | message | 触发条件 |
|---|---|---|
| 401 | 请先登录 | 无 Bearer 令牌 |

---

### 4.2 文档创建接口：POST /api/workflow/documents/

| 项 | 值 |
|---|---|
| 鉴权 | 需登录(Bearer) |
| Content-Type | application/json |

#### 请求体

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| title | string | 是 | 标题（非空） |
| doc_type | string | 是 | 仅 `page_flow` |
| config | object | 否 | VueFlow 画布配置 JSON（写库时序列化为 `config_json` 字符串） |
| directory_id | int | 否 | 所属目录 ID |
| description | string | 否 | 描述，默认 "" |

#### 成功响应（201）

```json
{
  "status": true,
  "data": {
    "id": 9,                                      # 文档主键 ID
    "doc_id": "WF-PF-20260902-172048-ABCD",       # 自动生成的业务 ID
    "title": "登录流程",                           # 标题
    "doc_type": "page_flow",                      # 文档类型
    "directory_id": 3,                            # 所属目录 ID
    "description": "登录页面流",                   # 描述
    "config": {                                   # 画布配置（JSON 对象）
      "nodes": [{"id": "n1"}],
      "links": []
    },
    "created_at": "2026-09-02T17:21:49.393585",
    "updated_at": "2026-09-02T17:21:49.393618"
  }
}
```

#### 错误码与文案

| HTTP | message | 触发条件 |
|---|---|---|
| 400 | 标题不能为空 | title 去空格后为空（api.py） |
| 400 | 工作流已不再支持积木测试用例，请使用用例管理模块 | doc_type=test_case |
| 400 | doc_type 必须是 page_flow | doc_type 非 page_flow |
| 400 | 目录不存在 | directory_id 对应目录不存在 |

---

### 4.3 文档详情接口：GET /api/workflow/documents/{doc_id}/

| 项 | 值 |
|---|---|
| 鉴权 | 需登录(Bearer) |

路径参数 `{doc_id}` 为文档业务 ID。无请求体。

#### 成功响应（200）

```json
{
  "status": true,
  "data": {
    "id": 9,
    "doc_id": "WF-PF-20260902-172048-ABCD",
    "title": "登录流程",
    "doc_type": "page_flow",
    "directory_id": 3,
    "description": "登录页面流",
    "config": {                                   # 画布配置（JSON 对象）
      "nodes": [{"id": "n1"}],
      "links": []
    },
    "created_at": "2026-09-02T17:21:49.393585",
    "updated_at": "2026-09-02T17:21:49.393618"
  }
}
```

#### 错误码与文案

| HTTP | message | 触发条件 |
|---|---|---|
| 404 | 没有找到。 | 文档不存在或 doc_type=test_case（get_object） |

---

### 4.4 文档更新接口：PUT/PATCH /api/workflow/documents/{doc_id}/

| 项 | 值 |
|---|---|
| 鉴权 | 需登录(Bearer) |
| Content-Type | application/json |

#### 请求体

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| title | string | 否(PATCH)/是(PUT) | 标题 |
| doc_type | string | 否 | 仅 `page_flow` |
| config | object | 否 | 画布配置 JSON |
| directory_id | int | 否 | 所属目录 ID |
| description | string | 否 | 描述 |

#### 成功响应（200）

同 §4.3 文档详情响应（`data` 为更新后的文档，字段一致）。

#### 错误码与文案

| HTTP | message | 触发条件 |
|---|---|---|
| 404 | 没有找到。 | 文档不存在（get_object） |
| 400 | 标题不能为空 | title 为空 |
| 400 | 工作流已不再支持积木测试用例，请使用用例管理模块 | doc_type=test_case |
| 400 | doc_type 必须是 page_flow | doc_type 非 page_flow |
| 400 | 目录不存在 | directory_id 对应目录不存在 |

---

### 4.5 文档删除接口：DELETE /api/workflow/documents/{doc_id}/

| 项 | 值 |
|---|---|
| 鉴权 | 需登录(Bearer) |

无请求体。

#### 成功响应（204）

无响应体（HTTP 204 No Content）。

#### 错误码与文案

| HTTP | message | 触发条件 |
|---|---|---|
| 404 | 没有找到。 | 文档不存在 |

---

### 4.6 文档导入接口：POST /api/workflow/documents/_import/

| 项 | 值 |
|---|---|
| 鉴权 | 需登录(Bearer) |
| Content-Type | application/json |

> ⚠️ **路径真相**：实际注册的 router 路径为 `/documents/_import/`（**带下划线**，来自方法名 `_import`），而非 `views_api.py` docstring 中的 `/documents/import/`。legacy 的导入路径才是 `/documents/import`（无下划线、无尾斜杠）。

#### 查询参数

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| overwrite | string | 否 | `1`/`true`/`True` 时覆盖同 doc_id 文档 |

#### 请求体

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| envelope | object | 否 | 导出 envelope JSON；也可直接平铺传 envelope 字段（不加 `envelope` 包装） |

envelope 对象字段：

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| format | string | 否 | 固定 `workflow-doc-v1`（缺省按 v1 处理） |
| doc_id | string | 否 | 文档业务 ID；缺省自动生成 |
| doc_type | string | 否 | 仅 `page_flow`；缺省时若含 nodes 视为 page_flow |
| title | string | 否 | 标题（缺省取 name / "导入的文档"） |
| description | string | 否 | 描述 |
| directory_id | int | 否 | 所属目录 ID |
| config | object | 否 | 画布配置 JSON |

#### 成功响应（200/201）

```json
{
  "status": true,
  "data": {
    "id": 10,
    "doc_id": "WF-PF-20260902-172048-ABCD",
    "title": "导入的文档",
    "doc_type": "page_flow",
    "directory_id": null,
    "description": "",
    "config": {"nodes": [], "links": []},
    "created_at": "2026-09-02T17:21:49.393585",
    "updated_at": "2026-09-02T17:21:49.393618"
  }
}
```

> 新建返回 201，覆盖/更新返回 200（状态码随 `upsert_document` 结果）。

#### 错误码与文案

| HTTP | message | 触发条件 |
|---|---|---|
| 400 | 导入内容必须是 JSON 对象 | 请求体非 JSON 对象 |
| 400 | 工作流已不再支持积木测试用例导入，请使用用例管理模块 | 积木用例导入（format=testcase-scratch-v1 / doc_type=test_case / 含 blocks） |
| 400 | 无法识别 doc_type（仅支持 page_flow） | doc_type 缺失且无法识别 |
| 400 | 标题不能为空 | title 为空 |
| 400 | 目录不存在 | directory_id 对应目录不存在 |
| 409 | doc_id 已存在，禁止重复导入: {doc_id} | doc_id 已存在且 overwrite=false |
| 409 | doc_id 已存在: {doc_id} | 并发唯一冲突 |

---

### 4.7 文档导出接口：GET /api/workflow/documents/{doc_id}/export/

| 项 | 值 |
|---|---|
| 鉴权 | 需登录(Bearer) |

#### 查询参数

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| download | string | 否 | `1`/`true`/`True` 时以附件下载（非 JSON 信封） |

#### 成功响应（200，默认 JSON）

```json
{
  "status": true,
  "data": {
    "envelope": {                                # 导出 envelope（可直接回传给导入）
      "format": "workflow-doc-v1",               # 格式标识
      "doc_id": "WF-PF-20260902-172048-ABCD",    # 文档业务 ID
      "doc_type": "page_flow",                   # 文档类型
      "title": "登录流程",                        # 标题
      "description": "登录页面流",                # 描述
      "directory_id": 3,                         # 所属目录 ID
      "exported_at": "2026-09-02T17:21:49.393618", # 导出时间（ISO）
      "config": {"nodes": [], "links": []}       # 画布配置 JSON
    }
  }
}
```

#### 下载（`?download=1`）

返回 `application/json` 内容 + `Content-Disposition: attachment; filename="{doc_id}.json"`，**非 JSON 信封**（`HttpResponse` 附件下载）。

#### 错误码与文案

| HTTP | message | 触发条件 |
|---|---|---|
| 404 | 文档不存在 | 文档不存在或 doc_type=test_case |

---

### 4.8 文档移动接口：POST /api/workflow/documents/{doc_id}/move/

| 项 | 值 |
|---|---|
| 鉴权 | 需登录(Bearer) |
| Content-Type | application/json |

#### 请求体

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| directory_id | int/null | 否 | 目标目录 ID；`null`/`""`/`"null"` 移到根（未分类）；兼容 `parent_id` 字段 |

#### 成功响应（200）

```json
{
  "status": true,
  "data": {
    "id": 9,                                      # 文档主键 ID
    "doc_id": "WF-PF-20260902-172048-ABCD",       # 文档业务 ID
    "title": "登录流程",                           # 标题
    "doc_type": "page_flow",                      # 文档类型
    "directory_id": 5,                            # 移动后的目录 ID；null 为未分类
    "description": "登录页面流",                   # 描述
    "created_at": "2026-09-02T17:21:49.393585",
    "updated_at": "2026-09-02T17:21:49.393618"
  }
}
```

> 移动响应不含 `config`（`serialize_document(include_config=False)`）。

#### 错误码与文案

| HTTP | message | 触发条件 |
|---|---|---|
| 400 | 文档不存在 | 文档不存在 |
| 400 | 目录不存在 | 目标目录不存在 |

---

## 5. legacy 平铺端点（目录）

> 平铺信封 `{status, directory|directories|tree, ...}`，**无 `data` 层**；路径**不带尾斜杠**。行为与 router 对应端点一致。

### 5.1 目录列表：GET /api/workflow/directories

同 §3.1，但信封平铺：

```json
{
  "status": true,                                # 恒为 true
  "directories": [ /* 同 serialize_directory 结构 */ ],
  "tree": [ /* 同 get_directory_tree 结构 */ ]
}
```

| HTTP | message | 触发条件 |
|---|---|---|
| 405 | method not allowed | 方法非 GET |

### 5.2 目录创建：POST /api/workflow/directories/create

请求体同 §3.2（`name` / `parent_id` / `sort_order`）。

```json
{ "status": true, "directory": { "id": 3, "name": "支付模块", "parent_id": 1, "sort_order": 0, "created_at": "...", "updated_at": "...", "doc_count": 0 } }
```

> 201 创建成功；错误 400 文案与 §3.2 一致（目录名不能为空 / 父目录不存在 / 同级已存在目录「{name}」）。

### 5.3 目录移动：POST /api/workflow/directories/{dir_id}/move

请求体 `{ "parent_id": <int|null> }`（`null`/`""`/`"null"` 移到根）。

```json
{ "status": true, "directory": { "id": 2, "name": "子目录", "parent_id": null, "sort_order": 0, "created_at": "...", "updated_at": "...", "doc_count": 1 } }
```

> 错误 400 文案同 §3.6（目录不存在 / 不能将目录移入自身 / 目标目录不存在 / 不能将目录移入其子目录 / 同级目录名冲突）。

### 5.4 目录更新/删除：POST /api/workflow/directories/{dir_id}

一个端点承载两种操作，用请求体 `action` 区分。

#### 请求体

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| action | string | 否 | `update`（默认）/ `delete` |
| name | string | 否 | 更新时的目录名 |
| parent_id | int | 否 | 更新时的父目录 ID |

- `action=delete`：成功 `{ "status": true }`；失败 400 `{ "status": false, "message": "目录不存在" }`。
- `action=update`：成功 `{ "status": true, "directory": {...} }`（同 §5.3 结构）；失败 400 文案同 §3.2/§3.4（目录不存在 / 目录名不能为空 / 父目录不存在 / 同级目录名冲突）。

---

## 6. legacy 平铺端点（文档）

### 6.1 文档列表：GET /api/workflow/documents

查询参数 `directory_id` / `doc_type` 同 §4.1。

```json
{
  "status": true,
  "documents": [ /* serialize_document(include_config=False)，无 config */ ]
}
```

### 6.2 文档创建/更新：POST /api/workflow/documents/create

请求体：`doc_id`（可选，存在则更新）/ `title`（或 `name`）/ `doc_type` / `config` / `directory_id` / `description`。

```json
{ "status": true, "document": { "id": 9, "doc_id": "WF-PF-...", "title": "...", "doc_type": "page_flow", "directory_id": 3, "description": "...", "config": {...}, "created_at": "...", "updated_at": "..." } }
```

> 成功状态码 200（更新）/ 201（新建）；失败 `{ "status": false, "message": ... }`，状态码随 `upsert_document`（400/404/409），文案同 §4.2/§4.4。

### 6.3 文档导入：POST /api/workflow/documents/import

查询参数 `overwrite`、请求体（`{envelope:{...}}` 或直接平铺）同 §4.6。

```json
{ "status": true, "document": { ... } }
```

> 错误 400/409 文案同 §4.6。

### 6.4 文档导出：GET /api/workflow/documents/{doc_id}/export

同 §4.7，但默认 JSON 信封平铺：`{ "status": true, "envelope": {...} }`；`?download=1` 返回附件下载（非 JSON）。404 `{ "status": false, "message": "文档不存在" }`。

### 6.5 文档移动：POST /api/workflow/documents/{doc_id}/move

请求体 `{ "directory_id": <int|null> }`（兼容 `parent_id`）。成功 `{ "status": true, "document": {...} }`（无 config）；错误 400 文案同 §4.8。

### 6.6 文档详情/更新/删除：GET/PUT/DELETE /api/workflow/documents/{doc_id}

- **GET**：成功 `{ "status": true, "document": {...} }`（含 `config`）；404 `{ "status": false, "message": "文档不存在" }`。
- **PUT**：请求体同 §4.4；成功 `{ "status": true, "document": {...} }`；404 `{ "status": false, "message": "文档不存在" }`，其余错误 400/409 文案同 `upsert_document`。
- **DELETE**：成功 `{ "status": true }`；404 `{ "status": false, "message": "文档不存在" }`。
- 其他方法 405 `{ "status": false, "message": "method not allowed" }`。

---

## 7. 附注与已知差异

1. **router 导入路径带下划线**：`/documents/_import/`（方法名 `_import` 直接成为 URL 段），与 `views_api.py` docstring 中的 `/documents/import/` 不符，以 URL 注册为准。
2. **`doc_count` 字段不一致**：`WorkflowDirectorySerializer` 声明了 `doc_count`，但 `WorkflowDirectory` 模型无该属性且查询未 `annotate`，故 router 目录 create/retrieve/update 响应**实际不返回** `doc_count`；而列表/树/移动（走 `serialize_directory`）**返回** `doc_count`。
3. **信封双口径**：router 走 `{status, data}`；legacy 平铺（无 `data`）。两套路径并存，行为一致（ARCH-09）。
4. **非 HTTP 数据出口（不入本文档端点表）**：`api.py` 导出的 `build_page_flow_document`、`get_document_digest`、`list_document_summaries` 仅供 AI 工具进程内直调（同进程无 SSE/WS），未在 `urls.py` 注册，故无 HTTP 端点。
5. **本模块无 WS/SSE**（见 `apps/workflow/AGENTS.md`）。
6. **`test_case` 已下线**：新建/导入/读取均被拒绝或返回空，`doc_type` 仅 `page_flow`。

---

## 8. 错误文案汇总（来自 api.py / views.py 实际值）

| 触发域 | 文案 |
|---|---|
| 目录名 | 目录名不能为空 / 同级已存在目录「{name}」/ 同级目录名冲突 |
| 目录引用 | 目录不存在 / 父目录不存在 / 目标目录不存在 |
| 目录移动 | 不能将目录移入自身 / 不能将目录移入其子目录 |
| 文档标题 | 标题不能为空 |
| 文档类型 | doc_type 必须是 page_flow / 工作流已不再支持积木测试用例，请使用用例管理模块 |
| 文档引用 | 文档不存在 / 文档不存在: {doc_id} / doc_id 已存在: {doc_id} |
| 导入 | 导入内容必须是 JSON 对象 / 工作流已不再支持积木测试用例导入，请使用用例管理模块 / 无法识别 doc_type（仅支持 page_flow） / doc_id 已存在，禁止重复导入: {doc_id} |
| 通用(legacy) | method not allowed（405） |
| 鉴权 | 请先登录 / 登录已过期或令牌无效（401，中间件） |
