# API-设备检查器 — /api/inspector/*

> 设备检查器（device_inspector）快照化 REST 全集 6 个端点：抓取 / 列表 / 分层查询 / 删除 / 一键清空 / 保存到元素定位。
> 真相源：`apps/device_inspector/urls.py` + `views.py` + `api.py` + `service.py`；元素落盘契约跨 `apps/element_locator/api_snapshot.py`。

## 1. 总览

| 接口 | 方法 | 鉴权 | 说明 |
|---|---|---|---|
| 快照抓取接口 | POST /api/inspector/capture/ | 需登录(Bearer) | 一键抓取（dump/OCR）→ 快照落库 |
| 快照列表接口 | GET /api/inspector/snapshots/ | 需登录(Bearer) | 快照列表（倒序，最多返回保留上限 10 条） |
| 快照分层查询接口 | GET /api/inspector/snapshots/{id}/layers/ | 需登录(Bearer) | 两级分组 + 筛减分页；分层即时计算，含被展示裁剪丢弃的元素 |
| 快照删除接口 | DELETE /api/inspector/snapshots/{id}/delete | 需登录(Bearer) | 删除快照记录 + 截图/缩略图文件 |
| 一键清空接口 | DELETE /api/inspector/snapshots/clear/ | 需登录(Bearer) | 清空本人全部历史快照，返回删除条数 |
| 元素保存接口 | POST /api/inspector/snapshots/{id}/save-elements | 需登录(Bearer) | 筛减保存到元素定位（经 element_locator api） |

## 2. 通用约定

- 路径**必须带尾斜杠**，缺失即 404（`APPEND_SLASH=False`；容错中间件已删除，见 `openspec/specs/api-path-convention`）。
- 响应信封：成功 `{status: true, data}`，失败 `{status: false, message}`（`EnvelopeJSONRenderer` 统一包裹）。
- **全部 6 个端点均需登录**，携带 `Authorization: Bearer <access_token>`（DRF 默认 `IsAuthenticated`，无 AllowAny 覆盖；未登录统一返回 401）。
- 快照截图/缩略图以**相对路径字符串**落库并返回（`inspector/shots/…`、`inspector/thumbs/…`），前端经 `/media/` 拉取文件，**不是** JSON 内嵌 base64，也不是 FileResponse。
- 本模块**无 WS/SSE**；`snapshots/{id}/layers` 基于已存快照的全量节点索引即时计算，不落库、无设备交互、无 LLM。

---

## 3. 快照抓取接口：POST /api/inspector/capture/

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
    "elements": [                                # 全量元素（裁剪后），结构见第 9 节元素对象
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

## 4. 快照列表接口：GET /api/inspector/snapshots/

| 项 | 值 |
|---|---|
| 鉴权 | 需登录（Bearer Token） |

### 请求（查询参数）

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| offset | int | 否 | 偏移量，默认 0 |
| limit | int | 否 | 每页条数；实际最多返回 10 条（历史快照保留上限），超出按 10 截断 |

> 列表按 `created_by`（当前用户）过滤，`created_at` 倒序；时间相同再按 ID 倒序（与自动淘汰口径一致）。
> 每个用户最多保留 **10 条**历史快照：采集成功后会淘汰更早的记录，因此列表最多返回 10 条；`total` 恒为该用户的真实总数，不因封顶改写。

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

## 5. 快照分层查询接口：GET /api/inspector/snapshots/{id}/layers/

| 项 | 值 |
|---|---|
| 鉴权 | 需登录（Bearer Token） |
| 契约规格 | `openspec/specs/device-inspector-layers` |

按两级分组返回该快照的**全量**元素（含被展示裁剪丢弃的），支持筛减与分页。分层由快照的全量节点索引（`di_snapshots.nodes_json`）即时计算，**不落库、无设备交互**。

### 请求（查询参数）

| 参数 | 类型 | 说明 |
|---|---|---|
| group | string | 一级分组：`layout_container` / `scroll_collection` / `content_widget` / `unclassified`；非法 → 400 |
| sub | string | 二级分组：`text` / `icon` / `other`；**仅当 group=content_widget 时有效**，否则 400 |
| flag | string（可重复） | 交互标志，多个取**交集**：`clickable` / `long_clickable` / `scrollable` / `checkable` / `checked` / `enabled` / `focusable`；非法 → 400 |
| q | string | 关键词，对文本 / 资源标识 / 内容描述 / 类名做忽略大小写的子串匹配 |
| only_kept | `1` | 只要被展示裁剪保留的元素 |
| only_stable | `1` | 只要主定位唯一的元素 |
| offset / limit | int | 分页。**`limit` 缺省即不截断**（返回自 `offset` 起的全部命中）；显式给定时上限 500；非整数、offset<0、limit≤0 → 400 |

### 成功响应（200）

```json
{
  "status": true,
  "data": {
    "snapshot_id": 12,
    "source": "index",                 // index = 全量节点索引；legacy = 历史快照降级为保留集
    "package": "com.govee.home",
    "activity": ".main.MainTabActivity",
    "screen": { "w": 1080, "h": 2340 },
    "screenshot_path": "inspector/shots/capture_20260101_000000_000000.png",
    "summary": {
      "total": 140,
      "groups": [
        { "key": "layout_container", "name": "布局容器", "level": 1, "count": 74, "kept": 38,
          "stable_primary": 37, "clickable": 11, "scrollable": 0, "children": [] },
        { "key": "content_widget", "name": "内容控件", "level": 1, "count": 61, "kept": 55,
          "stable_primary": 44, "clickable": 17, "scrollable": 0,
          "children": [
            { "key": "text", "name": "文本", "level": 2, "count": 22, "kept": 22, "stable_primary": 15,
              "clickable": 1, "scrollable": 0 },
            { "key": "icon", "name": "图标", "level": 2, "count": 34, "kept": 29, "stable_primary": 21,
              "clickable": 18, "scrollable": 0 },
            { "key": "other", "name": "其它", "level": 2, "count": 5, "kept": 4, "stable_primary": 5,
              "clickable": 0, "scrollable": 0 } ] }
      ]
    },
    "total_matched": 140,
    "offset": 0,
    "limit": null,                     // 缺省不截断时为 null；显式分页时才是请求的条数
    "elements": [ /* 结构见第 9 节；每元素只带一条 primary，MUST NOT 含候选列表 */ ]
  }
}
```

> `summary.groups` 的计数**恒为该快照全量**（供分组选择器显示徽标，切分组时不变）；`total_matched` 才是本次筛减后的条数。**条数缺省即不截断**：此时返回的条目覆盖全量，故分组计数与条目数必然相等（同一响应内的两个口径不会分叉）；只有显式给 `limit` 时才按区间返回，此时区间外的元素由 `total_matched` 反映。元素按坐标顺序（顶边 y → 左边 x → 层级深度）排列；被展示裁剪丢弃的元素同样返回，以 `kept_in_snapshot` 区分（实线 / 虚线）。
> 响应**只给一条主定位**（`primary`：表达式 / 类型 / 匹配数 / 是否稳定），**不含候选全量**——候选是派生数据，且挑候选的规则必须唯一（算法层 `algorithms/element_layers.pick_primary`），不在调用方二次挑选。140 元素量级响应体约 93 KB（带候选全量为 134.6 KB 量级）。

### 错误码与文案

| 状态码 | 文案 | 触发 |
|---|---|---|
| 400 | 未知的一级分组 / 未知的二级分组 / 二级分组只在一级分组为内容控件时有效 / 未知的交互标志：X | 分组或标志取值非法 |
| 400 | 无效的分页参数 | offset/limit 非整数、offset<0 或 limit≤0 |
| 404 | 快照不存在 | id 不存在或不属于当前调用者 |
| 401 | — | 未登录 |

---

## 6. 快照删除接口：DELETE /api/inspector/snapshots/{id}/delete

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

## 7. 元素保存接口：POST /api/inspector/snapshots/{id}/save-elements

| 项 | 值 |
|---|---|
| 鉴权 | 需登录（Bearer Token） |
| Content-Type | application/json |

> 筛减保存快照到元素定位（写元素资产经 `element_locator.api.import_snapshot_page`，禁止本模块直接 ORM 写 `el_` 表）。
> 两种模式：传 `page_id` = 保存到已有页面（元素 upsert 追加）；否则传 `page_label`（+ `folder_path`）= 新建页面。
> **只保存六项**（变更 `rework-save-to-elements`）：缩略图、元素名称、序号、文本、主定位、交互标注；
> 类名 / 内容描述 / 坐标分量 / 层级 / 父内序号 / 候选 XPath 不再写入（`resource_id` 与 `bounds` 仍写入，作为去重键）。
> **缩略图**在保存时按元素 bounds 从该快照已存的整屏截图裁剪（检查器侧），再复制到元素定位自有目录；
> 截图缺失或裁剪失败时该元素缩略图留空 + 告警，保存不失败。
> **不保存也不关联整屏截图**：页面 `screenshot_path` 恒为空。
> 页面级 OCR 不随保存写入（变更 `rework-inspector-view`）：快照自身 OCR 仍存于 `di_snapshots.ocr_json`，
> 元素定位页面 `ocr_json` 恒为空。

### 请求体

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| page_label | string | 否 | 新建页面名称；与 page_id 二选一（无 page_id 时必填，空 → 400） |
| folder_path | string | 否 | 目录路径，按 `/` 逐级查找或创建（空 = 根目录） |
| page_id | int | 否 | 已有页面 ID（须为整数字符串）；与 page_label/folder_path 二选一 |
| element_ids | array[int] | 否 | 勾选元素的**坐标顺序序号**（1 基，与分层端点 `seq` / 元素表「序号」列同源）；空 = 全部 |
| aliases | object | 否 | `{resource_id: 中文别名}` 映射，按 resource_id 回填到元素 alias |
| element_aliases | array | 否 | `[{index, name}]`，index 为坐标顺序序号；优先于 aliases，同一 resource_id 的多个元素互不覆盖 |

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
| 400 | 该快照无全量元素索引，无法保存 | 快照没有 nodes_json（历史快照） |
| 400 | 元素序号不存在：{值} | `element_ids` 含不在该快照全量元素序号内的值 |
| 400 | 目标页面不存在 | page_id 无效（不存在或为目录节点） |
| 409 | 目录最多嵌套 5 层 | folder_path 目录层级超 MAX_PAGE_TREE_DEPTH=5 |

## 8. 一键清空接口：DELETE /api/inspector/snapshots/clear/

| 项 | 值 |
|---|---|
| 鉴权 | 需登录（Bearer Token） |

无请求体。删除**当前调用者自己**的全部历史快照记录，返回本次删除的条数。

> 与单条删除同口径：先判定截图 / 缩略图是否仍被元素定位的页面或元素引用，**被引用的文件保留**，其余照旧清理。只影响调用者自己的记录；没有任何快照时成功返回 0（幂等）。

### 成功响应（200）

```json
{
  "status": true,     # 请求是否成功，恒为 true
  "data": {
    "deleted": 12     # 本次删除的快照条数（没有快照时为 0）
  }
}
```

### 错误码与文案

| HTTP | message | 触发条件 |
|---|---|---|
| 401 | — | 未携带有效 Bearer Token |

---

## 9. 附：元素对象结构（dump_json.elements 通用）

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

### nodes_json（全量节点索引，分层查询的数据源）

`di_snapshots.nodes_json` 存**未裁剪**的全量节点（含被展示裁剪丢弃的），供分层查询显示「拿得到但没保留」的元素。每个节点字段：

`depth` / `class_name` / `text` / `content_desc` / `resource_id` / `index` / `bounds` / `x` / `y` / `width` / `height` /
`clickable` / `enabled` / `scrollable` / `checkable` / `checked` / `focusable` / `long_clickable` / `kept_in_snapshot`。

**不含 XPath 候选**（候选由查询时即时生成）；**不在 `dump_json` 里重复**（`dump_json.elements` 仍是展示裁剪后的集合）。
引入本字段之前的历史快照该列为空列表 → 分层端点降级为保留集并在 `source` 标注 `legacy`。