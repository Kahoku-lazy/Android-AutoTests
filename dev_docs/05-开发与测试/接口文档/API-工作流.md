# API-工作流 — /api/workflow/*

> 工作流模块（apps/workflow）REST 接口文档：原型 / 编排目录 / 文档（VueFlow 画布数据）CRUD、导入导出、移动。
> 真相源：`apps/workflow/urls.py` + `views.py`（legacy 平铺）+ `views_api.py`（DRF router）+ `serializers.py` + `api.py` + `models.py`。
> 本模块无 `views_drf.py`；DRF 端点集中在 `views_api.py`，legacy 端点集中在 `views.py`。

## 1. 总览

| 接口 | 方法 | 鉴权 | 说明 |
|---|---|---|---|
| 原型列表接口 | GET /api/workflow/prototypes/ | 需登录(Bearer) | 原型列表（含 doc_count） |
| 原型创建接口 | POST /api/workflow/prototypes/ | 需登录(Bearer) | 新建原型 |
| 原型详情接口 | GET /api/workflow/prototypes/{id}/ | 需登录(Bearer) | 原型详情 |
| 原型更新接口 | PUT/PATCH /api/workflow/prototypes/{id}/ | 需登录(Bearer) | 更新名称/描述 |
| 原型删除接口 | DELETE /api/workflow/prototypes/{id}/ | 需登录(Bearer) | 级联删除其下目录与文档 |
| 目录列表接口 | GET /api/workflow/directories/ | 需登录(Bearer) | flat + tree；可 `?prototype_id=` |
| 目录创建接口 | POST /api/workflow/directories/ | 需登录(Bearer) | 新建目录（须 `prototype_id` 或 `parent_id`） |
| 目录详情接口 | GET /api/workflow/directories/{id}/ | 需登录(Bearer) | 目录详情 |
| 目录更新接口 | PUT/PATCH /api/workflow/directories/{id}/ | 需登录(Bearer) | 更新目录 |
| 目录删除接口 | DELETE /api/workflow/directories/{id}/ | 需登录(Bearer) | 级联删除目录及其文档 |
| 目录移动接口 | POST /api/workflow/directories/{id}/move/ | 需登录(Bearer) | 移动目录（禁止跨原型/自身/子孙） |
| 文档列表接口 | GET /api/workflow/documents/ | 需登录(Bearer) | 可 `?prototype_id=&directory_id=` |
| 文档创建接口 | POST /api/workflow/documents/ | 需登录(Bearer) | 须 `prototype_id`（或目录归属） |
| 文档导入接口 | POST /api/workflow/documents/_import/ | 需登录(Bearer) | envelope 含 `prototype_id` |
| 文档详情接口 | GET /api/workflow/documents/{doc_id}/ | 需登录(Bearer) | 文档详情（含 config） |
| 文档更新接口 | PUT/PATCH /api/workflow/documents/{doc_id}/ | 需登录(Bearer) | 更新文档 |
| 文档删除接口 | DELETE /api/workflow/documents/{doc_id}/ | 需登录(Bearer) | 删除文档 |
| 文档导出接口 | GET /api/workflow/documents/{doc_id}/export/ | 需登录(Bearer) | envelope 含 `prototype_id` |
| 文档移动接口 | POST /api/workflow/documents/{doc_id}/move/ | 需登录(Bearer) | 同原型内移动 |
| 原型列表接口(legacy) | GET /api/workflow/prototypes | 需登录(Bearer) | 平铺 `{status, prototypes}` |
| 原型创建接口(legacy) | POST /api/workflow/prototypes/create | 需登录(Bearer) | 平铺 `{status, prototype}` |
| 原型详情/更新/删除(legacy) | GET/POST/DELETE /api/workflow/prototypes/{id} | 需登录(Bearer) | 平铺信封 |
| 目录列表接口(legacy) | GET /api/workflow/directories | 需登录(Bearer) | `?prototype_id=`；平铺 flat + tree |
| 目录创建接口(legacy) | POST /api/workflow/directories/create | 需登录(Bearer) | body 含 `prototype_id` |
| 目录移动接口(legacy) | POST /api/workflow/directories/{dir_id}/move | 需登录(Bearer) | 平铺信封 |
| 目录更新/删除接口(legacy) | POST /api/workflow/directories/{dir_id} | 需登录(Bearer) | action=update/delete |
| 文档列表接口(legacy) | GET /api/workflow/documents | 需登录(Bearer) | `?prototype_id=&directory_id=&doc_type=` |
| 文档创建/更新接口(legacy) | POST /api/workflow/documents/create | 需登录(Bearer) | body 含 `prototype_id` |
| 文档导入接口(legacy) | POST /api/workflow/documents/import | 需登录(Bearer) | envelope/`prototype_id` |
| 文档导出接口(legacy) | GET /api/workflow/documents/{doc_id}/export | 需登录(Bearer) | 平铺 / 附件下载 |
| 文档移动接口(legacy) | POST /api/workflow/documents/{doc_id}/move | 需登录(Bearer) | 平铺信封 |
| 文档详情接口(legacy) | GET /api/workflow/documents/{doc_id} | 需登录(Bearer) | 平铺信封 |
| 文档更新接口(legacy) | PUT /api/workflow/documents/{doc_id} | 需登录(Bearer) | 平铺信封 |
| 文档删除接口(legacy) | DELETE /api/workflow/documents/{doc_id} | 需登录(Bearer) | 平铺信封 |

## 2. 通用约定

- **基础路径**：`/api/workflow/`（`config/urls.py` 挂载 `apps.workflow.urls`）。
- **层级**：`WorkflowPrototype`（原型）→ `WorkflowDirectory`（目录）→ `WorkflowDocument`（页面流）。
- **尾斜杠**：DRF router 路径**带尾斜杠**；legacy 路径**不带尾斜杠**。二者并存、行为一致。
- **响应信封（双口径，本模块特例 ARCH-09）**：
  - router 路径走全局标准信封：成功 `{status: true, data}`，失败 `{status: false, message}`。
  - legacy 平铺路径：`{status, prototype|prototypes|directory|document|documents|directories|tree|envelope, ...}`，**无 `data` 层**。
- **鉴权**：全部端点需登录。
- **无分页**：列表返回完整数组。
- **doc_type 仅支持 `page_flow`**。
- **Content-Type**：`application/json`。

---

## 2.1 原型（router：`/api/workflow/prototypes/`）

### 列表：GET /api/workflow/prototypes/

成功 `data` 为数组，元素字段：`id` / `name` / `description` / `doc_count` / `created_at` / `updated_at`。

### 创建：POST /api/workflow/prototypes/

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| name | string | 是 | 原型名称（全局唯一） |
| description | string | 否 | 描述 |

错误：400 原型名称不能为空；409 同名原型已存在。

### 详情 / 更新 / 删除

- GET `/api/workflow/prototypes/{id}/`
- PUT/PATCH：可改 `name` / `description`
- DELETE：级联删除该原型下全部目录与文档

### Legacy

- GET `/api/workflow/prototypes` → `{status, prototypes}`
- POST `/api/workflow/prototypes/create` → `{status, prototype}`
- GET/POST/DELETE `/api/workflow/prototypes/{id}` → 平铺信封（POST 可 `action=delete`）

---

## 3. 目录（router 标准端点，信封 `{status, data}`）

### 3.1 目录列表接口：GET /api/workflow/directories/

| 项 | 值 |
|---|---|
| 鉴权 | 需登录(Bearer) |
| Content-Type | 无需请求体 |

#### 查询参数

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| prototype_id | int | 否 | 按原型过滤；缺省返回全部（迁移兼容） |
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
| doc_type | string | 否 | 仅 `page_flow`；其它值返回空列表 |

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
| 404 | 没有找到。 | 文档不存在 |

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
| 400 | 无法识别 doc_type（仅支持 page_flow） | doc_type 缺失且无法识别为页面流 |
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
| 404 | 文档不存在 | 文档不存在或非 page_flow |

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
4. **非 HTTP 数据出口（不入本文档端点表）**：`api.py` 导出的 `get_document_digest`、`list_document_summaries` 仅供 AI 工具进程内只读直调；`list_document_summaries` 支持 `prototype_id` 过滤。
5. **本模块无 WS/SSE**（见 `apps/workflow/AGENTS.md`）。
6. **`doc_type` 仅 `page_flow`**：其它类型新建/导入 400，列表查询返回空。
7. **原型作用域**：目录/文档须归属 `prototype_id`；禁止跨原型移动；历史数据已迁入「默认原型」。

---

## 8. 错误文案汇总（来自 api.py / views.py 实际值）

| 触发域 | 文案 |
|---|---|
| 目录名 | 目录名不能为空 / 同级已存在目录「{name}」/ 同级目录名冲突 |
| 目录引用 | 目录不存在 / 父目录不存在 / 目标目录不存在 |
| 目录移动 | 不能将目录移入自身 / 不能将目录移入其子目录 |
| 文档标题 | 标题不能为空 |
| 文档类型 | doc_type 必须是 page_flow |
| 原型 | 原型名称不能为空 / 同名原型已存在 / 原型不存在 / prototype_id 不能为空 / 原型不存在 |
| 文档引用 | 文档不存在 / 文档不存在: {doc_id} / doc_id 已存在: {doc_id} |
| 导入 | 导入内容必须是 JSON 对象 / 无法识别 doc_type（仅支持 page_flow） / doc_id 已存在，禁止重复导入: {doc_id} / prototype_id 无效 |
| 跨原型 | 不能跨原型移动目录 / 不能跨原型移动文档 / 父目录不属于该原型 / 目录不属于该原型 |
| 通用(legacy) | method not allowed（405） |
| 鉴权 | 请先登录 / 登录已过期或令牌无效（401，中间件） |
