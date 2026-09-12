# API-设备检查器 — /api/inspector/*

> 设备检查器（device_inspector）快照化 REST 全集 7 个端点：抓取 / 列表 / 详情 / 结构分析 / 删除 / 保存到元素定位 / 页面只读回看。
> 真相源：`apps/device_inspector/urls.py` + `views.py` + `api.py` + `service.py`；元素落盘契约跨 `apps/element_locator/api_snapshot.py`。

## 1. 总览

| 接口 | 方法 | 鉴权 | 说明 |
|---|---|---|---|
| 快照抓取接口 | POST /api/inspector/capture | 需登录(Bearer) | 一键抓取（dump/OCR）→ 快照落库 |
| 快照列表接口 | GET /api/inspector/snapshots | 需登录(Bearer) | 快照列表（offset/limit，倒序） |
| 快照详情接口 | GET /api/inspector/snapshots/{id} | 需登录(Bearer) | 快照全量 JSON |
| 快照结构分析接口 | GET /api/inspector/snapshots/{id}/analyze | 需登录(Bearer) | 纯规则结构分区，不落库、无设备交互 |
| 快照删除接口 | DELETE /api/inspector/snapshots/{id}/delete | 需登录(Bearer) | 删除快照记录 + 截图/缩略图文件 |
| 元素保存接口 | POST /api/inspector/snapshots/{id}/save-elements | 需登录(Bearer) | 筛减保存到元素定位（经 element_locator api） |
| 页面只读视图接口 | GET /api/inspector/pages/{id} | 需登录(Bearer) | 元素定位已保存页面只读回看 |

## 2. 通用约定

- 路径**无尾斜杠**（尾斜杠经 `NormalizeTrailingSlashMiddleware` 规范化）。
- 响应信封：成功 `{status: true, data}`，失败 `{status: false, message}`（`EnvelopeJSONRenderer` 统一包裹）。
- **全部 7 个端点均需登录**，携带 `Authorization: Bearer <access_token>`（DRF 默认 `IsAuthenticated`，无 AllowAny 覆盖；未登录统一返回 401）。
- 快照截图/缩略图以**相对路径字符串**落库并返回（`inspector/shots/…`、`inspector/thumbs/…`），前端经 `/media/` 拉取文件，**不是** JSON 内嵌 base64，也不是 FileResponse。
- 本模块**无 WS/SSE**；`snapshots/{id}/analyze` 为纯规则分区（`algorithms/layout.classify_structure`），基于已存快照即时计算，不落库、无设备交互、无 LLM。

---

## 3. 快照抓取接口：POST /api/inspector/capture

| 项 | 值 |
|---|---|
| 鉴权 | 需登录（Bearer Token） |
| Content-Type | application/json |

### 请求体

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| serial | string | 是 | 目标设备序列号；空串 → 409「未选择设备，请先连接设备」 |
| method | string | 否 | 抓取方式：`dump` / `ocr`，默认 `dump`；取值非法 → 400 |

> 抓取流程：先截图落盘 → 按 method 抓 dump（UI 层级+XPath+元素缩略图）/ OCR（截图识别+OCR 缩略图）→ 落库 `di_snapshots`；抓取失败不落库（500，清理本批文件）。

### 成功响应（200）

```json
{
  "status": true,                                # 请求是否成功，恒为 true
  "data": {
    "snapshot_id": 1,                            # 快照 ID
    "serial": "emulator-5554",                   # 设备序列号
    "method": "dump",                            # 抓取方式：dump / ocr
    "package": "com.example.app",                # 前台应用包名
    "activity": "com.example.app.MainActivity",  # 前台 Activity 名
    "screen_w": 1080,                            # 屏幕宽（px）
    "screen_h": 1920,                            # 屏幕高（px）
    "element_count": 42,                         # 元素总数（裁剪后）
    "actionable_count": 18,                      # 可交互元素数（clickable/text/resource_id/content_desc）
    "elements": [                                # 全量元素（裁剪后），结构见第 10 节元素对象
      {
        "depth": 1,                              # 层级深度
        "class_name": "android.widget.TextView", # 类全名
        "text": "登录",                           # 文本
        "content_desc": "",                       # 内容描述
        "resource_id": "com.example.app:id/login",# 资源 ID
        "package": "com.example.app",             # 所属包名
        "index": "0",                             # 同级下标（字符串）
        "bounds": "[0,100][1080,200]",            # bounds 字符串
        "x": 0,                                   # 左上角 x（px）
        "y": 100,                                 # 左上角 y（px）
        "width": 1080,                            # 宽（px）
        "height": 100,                            # 高（px）
        "clickable": false,                       # 是否可点击
        "enabled": true,                          # 是否可用
        "scrollable": false,                      # 是否可滚动
        "checkable": false,                       # 是否可勾选
        "checked": false,                         # 是否已勾选
        "focusable": false,                       # 是否可聚焦
        "long_clickable": false,                  # 是否可长按
        "xpaths": [                               # XPath 候选（按 count 升序）
          {"type": "resource-id", "xpath": "//android.widget.TextView[@resource-id='com.example.app:id/login']", "count": 1}
        ],
        "thumbnail_path": ""                      # 元素缩略图相对路径（不可交互元素为空串）
      }
    ],
    "actionable": [                               # 可交互元素子集（字段同 elements，另含 thumbnail_path）
      {
        "depth": 1,
        "class_name": "android.widget.Button",
        "text": "",
        "content_desc": "",
        "resource_id": "com.example.app:id/login_btn",
        "package": "com.example.app",
        "index": "1",
        "bounds": "[0,200][1080,300]",
        "x": 0,
        "y": 200,
        "width": 1080,
        "height": 100,
        "clickable": true,
        "enabled": true,
        "scrollable": false,
        "checkable": false,
        "checked": false,
        "focusable": true,
        "long_clickable": false,
        "xpaths": [],
        "thumbnail_path": "inspector/thumbs/20260101_120000_000001/el_0.png"  # 元素缩略图相对路径（media 目录内）
      }
    ],
    "ocr_count": 10,                              # OCR 识别文本条数
    "texts": [                                    # OCR 文本列表（ocr 方法时非空）
      {
        "text": "登录",                            # 识别文本
        "x": 0,                                   # 左上角 x（px）
        "y": 100,                                 # 左上角 y（px）
        "width": 1080,                            # 宽（px）
        "height": 100,                            # 高（px）
        "thumbnail_path": "inspector/thumbs/20260101_120000_000001/ocr_0.png"  # OCR 缩略图相对路径
      }
    ],
    "screenshot_path": "inspector/shots/capture_20260101_120000_000001.png",  # 页面截图相对路径（media 目录内）
    "created_at": "2026-01-01T12:00:00"           # 创建时间（ISO 8601，无时区）
  }
}
```

### 错误码与文案

| HTTP | message | 触发条件 |
|---|---|---|
| 400 | 无效的获取方法 | method 不在 dump/ocr 之内 |
| 409 | 未选择设备，请先连接设备 | serial 为空 |
| 409 | 设备未注册 | serial 不在设备池 |
| 409 | 设备正被执行引擎占用（{occupied_by}），请等待执行完毕 | 设备 BUSY 且被执行引擎（runner-/ai_agent/task-/run-）占用 |
| 500 | 获取失败 | dump 抓取失败（已清理本批文件） |
| 500 | OCR 识别失败，请稍后重试 | OCR 识别失败（已清理本批文件） |
| 500 | 获取失败 | 其他未捕获异常 |

---

## 4. 快照列表接口：GET /api/inspector/snapshots

| 项 | 值 |
|---|---|
| 鉴权 | 需登录（Bearer Token） |

### 请求（查询参数）

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| offset | int | 否 | 偏移量，默认 0 |
| limit | int | 否 | 每页条数，默认 100，上限 100（超出截断为 100） |

> 列表按 `created_by`（当前用户）过滤，`created_at` 倒序。

### 成功响应（200）

```json
{
  "status": true,                     # 请求是否成功，恒为 true
  "data": {
    "total": 2,                       # 符合条件的快照总数
    "items": [                        # 当前页快照行（元信息，不含全量元素）
      {
        "id": 2,                      # 快照 ID
        "serial": "emulator-5554",    # 设备序列号
        "method": "dump",             # 抓取方式：dump / ocr
        "package": "com.example.app", # 前台应用包名
        "element_count": 42,          # 元素总数
        "ocr_count": 0,               # OCR 文本条数
        "created_by": "1",            # 创建者 user_id
        "created_at": "2026-01-01T12:30:00"  # 创建时间
      }
    ]
  }
}
```

### 错误码与文案

| HTTP | message | 触发条件 |
|---|---|---|
| 400 | 无效的分页参数 | offset / limit 非整数（int() 转换失败） |

---

## 5. 快照详情接口：GET /api/inspector/snapshots/{id}

| 项 | 值 |
|---|---|
| 鉴权 | 需登录（Bearer Token） |

### 请求

无请求体；路径参数 `id` 为快照 ID。

### 成功响应（200）

```json
{
  "status": true,                   # 请求是否成功，恒为 true
  "data": {                         # 快照全量 JSON（字段与第 3 节 capture 成功响应一致）
    "snapshot_id": 1,
    "serial": "emulator-5554",
    "method": "dump",
    "package": "com.example.app",
    "activity": "com.example.app.MainActivity",
    "screen_w": 1080,
    "screen_h": 1920,
    "element_count": 42,
    "actionable_count": 18,
    "elements": [ "…" ],            # 元素数组（结构见第 10 节）
    "actionable": [ "…" ],          # 可交互元素数组
    "ocr_count": 10,
    "texts": [ "…" ],               # OCR 文本数组
    "screenshot_path": "inspector/shots/capture_20260101_120000_000001.png",
    "created_at": "2026-01-01T12:00:00"
  }
}
```

### 错误码与文案

| HTTP | message | 触发条件 |
|---|---|---|
| 404 | 快照不存在 | 快照 ID 不存在或非本人快照 |

---

## 6. 快照结构分析接口：GET /api/inspector/snapshots/{id}/analyze

| 项 | 值 |
|---|---|
| 鉴权 | 需登录（Bearer Token） |

> 纯规则结构分区（`algorithms/layout.classify_structure`）：依据「位置 / class / package / 交互标志」即时计算，**不落库、无设备交互、无 LLM**。

### 请求

无请求体；路径参数 `id` 为快照 ID。

### 成功响应（200）

```json
{
  "status": true,                    # 请求是否成功，恒为 true
  "data": {
    "package": "com.example.app",    # 前台应用包名
    "activity": "com.example.app.MainActivity",  # 前台 Activity 名
    "is_webview": false,             # 内容区是否含 WebView（命中即提示切 Web context）
    "sections": [                    # 分区（自上而下排序）
      {
        "name": "系统状态栏",         # 分区显示名（中文）
        "role": "status_bar",         # 分区角色：status_bar / system_nav / header / tab_bar / content / bottom_nav / other
        "bounds": "[0,0][1080,120]",  # 分区聚合 bounds
        "element_count": 2            # 分区内元素数
      }
    ],
    "elements": [                    # 元素数组 = 原始字段 + role + metrics
      {
        "depth": 1,                  # 以下为原始元素字段（见第 10 节）
        "class_name": "android.widget.TextView",
        "text": "登录",
        "content_desc": "",
        "resource_id": "com.example.app:id/login",
        "package": "com.example.app",
        "index": "0",
        "bounds": "[0,100][1080,200]",
        "x": 0,
        "y": 100,
        "width": 1080,
        "height": 100,
        "clickable": false,
        "enabled": true,
        "scrollable": false,
        "checkable": false,
        "checked": false,
        "focusable": false,
        "long_clickable": false,
        "xpaths": [],
        "thumbnail_path": "",
        "role": "header",            # 该元素归属分区角色
        "metrics": []                # 指标标签列表（可点击/可滚动/可勾选，命中其一）
      }
    ]
  }
}
```

### 错误码与文案

| HTTP | message | 触发条件 |
|---|---|---|
| 404 | 快照不存在 | 快照 ID 不存在或非本人快照 |

---

## 7. 快照删除接口：DELETE /api/inspector/snapshots/{id}/delete

| 项 | 值 |
|---|---|
| 鉴权 | 需登录（Bearer Token） |

### 请求

无请求体；路径参数 `id` 为快照 ID。

> 删除 `di_snapshots` 记录并尽力清理关联截图与缩略图文件（失败仅告警，不影响删除结果）。

### 成功响应（200）

```json
{
  "status": true,       # 请求是否成功，恒为 true
  "data": {
    "deleted": true     # 是否已删除，恒为 true
  }
}
```

### 错误码与文案

| HTTP | message | 触发条件 |
|---|---|---|
| 404 | 快照不存在 | 快照 ID 不存在或非本人快照 |

---

## 8. 元素保存接口：POST /api/inspector/snapshots/{id}/save-elements

| 项 | 值 |
|---|---|
| 鉴权 | 需登录（Bearer Token） |
| Content-Type | application/json |

> 筛减保存快照到元素定位（写元素资产经 `element_locator.api.import_snapshot_page`，禁止本模块直接 ORM 写 `el_` 表）。
> 两种模式：传 `page_id` = 保存到已有页面（元素 upsert 追加）；否则传 `page_label`（+ `folder_path`）= 新建页面。

### 请求体

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| page_label | string | 否 | 新建页面名称；与 page_id 二选一（无 page_id 时必填，空 → 400） |
| folder_path | string | 否 | 目录路径，按 `/` 逐级查找或创建（空 = 根目录） |
| page_id | int | 否 | 已有页面 ID（须为整数字符串）；与 page_label/folder_path 二选一 |
| element_ids | array[int] | 否 | 勾选元素下标列表（对应 dump_json.elements 的下标）；空 = 全部 |
| include_ocr | bool | 否 | 是否一并写入 OCR，默认 true |
| aliases | object | 否 | `{resource_id: 中文别名}` 映射，按 resource_id 回填到元素 alias |

### 成功响应（200）

```json
{
  "status": true,     # 请求是否成功，恒为 true
  "data": {
    "saved": 3,       # 新增元素数
    "updated": 1,     # 更新（upsert 命中已有）元素数
    "skipped": 0,     # 跳过元素数（当前实现恒为 0，预留字段）
    "page_id": 5      # 目标页面 ID（新建或已有页面）
  }
}
```

### 错误码与文案

| HTTP | message | 触发条件 |
|---|---|---|
| 400 | 快照不存在 | 快照 ID 不存在或非本人快照 |
| 400 | 页面名称不能为空 | 未传 page_id 且 page_label 为空 |
| 400 | 该快照无元素数据 | 快照 dump_json.elements 为空 |
| 400 | 元素数据不能为空 | 筛减后元素列表为空 |
| 400 | 目标页面不存在 | page_id 无效（不存在或为目录节点） |
| 409 | 目录最多嵌套 5 层 | folder_path 目录层级超 MAX_PAGE_TREE_DEPTH=5 |
| 409 | 同名节点「{segment}」不是目录 | 目录路径中同名节点是页面（非目录） |
| 409 | 同级页面「{page_label}」已存在 | 新建模式下同级已存在同名页面 |
| 500 | 保存失败 | 其他未捕获异常 |

---

## 9. 页面只读视图接口：GET /api/inspector/pages/{id}

| 项 | 值 |
|---|---|
| 鉴权 | 需登录（Bearer Token） |

### 请求

无请求体；路径参数 `id` 为元素定位页面 ID（`el_pages`，非快照 ID）。

### 成功响应（200）

```json
{
  "status": true,                    # 请求是否成功，恒为 true
  "data": {
    "page_id": 5,                    # 页面 ID
    "label": "登录页",                # 页面标签
    "package": "com.example.app",    # 包名
    "activity": "com.example.app.MainActivity",  # Activity 名
    "screenshot_path": "inspector/shots/capture_20260101_120000_000001.png",  # 截图相对路径
    "element_count": 4,              # 元素数
    "ocr_json": { "texts": [ "…" ], "ocr_count": 10 },  # OCR 数据（无则 null）
    "elements": [                    # 已保存元素（元素定位模型字段）
      {
        "id": 101,                   # 元素 ID
        "class_name": "android.widget.Button",  # 类全名
        "text_val": "",              # 文本（元素定位字段名 text_val，注意与快照 text 不同）
        "content_desc": "",          # 内容描述
        "resource_id": "com.example.app:id/login_btn",  # 资源 ID
        "bounds": "[0,200][1080,300]",  # bounds 字符串
        "xpaths": [                  # XPath 候选（存库为 JSON 字符串，返回时解析为 list）
          {"type": "resource-id", "xpath": "//*[@resource-id='com.example.app:id/login_btn']", "count": 1}
        ],
        "x": 0,                      # 左上角 x
        "y": 200,                    # 左上角 y
        "width": 1080,               # 宽
        "height": 100,               # 高
        "depth": 1,                  # 层级深度
        "index": "1",                # 同级下标（字符串）
        "clickable": true,           # 是否可点击
        "enabled": true,             # 是否可用
        "scrollable": false,         # 是否可滚动
        "checked": false,            # 是否已勾选
        "thumbnail_path": "inspector/thumbs/20260101_120000_000001/el_0.png",  # 缩略图相对路径
        "alias": "登录按钮",          # 别名（保存时 alias 或 text/resource_id 兜底）
        "is_test_point": false       # 是否测试点标记
      }
    ]
  }
}
```

### 错误码与文案

| HTTP | message | 触发条件 |
|---|---|---|
| 404 | 页面不存在 | 页面 ID 不存在（或为目录节点） |

---

## 10. 附：元素对象结构（dump_json.elements 通用）

> 快照 `elements` / `actionable` 中的元素来自 `models/ui_nodes.py` 的 `Node` 转 dict，并追加 `xpaths`（候选列表）与 `thumbnail_path`（仅可交互元素、截图裁剪落盘后回填）。

| 字段 | 类型 | 说明 |
|---|---|---|
| depth | int | 层级深度 |
| class_name | string | 类全名（如 `android.widget.Button`） |
| text | string | 文本 |
| content_desc | string | 内容描述 |
| resource_id | string | 资源 ID（真实 id 含 `:`） |
| package | string | 所属包名 |
| index | string | 同级下标（字符串） |
| bounds | string | bounds 字符串 `[l,t][r,b]` |
| x / y / width / height | int | 位置与尺寸（px） |
| clickable / enabled / scrollable / checkable / checked / focusable / long_clickable | bool | 交互/状态标志 |
| xpaths | array | XPath 候选 `{type, xpath, count, note?}`，按 count 升序（仅具可定位身份元素生成） |
| thumbnail_path | string | 元素缩略图相对路径（media 目录内）；不可交互或裁剪失败为空串 |

> 结构分析端点（第 6 节）在以上字段基础上为每个元素追加 `role`（分区角色）与 `metrics`（指标标签数组）。
