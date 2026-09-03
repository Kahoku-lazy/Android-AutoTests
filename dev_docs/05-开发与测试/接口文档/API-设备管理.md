# API-设备管理 — /api/devices/*

> 设备管理模块（`apps/device_pool`）10 个端点：设备生命周期（扫描 / 连接 / 断开 / 激活 / 心跳）+ 占用 / 释放锁。
> 真相源：`apps/device_pool/urls.py` + `views.py` + `manager.py` + `models.py` + `shared/renderers.py`。
> 本模块**无 DRF Serializer / ViewSet**（无 `serializers.py` / `views_drf.py` / `views_api.py`），视图为函数式视图（`@api_view`），序列化统一走 `manager.DeviceSerializer.device_to_dict`。

## 1. 总览

| 接口 | 方法 | 鉴权 | 说明 |
|---|---|---|---|
| 设备列表接口 | GET /api/devices/ | 需登录(Bearer) | 设备列表 + 内嵌 `current` 字段（含状态同步 + 可见性过滤） |
| 设备扫描接口 | POST /api/devices/scan | 需登录(Bearer) | ADB 扫描注册（全量 / USB / WiFi） |
| 当前设备接口 | GET /api/devices/current | 需登录(Bearer) | 当前活动设备信息（预留，前端暂未消费） |
| 设备心跳接口 | GET /api/devices/heartbeat | 需登录(Bearer) | 心跳同步 + 各状态计数（前端 30s 轮询） |
| 设备连接接口 | POST /api/devices/{serial} | 需登录(Bearer) | 连接 + 采集信息 + 自动激活（observe 模式置使用中） |
| 设备断开接口 | POST /api/devices/{serial}/disconnect | 需登录(Bearer) | 删除无线设备记录（USB 无删除键） |
| 观察断开接口 | POST /api/devices/{serial}/disconnect-observe | 需登录(Bearer) | 轻量断开（不删记录，释放观察占用为 ONLINE） |
| 设备激活接口 | POST /api/devices/{serial}/activate | 需登录(Bearer) | 切换当前活动设备 |
| 设备锁定接口 | POST /api/devices/{serial}/lock | 需登录(Bearer) | 锁定 / 公开切换（WIFI 可见性） |
| 设备释放接口 | POST /api/devices/{serial}/release | 需登录(Bearer) | 释放设备检查器占用 |

## 2. 通用约定

- 路径**无尾斜杠**，唯一例外：列表接口 `GET /api/devices/`（尾斜杠）。其余 9 个端点均无尾斜杠。
- 响应信封：成功 `{status: true, data}`，失败 `{status: false, message}`（`EnvelopeJSONRenderer` 统一包裹；`retry` 字段仅在业务返回该键时透出，本模块不涉及）。
- 鉴权：**全部端点需登录**，携带 `Authorization: Bearer <access_token>`；`request.user_id` 由 `JWTAuthenticationMiddleware` 注入（数字用户 ID 字符串，用于可见性过滤 / 锁定归属 / 占用归属）。
- 状态机：`ONLINE` ⇄ `BUSY` → `OFFLINE`；设备离线（非 BUSY）时直接删除记录、不保留墓碑，故列表 `status` 仅出现 `ONLINE` / `BUSY`。
- 本模块无 WS，心跳为 HTTP 轮询端点；设备交互（ADB/u2）由 `manager.DeviceDetector` 编排。
- 写操作下沉 `manager.py`（四职责类）/ `api.py`，视图不直接 ORM 写；`DeviceError`（`APIException` 子类）由 DRF 异常处理器转为 `{status: false, message}`，`message` 即代码中抛出的文案。

**鉴权失败（对所有端点统一，由中间件直接返回）**：

| HTTP | message | 触发条件 |
|---|---|---|
| 401 | 请先登录 | 无 `Authorization: Bearer` 头 |
| 401 | 登录已过期或令牌无效 | 令牌无效 / 过期 / 已黑名单 / 非 access 类型 |

---

## 3. 设备列表接口：GET /api/devices/

| 项 | 值 |
|---|---|
| 鉴权 | 需登录（Bearer Token） |
| Content-Type | —（无请求体） |

### 请求

无请求体；`user_id` 取自 JWT，用于可见性过滤（管理员全局可见 / USB 恒公开 / WIFI 公开或仅锁定者与配置者可见）。

### 成功响应（200）

```json
{
  "status": true,                       # 请求是否成功，恒为 true
  "data": {
    "devices": [                        # 可见设备列表（ONLINE 在前，BUSY 在后）
      {
        "id": 1,                        # 设备记录主键
        "serial": "abc123",             # 设备序列号（唯一）
        "name": "",                     # 设备名
        "model": "Pixel 5",             # 型号
        "brand": "Google",              # 品牌
        "screen": "1080x2340",          # 分辨率（宽x高，缺失为空串）
        "status": "ONLINE",             # 状态：ONLINE | BUSY
        "connection_type": "USB",       # 连接类型：USB | WIFI
        "connection_addr": "",          # 无线设备连接地址（IP:port / mDNS），USB 为空
        "locked": false,                # 是否被锁定（仅 WIFI 可为 true）
        "locked_by": "",                # 锁定者用户名（仅 WIFI 有值，否则空）
        "locked_at": null,              # 锁定时间（ISO 格式，未锁定为 null）
        "occupied_by": "",              # 占用者用户名（空 = 未占用）
        "occupied_at": null,            # 占用时间（ISO 格式，未占用为 null）
        "connected_at": "2026-08-21T10:00:00",  # 首次连接时间（ISO 格式）
        "added_by": "admin",            # 配置者用户名（无线主动连接时补记）
        "last_seen": "2026-08-21T10:05:00",     # 最后在线时间（ISO 格式）
        "is_current": true,             # 是否当前活动设备
        "remaining": 0                  # BUSY 且被占用时为活跃锁剩余秒数，否则 0
      }
    ],
    "current": "abc123"                 # 当前活动设备序列号（指向不可见设备时为 null）
  }
}
```

> 列表已内嵌 `current` 字段，device-inspector「设备列表」直接经本接口读取，无需再调独立 `/current` 端点。

### 错误码与文案

| HTTP | message | 触发条件 |
|---|---|---|
| 500 | 设备列表加载失败 | 状态同步 / 序列化抛出未捕获异常 |

---

## 4. 设备扫描接口：POST /api/devices/scan

| 项 | 值 |
|---|---|
| 鉴权 | 需登录（Bearer Token） |
| Content-Type | application/json |

### 请求体

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| target | string | 否 | 扫描目标；空 = 全量扫描 ADB 可见设备；含 `:` 按 WIFI（IP:port）连接；否则按 USB 序列号查找 |

### 成功响应（200）

```json
{
  "status": true,                       # 请求是否成功，恒为 true
  "data": {
    "count": 1,                         # 本轮返回的设备数量
    "newly_added": 1,                   # 本轮新注册设备数（已存在则为 0）
    "devices": [                        # 设备列表（字段同 §3 devices 元素）
      { "serial": "192.168.1.10:5555", "status": "ONLINE" }
    ]
  }
}
```

### 错误码与文案

| HTTP | message | 触发条件 |
|---|---|---|
| 400 | 无效的 IP 或端口 | WIFI target 的 IP 不合法或端口不在 1024~65535 |
| 400 | device {target} not found | USB target 不在 `adb devices` 可见列表 |
| 502 | 无法解析设备 {addr} 的序列号，请确认设备在线后重试 | 无线设备连上后仍取不到 ro.serialno |
| 502 | 设备 ATX Agent 未运行，请在设备端启动 uiautomator2 服务 | u2 探测报错含 atx-agent / offline |
| 504 | 连接超时，请检查设备 USB/WiFi 连接 | adb connect 失败/超时 / u2 探测其他连接错误 |
| 500 | 扫描失败 | 其他未捕获异常 |

---

## 5. 当前设备接口：GET /api/devices/current

| 项 | 值 |
|---|---|
| 鉴权 | 需登录（Bearer Token） |
| Content-Type | —（无请求体） |

### 请求

无请求体。返回当前活动设备（`device_pool.current_serial`）信息。

> **预留端点**：前端暂未消费（2026-08-21 校验确认），保留路由。

### 成功响应（200）

```json
{
  "status": true,                       # 请求是否成功，恒为 true
  "data": {
    "serial": "abc123",                 # 当前设备序列号（无当前设备时为空串）
    "screen_w": 1080,                   # 屏幕宽（记录缺失时回退引擎 displayWidth）
    "screen_h": 2340,                   # 屏幕高（记录缺失时回退引擎 displayHeight）
    "package": "com.android.settings",  # 当前前台应用包名
    "model": "Pixel 5",                 # 型号（仅设备记录存在时返回）
    "brand": "Google",                  # 品牌（仅设备记录存在时返回）
    "connection_type": "USB"            # 连接类型（仅设备记录存在时返回）
  }
}
```

> 当 `current_serial` 对应的设备记录不存在（如未连接）时，仅返回 `serial` / `screen_w` / `screen_h` / `package` 四个字段。

### 错误码与文案

无业务错误码（读前台应用失败时降级为 `package: ""`，不抛错）。

---

## 6. 设备心跳接口：GET /api/devices/heartbeat

| 项 | 值 |
|---|---|
| 鉴权 | 需登录（Bearer Token） |
| Content-Type | —（无请求体） |

### 请求

无请求体。触发状态同步 + 刷新活跃锁心跳 + 回收过期 observe 锁。

### 成功响应（200）

```json
{
  "status": true,                       # 请求是否成功，恒为 true
  "data": {
    "updated": 2,                       # 本轮状态更新（如过期锁释放）数量
    "offline": 1,                       # 本轮离线删除（非 BUSY 设备）数量
    "online": 3,                        # 当前 ONLINE 设备数
    "busy": 1,                          # 当前 BUSY 设备数
    "offline_count": 0,                 # 固定 0（保留字段，兼容前端）
    "disconnected": 0,                  # 固定 0（保留字段，兼容前端）
    "total": 4                          # 设备总数（online + busy）
  }
}
```

### 错误码与文案

无业务错误码。

---

## 7. 设备连接接口：POST /api/devices/{serial}

| 项 | 值 |
|---|---|
| 鉴权 | 需登录（Bearer Token） |
| Content-Type | application/json |

### 路径参数

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| serial | string | 是 | 目标设备序列号（需已注册，否则 404） |

### 请求体

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| activate | boolean | 否 | 是否连接后自动切换为当前设备；缺省 true |
| mode | string | 否 | 为 `observe` 时连接后进入观察占用（置 BUSY） |

### 成功响应（200）

```json
{
  "status": true,                       # 请求是否成功，恒为 true
  "data": {
    "serial": "abc123",                 # 设备序列号
    "model": "Pixel 5",                 # 型号（采集所得）
    "screen_w": 1080,                   # 屏幕宽
    "screen_h": 2340,                   # 屏幕高
    "android_version": "30"             # Android SDK 版本（字符串，采集失败为空）
  }
}
```

### 错误码与文案

| HTTP | message | 触发条件 |
|---|---|---|
| 404 | 设备 {serial} 未注册 | 记录不存在 |
| 409 | 设备正在使用中，无法连接 | 设备 status 为 BUSY |
| 502 | 设备 ATX Agent 未运行，请在设备端启动 uiautomator2 服务 | u2 探测报错含 atx-agent / offline |
| 504 | 连接超时，请检查设备 USB/WiFi 连接 | adb connect 超时 / u2 探测其他连接错误 |

---

## 8. 设备断开接口：POST /api/devices/{serial}/disconnect

| 项 | 值 |
|---|---|
| 鉴权 | 需登录（Bearer Token） |
| Content-Type | —（无请求体） |

### 路径参数

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| serial | string | 是 | 目标设备序列号 |

### 请求

无请求体。删除无线设备记录（清理连接缓存 + 活跃锁标记 released）。

### 成功响应（200）

```json
{
  "status": true,                       # 请求是否成功，恒为 true
  "data": {
    "serial": "abc123",                 # 被删除的设备序列号
    "deleted": true                     # 是否已删除，恒为 true
  }
}
```

### 错误码与文案

| HTTP | message | 触发条件 |
|---|---|---|
| 404 | 设备 {serial} 未注册 | 记录不存在 |
| 400 | USB 设备无删除键 | 设备连接类型非 WIFI |
| 409 | 设备使用中，无法删除 | 设备 status 为 BUSY |

---

## 9. 观察断开接口：POST /api/devices/{serial}/disconnect-observe

| 项 | 值 |
|---|---|
| 鉴权 | 需登录（Bearer Token） |
| Content-Type | —（无请求体） |

### 路径参数

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| serial | string | 是 | 目标设备序列号 |

### 请求

无请求体。轻量断开：不删除记录，释放观察占用（仅当占用者为观察连接、非执行引擎时恢复 ONLINE）。

### 成功响应（200）

```json
{
  "status": true,                       # 请求是否成功，恒为 true
  "data": {
    "serial": "abc123",                 # 设备序列号
    "message": "设备观察连接已断开"       # 固定提示文案
  }
}
```

### 错误码与文案

无业务错误码（记录不存在或占用者为执行引擎时同样返回成功响应，仅不产生释放动作）。

---

## 10. 设备激活接口：POST /api/devices/{serial}/activate

| 项 | 值 |
|---|---|
| 鉴权 | 需登录（Bearer Token） |
| Content-Type | —（无请求体） |

### 路径参数

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| serial | string | 是 | 目标设备序列号（不存在时自动注册后激活） |

### 请求

无请求体。切换 `device_pool` 当前设备到该序列号（记录不存在时先 `register_device` 注册）。

### 成功响应（200）

```json
{
  "status": true,                       # 请求是否成功，恒为 true
  "data": {
    "current": "abc123"                 # 新激活（当前）设备序列号
  }
}
```

### 错误码与文案

| HTTP | message | 触发条件 |
|---|---|---|
| 400 | 设备正在使用中，无法激活 | 设备 status 为 BUSY |

---

## 11. 设备锁定接口：POST /api/devices/{serial}/lock

| 项 | 值 |
|---|---|
| 鉴权 | 需登录（Bearer Token） |
| Content-Type | application/json |

### 路径参数

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| serial | string | 是 | 目标设备序列号 |

### 请求体

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| locked | boolean | 否 | true = 锁定（可见性私有化），false = 公开；缺省 true |

> 归属人 `user_id` 优先取 JWT（`request.user_id`），为空时回退请求体 `user_id`。

### 成功响应（200）

```json
{
  "status": true,                       # 请求是否成功，恒为 true
  "data": {
    "serial": "abc123",                 # 设备序列号
    "locked": true                      # 锁定结果状态
  }
}
```

### 错误码与文案

| HTTP | message | 触发条件 |
|---|---|---|
| 404 | 设备 {serial} 未注册 | 记录不存在 |
| 400 | USB 设备不支持锁定 | 设备连接类型非 WIFI |
| 409 | 设备已被 {locked_by} 锁定 | 已被其他用户锁定（占位为 locked_by 原始值，即锁定者 user_id 字符串） |

---

## 12. 设备释放接口：POST /api/devices/{serial}/release

| 项 | 值 |
|---|---|
| 鉴权 | 需登录（Bearer Token） |
| Content-Type | —（无请求体） |

### 路径参数

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| serial | string | 是 | 目标设备序列号 |

### 请求

无请求体。释放设备检查器占用（恢复 ONLINE + 活跃锁标记 released）。

### 成功响应（200）

```json
{
  "status": true,                       # 请求是否成功，恒为 true
  "data": {
    "serial": "abc123",                 # 设备序列号
    "released": true                    # 是否已释放，恒为 true
  }
}
```

### 错误码与文案

| HTTP | message | 触发条件 |
|---|---|---|
| 404 | 设备 {serial} 未注册 | 记录不存在 |
| 409 | 设备正在执行用例，无法解除占用 | 占用者为执行引擎（ai_agent / runner- / task- / run- 前缀） |
| 400 | 设备未被占用，无需操作 | 设备当前无占用 |
