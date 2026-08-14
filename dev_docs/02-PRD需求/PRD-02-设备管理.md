# PRD-02 — 设备管理 (Device Pool)

> 关联模块：`apps/device_pool/` · 前端：`frontend/src/modules/device-pool/`
> 关联全局：[`需求大纲.md`](./需求大纲.md) §5.2
> 版本：v6.0 · 状态：评审中 · 日期：2026-08-14

**修订记录**

| 版本 | 日期 | 变更摘要 |
|------|------|----------|
| v6.0 | 2026-08-14 | 按仪表盘 PRD 格式重构：移除实现细节（文件行数/实施状态/已知问题），补齐功能详细规格（F-XX-XX 逐项 + 边界状态 + 验收标准）、布局与视觉设计、后端功能逻辑、API 字段级契约（13 端点）、数据来源表、非功能/非目标/关键约束/文件索引；同步代码真相（Pinia→composable、.js→.ts、views.py→views/ 包、动森→Doodle Craft） |
| v5.0 | 2026-07-25 | 拍立得 KPI 卡片、Dual 视图（表格/卡片）、FilterTabs 迁入 shared、模块背景点阵纸纹、全宽布局 |

---

## 1. 功能定位

设备管理是平台的**设备基础设施层**，是唯一直接与 Android 设备通信的模块。用户在此扫描、连接、锁定、释放 Android 设备，并管理设备使用队列。页面由两个区块自上而下排列：统计概览 → 设备列表。

**核心职责**：

- **扫描** ADB 设备（USB / WiFi 局域网），注册到设备池
- **连接** 设备（uiautomator2 + Airtest 双连接），采集设备元信息
- **锁定 / 释放** 设备（用户绑定 + 进程占用两种语义）
- **排队** 管理忙碌设备的使用队列（FIFO 自动分配）
- **断开** 设备（普通 / 强制断开，保留锁审计）
- **统计** 设备状态分布（在线 / 使用中 / 离线 / 总计）

设备管理是**管理模块（有写操作）**：区别于仪表盘的只读聚合，所有写操作走 `api.ts` → djangoClient，组件不直连 HTTP。

---

## 2. 功能详细规格

### 2.1 ADB 扫描（F-01-01）

扫描当前 ADB 可见设备并注册到设备池。支持全量扫描（`adb devices`）与指定目标扫描（USB 串号 或 WiFi `IP:port`）。

| 输入 | 行为 |
|------|------|
| 无 target（全量） | `adb devices` 列出全部在线设备，逐台 `update_or_create` 注册，新设备采集元信息，OFILINE 恢复为 ONLINE |
| target = USB 串号 | 校验目标在 adb 列表中，注册并采集信息 |
| target = `IP:port` | 纵深防御校验 IPv4/端口格式，`adb connect` 后注册（见 F-01-02） |

**组件**：`index.vue` 刷新按钮（`handleRefresh` → `loadDevices`）、`NetworkConnectDialog.vue`（局域网表单）。

**边界状态**：

| 场景 | 行为 |
|------|------|
| adb 无设备 | 返回空列表，前端显示空态「暂无设备」 |
| 目标非法 IP/端口 | 返回 400「无效的 IP 或端口」 |
| `adb connect` 超时 | 返回 504「连接超时」 |

**验收标准**：

- 全量扫描返回 `count` 与 `newly_added` 与列表一致
- 新设备首次扫描后元信息（model/brand/screen）已采集
- 非法 IP（如 `999.1.1.1`）与非法端口（如 `0`）被 400 拦截，不透传给 adb

### 2.2 WiFi 局域网连接（F-01-02）

通过 IP:端口连接无线调试设备。前端 `NetworkConnectDialog` 弹窗收集 IP + 端口，前端校验通过后 POST 到后端，后端再校验并 `adb connect`。

| 字段 | 校验 | 说明 |
|------|------|------|
| IP | IPv4 点分十进制，每段 0–255 | 前端 `IPV4_RE` + 后端正则双重校验 |
| 端口 | 1–65535 整数（默认 5555） | 前端 1–65535，后端 1024–65535 |

**组件**：`NetworkConnectDialog.vue`（el-dialog + el-form，聚焦第一个非法字段）。

**边界状态**：

| 场景 | 行为 |
|------|------|
| IP 格式非法 | 前端 inline 错误提示「请输入合法的 IPv4 地址」，不发送请求 |
| `adb connect` 返回非 connected | 返回 400「无法连接到 target」 |
| 连接超时 | 返回 504 |

**验收标准**：

- IP/端口前端校验 + 后端纵深防御双层拦截
- 连接成功后设备出现在列表，`connection_type = WIFI`
- 提交中 `loading` 态防重复提交

### 2.3 统计概览（F-02-01）

页面顶部 4 张拍立得 KPI 卡片，展示设备状态分布。每张卡片：彩色几何图形 → 标签 → 数字，微旋转排列，hover 归正放大。

| 卡片 | 颜色 | 图形 | 口径 |
|------|:--:|:--:|------|
| 在线 | 薄荷绿 `#6BCB77` | ◆ 菱形 | `status === 'ONLINE'` 的设备数 |
| 使用中 | 桃粉 `#FFB5A7` | ▲ 三角 | `status === 'BUSY'` 的设备数 |
| 离线 | 浅灰 `#d4d8dc` | ■ 方块 | `status === 'OFFLINE' \|\| 'DISCONNECTED'` 的设备数 |
| 总计 | 墨黑 `var(--ink)` | ● 圆 | 全部设备总数 |

**组件**：`shared/components/KpiCard.vue`，props: value / label / color / shape。

**边界状态**：

| 场景 | 行为 |
|------|------|
| 无设备 | 四卡均显示 0 |
| 数据加载中 | 列表 loading 态，KPI 由已加载数据派生 |

**验收标准**：

- 四卡数值与设备列表查询结果一致（在线+使用中+离线 = 总计）
- 卡片几何图形（菱形/三角/方块/圆）与颜色映射正确

### 2.4 设备列表（F-02-02）

设备筛选 + 操作工具栏 + 表格/卡片双视图。

**工具栏**：

| 元素 | 位置 | 功能 |
|------|------|------|
| FilterTabs（全部/在线/使用中/离线） | 左 | 按状态筛选 |
| 视图切换（📋表格 / 📷卡片） | 右 | 双视图切换 |
| 设备计数「N 台」 | 右 | 实时数量 |
| 局域网连接 | 右 | 弹 WiFi 连接窗 |
| 刷新设备 | 右 | 重新扫描，loading 旋转 |

**表格视图**（8 列，`AppTable` 渲染）：

| 列 | 渲染 | 说明 |
|------|------|------|
| 序列号 | 等宽字体 + 当前设备 ● | `record.serial` |
| 型号 | `displayModel(record)` | brand + model |
| 分辨率 | `record.screen` | 空显示灰「—」 |
| 状态 | `DeviceStatusCell` | 4 状态 el-tag |
| 连接 | `connectionLabel(connection_type)` | USB 有线 / 无线 ADB |
| 锁定 | 锁定者 / 「共用」 | 紫底 / 绿底标签 |
| 最后在线 | `formatRelativeTime(last_seen)` | 相对时间 |
| 操作 | `DeviceActionsCell` | 锁定/排队/解除占用/断开，条件禁用 |

**卡片视图**：按状态分 3 组（🟢在线 / 🔴使用中 / ⚫离线），`DeviceCard` 渲染，空组自动隐藏。

**组件**：`AppTable.vue`、`DeviceCard.vue`、`DeviceStatusCell.vue`、`DeviceActionsCell.vue`、`FilterTabs.vue`、`EmptyState.vue`。

**边界状态**：

| 场景 | 行为 |
|------|------|
| 列表为空 | 空态「暂无设备，点击刷新扫描」/「没有匹配的设备」 |
| 离线设备 | 行半透明 `opacity: 0.5` |
| 分页 | `usePagination`，选项 [5, 10, 20] |

**验收标准**：

- 表格/卡片双视图切换后筛选、分页状态一致
- 设备按 ONLINE > BUSY > OFFLINE > DISCONNECTED 排序
- 卡片可键盘操作（role=button + tabindex + Enter/Space）

### 2.5 设备锁定（F-02-03）

锁定设备支持两种语义：**用户绑定**（`type=user`，设置 `locked_by`，不改状态）与**进程占用**（`type=occupy`，设置 `occupied_by`，改 `status=BUSY`）。

| 语义 | 字段 | 状态变化 |
|------|------|---------|
| 用户绑定（user） | `locked_by` / `locked_at` | status 不变 |
| 进程占用（occupy） | `occupied_by` / `occupied_at` | status → BUSY |

**组件**：`DeviceActionsCell.vue`（锁定按钮，`handleLockClick`）。

**边界状态**：

| 场景 | 行为 |
|------|------|
| 设备 OFFLINE/DISCONNECTED | 400「设备已离线，无法操作」 |
| 已被他人绑定 | 409「设备已被 X 绑定」 |
| 已被他人占用 | 409「设备已被 X 占用」 |
| user_id 为空 | 400 |

**验收标准**：

- 用户绑定不改 status，进程占用改 BUSY
- 每次锁定写一条 DeviceLock 审计记录（status=active）
- 同一设备同时最多 1 个活跃锁（数据库 UNIQUE 约束）

### 2.6 设备释放（F-02-04）

释放设备锁/占用，保留审计记录（标记 released，不删除）。

| 参数 | 行为 |
|------|------|
| `unlock=true` 且无占用 | 仅解用户绑定，清 `locked_by` |
| 有占用 | 清 `occupied_by` + 恢复 ONLINE + 队列自动分配 |
| `force=true` | 强制释放执行引擎占用（`runner-`/`ai_agent`/`task-`/`run-` 前缀） |

**边界状态**：

| 场景 | 行为 |
|------|------|
| 执行引擎占用且未 force | 409「设备正在执行用例，无法解除占用」 |
| 无占用却请求释放 | 400「设备未被占用」 |
| 无绑定却请求解绑 | 400「设备未被绑定」 |

**验收标准**：

- 释放后锁记录 status=released，不删除
- 释放触发队列自动分配（`_auto_assign_from_queue`）

### 2.7 强制断开（F-02-05）

断开设备连接，强制断开他人设备需填写原因（管理员操作）。

| 参数 | 说明 |
|------|------|
| `force` | 强制断开标记 |
| `reason` | 强制断开他人时必填 |

**边界状态**：

| 场景 | 行为 |
|------|------|
| 他人使用中且非锁定者 | 403「只有锁定者可以断开」 |
| 强制断开他人且无 reason | 400「必须填写原因」 |
| 断开成功 | 释放锁 + 删除设备记录（无 DISCONNECTED 历史） |

**组件**：`DisconnectDialog.vue`（el-dialog，`isBusyOthers` 时必填原因）。

**验收标准**：

- 断开后设备记录删除、缓存清理、锁审计保留
- 强制断开他人必须填原因才放行

### 2.8 加入排队（F-03-01）

忙碌设备（BUSY）被他人锁定时，可加入等待队列。

| 规则 | 说明 |
|------|------|
| 防重复 | 同一用户对同一设备只能排队一次 |
| FIFO | 释放时队首自动分配 |

**边界状态**：

| 场景 | 行为 |
|------|------|
| 已在排队 | 返回 `已在排队中` + 当前位置 + 等待时长 |
| user_id 为空 | 400 |

**验收标准**：

- 重复排队不产生重复记录，返回当前位置
- 排队记录 status=waiting

### 2.9 取消排队（F-03-02）

离开设备等待队列。

**组件**：`QueuePanel.vue`（排队 Popover 面板，列出用户/设备/等待时长，操作列「取消」）。

**验收标准**：

- 取消后排队记录 status=cancelled
- 传 user_id 只取消本人排队

---

## 3. 布局与视觉设计

> 全部颜色/字号引用 Doodle Craft 主题令牌（[`frontend/DESIGN_SYSTEM.md`](../frontend/DESIGN_SYSTEM.md)）。KPI 卡片颜色为 hex 字面量（见约束 C-03）。

### 3.1 页面布局

```
┌─────────────────────────────────────────────┐
│ WorkbenchHeader（标题 + 排队面板）            │
├─────────────────────────────────────────────┤
│ ① 统计概览   4 张拍立得 KPI 卡片              │
│ ② 设备列表   工具栏 + 表格/卡片双视图          │
└─────────────────────────────────────────────┘
```

- 页面底色：米白纸纹（`--doodle-bg`）叠加点阵底纹
- 章节标题：展示字体 `--app-size-lg`、字重 700，下方手绘波浪下划线
- 设备列表区块：模块色（薄荷绿 4%）底 + 2.5px 20% 边圆角容器

### 3.2 卡片设计（拍立得风格）

| 属性 | 规格 |
|------|------|
| 形状 | 圆角 `6px 10px`；墨色描边 3px（状态色）；投影扁平 |
| 图钉 | 卡片顶部居中 9px 圆形图钉（`--app-pushpin-*` 径向渐变） |
| 姿态 | `nth-child(3n)` 交替微旋转 -0.8°/+0.5°/-0.4°；hover 归正放大 1.03 |
| 照片区 | 44px 高状态色区块，圆角 `3px 5px`，2px 同色边；序列号等宽 12px |
| 状态边 | 在线绿 / 使用中粉 / 离线灰（`--app-status-success` / `--app-status-danger` / `--app-offline`） |

### 3.3 状态与组件规格

| 元素 | 规格 |
|------|------|
| 状态 el-tag | 不对称圆角 `4px 8px` + 1.5px 状态色边 + 状态色底 |
| 状态 Badge | 执行中粉 / 占用中黄 / 已绑定紫，圆角 `3px 6px` |
| 视图切换 | 2px 模块色边圆角容器，active 填模块色白字 |
| 排队 badge | 粉底 `--app-status-danger` + 2px ink 边 + 扁平投影 |
| 操作按钮 | 圆角 `4px 8px` + 2px 边 + 状态色（锁定紫 / 断开红 / 排队黄） |

### 3.4 KPI 配色（模块状态色）

| 卡片 | 色值 |
|------|------|
| 在线 | `#6BCB77`（薄荷绿） |
| 使用中 | `#FFB5A7`（桃粉） |
| 离线 | `#d4d8dc`（浅灰） |
| 总计 | `var(--ink)`（墨黑） |

---

## 4. 后端功能逻辑

### 4.1 设备状态机

```
(new) → ONLINE ──锁定/占用──→ BUSY ──释放/超时──→ ONLINE
                     │
   adb 不可见        │
   ONLINE ─────────→ OFFLINE ──adb 恢复──→ ONLINE
```

| 状态 | 含义 | 进入条件 |
|------|------|---------|
| `ONLINE` | 在线可用 | adb 可见且未锁定 |
| `BUSY` | 使用中 | 进程占用（occupy）或自动锁定 |
| `OFFLINE` | 离线 | adb 列表不可见 |
| `DISCONNECTED` | 瞬态 | 历史遗留标记，`_purge_disconnected_devices` 同步时删除 |

> ⚠️ 断开操作 `_delete_device_record` **删除记录**（无 DISCONNECTED 墓碑）；DISCONNECTED 仅作为同步时的瞬态标记被清理，不作为持久状态。

### 4.2 锁口径

| 项 | 说明 |
|------|------|
| 锁类型 | `user`（用户绑定，不改 status）/ `process`（进程占用，改 BUSY） |
| 审计 | DeviceLock 永不删除，通过 `status`（active/released/expired）追踪生命周期 |
| 并发 | 数据库 UNIQUE 约束保证同一设备同时最多 1 个活跃锁 |
| 超时 | 默认 300s；`remaining_seconds` 计算剩余时长 |
| 释放原因 | manual / timeout / disconnect / force |

### 4.3 排队调度

```
设备 BUSY → 他人加入队列（waiting，防重复）
释放时 _auto_assign_from_queue → 队首 assigned → 自动绑定 + 建锁
排队超时 30 分钟 → timeout
```

### 4.4 心跳与状态同步

- 前端每 30s 轮询 `heartbeat`（`HEARTBEAT_INTERVAL`）
- `_update_device_status`：同步 adb 真实状态 → DB；BUSY 且锁超时 → 自动释放
- `_check_timeout_queue`：清理超时排队记录

### 4.5 降级规则

| 场景 | 行为 |
|------|------|
| adb 不可用 | `_adb_device_serials` 返回空集，全部设备标记 OFFLINE |
| 设备信息采集失败 | 记录 warning，不影响注册 |
| 心跳失败 | 前端 debug 日志，不打断 UI |

---

## 5. API 接口功能

鉴权：全部端点需要 JWT Bearer 鉴权（公开路径除外）。响应统一 `{status, data}` / `{status, message}`，JSON 字段 snake_case。

### 5.1 端点总览

| # | 方法 | 端点 | 功能 | 前端消费 |
|---|------|------|------|:--:|
| 1 | GET | `/api/devices/` | 设备列表 + 当前设备 + 排队长度 | ✅ |
| 2 | POST | `/api/devices/scan` | ADB 扫描注册（F-01-01） | ✅ |
| 3 | GET | `/api/devices/current` | 当前活动设备信息 | ❌ |
| 4 | GET | `/api/devices/heartbeat` | 心跳检测 + 状态同步 | ✅ |
| 5 | GET | `/api/devices/queue` | 排队状态列表 | ✅ |
| 6 | POST | `/api/devices/{serial}` | 连接设备（F-01-02） | ✅ |
| 7 | POST | `/api/devices/{serial}/disconnect` | 断开设备（F-02-05） | ✅ |
| 8 | POST | `/api/devices/{serial}/disconnect-observe` | 轻量断开（observe 模式） | ❌ |
| 9 | POST | `/api/devices/{serial}/activate` | 激活设备 | ✅ |
| 10 | POST | `/api/devices/{serial}/lock` | 锁定设备（F-02-03） | ✅ |
| 11 | POST | `/api/devices/{serial}/release` | 释放设备（F-02-04） | ✅ |
| 12 | POST | `/api/devices/{serial}/queue` | 加入排队（F-03-01） | ✅ |
| 13 | POST | `/api/devices/{serial}/queue/leave` | 取消排队（F-03-02） | ✅ |

> 端点 3（`/current`）、8（`/disconnect-observe`）前端未消费，供 element-locator / case-manager observe 模式使用。

### 5.2 端点 1 — 设备列表

**接口地址**：`GET /api/devices/`

**请求**：无参数。

**响应 data 字段**：

| 字段 | 类型 | 必填 | 约束 | 说明 |
|------|------|:--:|------|------|
| `devices[]` | array | 是 | 按 ONLINE > BUSY > OFFLINE > DISCONNECTED 排序 | 设备列表 |
| `current` | string \| null | 是 | 当前激活设备 serial，无则 null | 当前设备 |
| `queue_length` | number | 是 | 整数 ≥0 | 等待中排队数 |

**devices 元素字段**：

| 字段 | 类型 | 必填 | 约束 | 说明 |
|------|------|:--:|------|------|
| `id` | number | 是 | 整数 | 设备记录 ID |
| `serial` | string | 是 | 非空，≤100 字符，唯一 | 序列号 |
| `name` | string | 是 | 可空 | 设备名 |
| `model` | string | 是 | 可空 | 型号 |
| `brand` | string | 是 | 可空 | 品牌 |
| `screen` | string | 是 | 可空，格式 `WxH` | 分辨率 |
| `status` | string | 是 | 枚举 `ONLINE`/`BUSY`/`OFFLINE`/`DISCONNECTED` | 状态 |
| `connection_type` | string | 是 | 枚举 `USB`/`WIFI` | 连接类型 |
| `locked_by` | string | 是 | 可空 | 锁定者用户 |
| `locked_at` | string \| null | 是 | ISO 时间或 null | 锁定时间 |
| `occupied_by` | string | 是 | 可空 | 占用进程 |
| `occupied_at` | string \| null | 是 | ISO 时间或 null | 占用时间 |
| `last_seen` | string \| null | 是 | ISO 时间或 null | 最后在线 |
| `is_current` | boolean | 是 | — | 是否当前激活 |
| `remaining` | number | 是 | 整数 ≥0；BUSY 时剩余秒 | 锁剩余时长 |

**响应示例**：

```json
{
  "status": true,
  "devices": [
    {
      "id": 1,
      "serial": "emulator-5554",
      "name": "",
      "model": "Pixel 8",
      "brand": "Google",
      "screen": "1080x2400",
      "status": "ONLINE",
      "connection_type": "USB",
      "locked_by": "",
      "locked_at": null,
      "occupied_by": "",
      "occupied_at": null,
      "last_seen": "2026-08-14T10:00:00",
      "is_current": true,
      "remaining": 0
    }
  ],
  "current": "emulator-5554",
  "queue_length": 0
}
```

### 5.3 端点 2 — ADB 扫描

**接口地址**：`POST /api/devices/scan`

**请求字段**：

| 字段 | 类型 | 必填 | 约束 | 说明 |
|------|------|:--:|------|------|
| `target` | string | 否 | USB 串号 或 `IP:port`；空 = 全量扫描 | 扫描目标 |

**响应 data 字段**：

| 字段 | 类型 | 必填 | 说明 |
|------|------|:--:|------|
| `count` | number | 是 | 扫描到的设备数 |
| `newly_added` | number | 是 | 新注册设备数 |
| `devices[]` | array | 是 | 同端点 1 devices 元素 |

**错误**：非法 IP/端口 400；`adb connect` 失败 400；超时 504。

**响应示例**：

```json
{ "status": true, "count": 1, "newly_added": 0, "devices": [ { "serial": "emulator-5554", "status": "ONLINE" } ] }
```

### 5.4 端点 3 — 当前设备

**接口地址**：`GET /api/devices/current`

**响应 data 字段**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `serial` | string | 当前激活设备 serial |
| `screen_w` / `screen_h` | number | 屏幕宽高 |
| `package` | string | 当前前台包名 |
| `model` / `brand` | string | 型号 / 品牌 |
| `connection_type` | string | USB / WIFI |

### 5.5 端点 4 — 心跳检测

**接口地址**：`GET /api/devices/heartbeat`

**响应 data 字段**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `updated` | number | 本次同步更新的设备数 |
| `offline` / `online` / `busy` / `offline_count` / `disconnected` | number | 各状态计数 |
| `total` | number | 状态计数总和 |

### 5.6 端点 5 — 排队状态

**接口地址**：`GET /api/devices/queue`

**响应 data 字段**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `queue[]` | array | 等待中的排队记录（FIFO） |
| `count` | number | 排队条数 |

**queue 元素字段**：`position`（位置）、`serial`、`user_id`、`requested_at`、`waited_seconds`（等待秒数）。

**响应示例**：

```json
{
  "status": true,
  "queue": [
    { "position": 1, "serial": "emulator-5554", "user_id": "alice", "requested_at": "2026-08-14T09:00:00", "waited_seconds": 120 }
  ],
  "count": 1
}
```

### 5.7 端点 6 — 连接设备

**接口地址**：`POST /api/devices/{serial}`

**请求字段**：

| 字段 | 类型 | 必填 | 约束 | 说明 |
|------|------|:--:|------|------|
| `activate` | boolean | 否 | 默认 true | 是否自动激活 |
| `mode` | string | 否 | `observe` 轻量连接（不锁定） | 连接模式 |
| `user_id` | string | 否 | 提供则自动锁定 | 操作用户 |
| `timeout` | number | 否 | 默认 300 | 锁超时秒 |

**响应 data 字段**：`serial` / `model` / `screen_w` / `screen_h` / `android_version`。

**错误**：设备未注册 404；离线 400；他人锁定 409；ATX Agent 未运行 502；连接超时 504。

### 5.8 端点 7 — 断开设备

**接口地址**：`POST /api/devices/{serial}/disconnect`

**请求字段**：

| 字段 | 类型 | 必填 | 约束 | 说明 |
|------|------|:--:|------|------|
| `force` | boolean | 否 | 默认 false | 强制断开 |
| `reason` | string | 否 | 强制断开他人必填 | 原因 |
| `user_id` | string | 否 | — | 操作用户 |

**响应 data 字段**：`serial` / `disconnected`（bool）/ `locks_released`（number）。

**错误**：未注册 404；他人使用中 403；强制断开无原因 400。

### 5.9 端点 8 — 轻量断开（observe）

**接口地址**：`POST /api/devices/{serial}/disconnect-observe`

仅清理 uiautomator2 连接缓存，不删 DB 记录、不释放锁。供 element-locator / case-manager observe 模式使用。

**响应 data 字段**：`serial` / `message`。

### 5.10 端点 9 — 激活设备

**接口地址**：`POST /api/devices/{serial}/activate`

切换 DevicePool 当前设备指针。响应 `{status, current}`。设备 OFFLINE/DISCONNECTED 返回 400。

### 5.11 端点 10 — 锁定设备

**接口地址**：`POST /api/devices/{serial}/lock`

**请求字段**：

| 字段 | 类型 | 必填 | 约束 | 说明 |
|------|------|:--:|------|------|
| `type` | string | 否 | `user`（默认）/ `occupy` | 锁定类型 |
| `user_id` | string | 是 | 非空 | 操作用户 |
| `timeout` | number | 否 | 默认 300 | 锁超时秒 |

**响应 data 字段**（type=user）：`serial` / `user_id` / `locked_at` / `timeout` / `is_occupied`。
**响应 data 字段**（type=occupy）：`serial` / `occupied_by` / `occupied_at` / `timeout`。

**错误**：user_id 空 400；未注册 404；离线 400；他人绑定/占用 409。

### 5.12 端点 11 — 释放设备

**接口地址**：`POST /api/devices/{serial}/release`

**请求字段**：

| 字段 | 类型 | 必填 | 说明 |
|------|------|:--:|------|
| `reason` | string | 否 | manual / force |
| `user_id` | string | 否 | 操作用户 |
| `force` | boolean | 否 | 强制释放执行引擎占用 |
| `unlock` | boolean | 否 | 同时解用户绑定 |

**响应 data 字段**：`serial` / `released` / `force_released` / `unlocked`（解绑单独返回 `unlocked: true`）。

**错误**：未注册 404；执行引擎占用未 force 409；无占用 400；无绑定 400。

### 5.13 端点 12 — 加入排队

**接口地址**：`POST /api/devices/{serial}/queue`

**请求字段**：`user_id`（必填，非空）。

**响应 data 字段**：`message` / `position`（位置）/ `waited_seconds`（等待秒）。已在排队返回「已在排队中」+ 当前位置。

**错误**：user_id 空 400；未注册 404。

### 5.14 端点 13 — 取消排队

**接口地址**：`POST /api/devices/{serial}/queue/leave`

**请求字段**：`user_id`（可选，提供则只取消本人）。

**响应 data 字段**：`cancelled`（取消条数）。

### 5.15 契约变更

| 版本 | 变更 |
|------|------|
| v5.0 | 锁定语义拆分 user / occupy（`lock_type`）；释放增加 `unlock`/`force` 参数 |
| v6.0 | 端点清单校正：13 端点（前端消费 11，`/current`、`/disconnect-observe` 为 observe 后端接口） |

---

## 6. 数据来源表

| 表 | 表前缀 | 说明 |
|------|:--:|------|
| `dp_devices` | dp_ | 设备注册表（serial 唯一 + 元信息 + 状态 + 绑定/占用） |
| `dp_device_locks` | dp_ | 锁审计表（永不删除，status 追踪生命周期） |
| `dp_device_queue` | dp_ | FIFO 等待队列 |

---

## 7. 非功能需求

| 类别 | 指标 | 目标值 |
|------|------|:--:|
| 性能 | 列表接口响应 | ≤500ms（不逐设备 u2.connect，用 DB 缓存字段） |
| 并发 | 锁并发安全 | `select_for_update` + UNIQUE 约束 |
| 可靠性 | 断连恢复 | 心跳 30s 轮询 + 锁超时 300s 自动释放 |
| 兼容性 | 窄屏适配 | ≤900px KPI 2 列、卡片组 2 列 |
| 无障碍 | 减少动态效果 | 卡片可键盘操作（role/tabindex/Enter/Space） |

---

## 8. 非目标（Non-goals）

| 不做的功能 | 原因 |
|------|------|
| 设备分组 / 标签管理 | 待产品评估（原附录 B 未实施项） |
| 设备远程控制（实时屏幕操作） | 设备操作由 element-locator / test-runner 承担 |
| 设备批量操作（多选锁定/断开） | 当前逐台操作，保持简单 |
| DISCONNECTED 持久化历史 | 断开即删记录，无墓碑（前后端契约见 ARCH §1.5） |

---

## 9. 关键约束速查

| 编号 | 约束 | 实施位置 |
|------|------|------|
| C-01 | serial 唯一，同设备不可重复注册 | `models.py` UNIQUE |
| C-02 | 同时仅 1 个活跃锁（数据库级并发） | `dp_device_locks` UNIQUE(device, active) |
| C-03 | 颜色/字号引用 Doodle Craft 令牌；KPI 卡片 hex 为字面量例外（改色同步 §3.4） | `DevicePoolView.style.css`、`index.vue` |
| C-04 | 写操作收敛：View/Tool → api.py → ORM，禁止跨模块直接 ORM 写 | `api.py` |
| C-05 | 锁审计永不删除，仅标记 status | `models.py` + `_release_internal` |
| C-06 | 响应统一 `{status, data}` / `{status, message}`，snake_case | 全部端点 |
| C-07 | 设备操作走 DevicePool 单例，禁止直接 u2/Airtest | `pool.py` |
| C-08 | 心跳超时 300s 自动释放；排队 30 分钟超时 | `helpers.py` |

---

## 10. 相关文件索引

| 层 | 文件 | 说明 |
|------|------|------|
| 前端 | `frontend/src/modules/device-pool/index.vue` | 页面编排（241 行） |
| 前端 | `frontend/src/modules/device-pool/DevicePoolView.logic.ts` | 编排器 useDevicePoolView |
| 前端 | `frontend/src/modules/device-pool/DevicePoolView.style.css` | 页面样式（Doodle Craft） |
| 前端 | `frontend/src/modules/device-pool/api.ts` | 数据层（11 端点） |
| 前端 | `frontend/src/modules/device-pool/constants.ts` | 状态映射/列/分组配置 |
| 前端 | `frontend/src/modules/device-pool/helpers.ts` | 纯函数 |
| 前端 | `frontend/src/modules/device-pool/composables/` | useDevicePoolState / useDeviceActions / useHeartbeat |
| 前端 | `frontend/src/modules/device-pool/components/` | DeviceCard / DeviceStatusCell / DeviceActionsCell / QueuePanel / DisconnectDialog / NetworkConnectDialog |
| 后端 | `apps/device_pool/models.py` | 3 表定义 |
| 后端 | `apps/device_pool/urls.py` | 13 端点路由 |
| 后端 | `apps/device_pool/views/` | device_views / lock_views / connect_views / helpers |
| 后端 | `apps/device_pool/api.py` | 跨模块写操作白名单 |
| 后端 | `apps/device_pool/pool.py` | DevicePool 单例（Airtest + u2） |

---

## 附录A：功能边界规则

| 边界 | 规则 |
|------|------|
| 我能做什么 | 扫描/连接/锁定/释放/断开设备、查看状态分布、排队管理 |
| 我不能做什么 | 在设备上执行用例（执行引擎）、定位元素（元素定位）、AI 操控（AI 助手） |
| 如需越界 | 由 element-locator / test-runner / AI 助手通过 api.py / DevicePool 调用本模块能力 |
| 数据可见性 | 设备列表按当前 ADB 可见性 + DB 状态展示 |
