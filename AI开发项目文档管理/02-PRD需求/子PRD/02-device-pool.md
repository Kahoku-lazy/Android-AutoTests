# 子PRD — 设备管理 (Device Pool)

> 关联模块：`apps/device_pool/` · 前端：`frontend/src/modules/device-pool/`
> 关联全局：`../全局PRD.md` · 关联架构：`../../01-技术架构/技术代码结构.md` §2.2
> 版本：v2.0 · 状态：⏳ v2 计划 · 日期：2026-06-30

---

## 1. 模块概述

### 1.1 要解决的问题

在 Android 自动化测试平台中，设备是核心资产。当前痛点：

| 痛点 | 现状 | 影响 |
|------|------|------|
| **设备不可见** | 工程师不知道哪台设备空闲、哪台被占用 | 频繁碰壁，反复尝试连接 |
| **抢占冲突** | 多人同时操作同一台设备，互相覆盖测试结果 | 测试结果不可信，排查困难 |
| **断连无感知** | 设备掉线后平台无提示，任务静默失败 | 浪费执行时间，报告缺失 |
| **连接门槛高** | 需手动记 IP/串号，无线连接步骤繁琐 | 非技术人员完全无法自助 |

### 1.2 解决方案

**设备管理模块**作为平台的设备资产管理中枢，提供设备的全生命周期管理：

```
[ADB 扫描] → [注册入库] → [状态监控] → [锁定/释放] → [排队调度] → [连接/断开]
```

### 1.3 业务目标

| 目标 | 衡量方式 | 目标值 |
|------|----------|:--:|
| 设备利用率提升 | BUSY 时间 / 总 ONLINE 时间 | ≥60% |
| 冲突归零 | 多人同时操作同设备事件数 | 0 |
| 断连感知延迟 | 断连 → 平台标记 OFFLINE | ≤30s |
| 连接成功率达 | 连接成功 / 连接尝试 | ≥98% |

### 1.4 与其他模块的关系

```
                   ┌──────────────┐
                   │  device-pool │ ← 本模块
                   └──┬───┬───┬──┘
          ┌──────────┘   │   └──────────┐
          ▼              ▼              ▼
  ┌──────────────┐ ┌──────────┐ ┌──────────────┐
  │element-locator│ │test-runner│ │report-generator│
  │ 实时截图+元素  │ │ 并行执行  │ │ 设备维度报告  │
  └──────────────┘ └──────────┘ └──────────────┘
```

- **element-locator**：通过 DevicePool 获取设备截屏和 UI 层级
- **test-runner**：执行前获取设备锁，执行后释放
- **report-generator**：按设备维度统计执行结果

---

## 2. 用户画像与用户故事

### 2.1 核心用户

| 角色 | 使用频率 | 核心场景 |
|------|:--:|------|
| **测试工程师** | 每天 | 连接设备 → 锁定 → 定位元素 → 运行用例 → 释放 |
| **QA 负责人** | 每天 | 查看设备池状态 → 分配设备 → 监控并行任务 |
| **产品经理** | 每周 | 连接设备 → 快速查看应用页面 → 验证需求 |

### 2.2 用户故事

| 编号 | As a... | I want to... | So that... | 验收标准 | P |
|------|---------|-------------|-----------|----------|:--:|
| US-DP-01 | 测试工程师 | 在页面中看到所有已连接设备的状态一览 | 清楚知道哪些设备可用，无需挨个试 | ①表格列：序列号/型号/分辨率/状态/锁定用户/最后在线时间 ②状态实时刷新(≤30s) ③离线设备用置灰+角标标注 | P0 |
| US-DP-02 | 测试工程师 | 一键扫描并展示所有 ADB 已连接设备 | 新设备连上 USB 后即可被平台发现 | ①点击「扫描」按钮触发 adb devices ②新设备自动注册入库 ③已离线设备恢复时自动标记 ONLINE | P0 |
| US-DP-03 | 测试工程师 | 勾选一台设备后点击「连接」，看到该设备的实时手机画面 | 快速进入元素定位流程，无需额外跳转 | ①列表支持单选/勾选 ②连接成功后自动跳转到 element-locator 页面 ③实时截图延迟≤500ms ④失败时提示具体原因（设备离线/已被锁定/ADB 权限不足） | P0 |
| US-DP-04 | 测试工程师 | 锁定一台设备，确保测试过程中不会被他人抢占 | 测试结果不被他人行为污染 | ①锁定后状态变为 BUSY ②其他用户看到「已被 XXX 锁定，剩余 XX 分钟」 ③锁定超时自动释放（默认 5 分钟可配） ④锁定冲突时提示"该设备已被锁定" | P0 |
| US-DP-05 | 测试工程师 | 测试完成后手动释放设备，或系统自动释放 | 设备回到 ONLINE 状态，其他人可以使用 | ①手动释放立即生效 ②系统按锁定超时自动释放 ③释放后解除设备锁记录 | P0 |
| US-DP-06 | QA 负责人 | 强行断开一台离线或异常的设备连接 | 清理不可用设备，释放被僵尸占用的设备 | ①点击「断开」→ ADB disconnect ②强制清空该设备所有锁记录 ③设备从列表中移除（或标记为 DISCONNECTED 直到下次扫描恢复） ④断开操作需二次确认弹窗 | P1 |
| US-DP-07 | QA 负责人 | 查看当前排队等待设备的队列 | 了解设备资源竞争情况，合理调度 | ①页面顶部显示排队人数徽标 ②点击可展开详细队列：用户/设备/等待时间/预计剩余 ③队列按 FIFO 排序 | P1 |
| US-DP-08 | 测试工程师 | 在设备离线时收到提示，上线时收到通知 | 及时了解设备状态变化，不浪费时间等离线设备 | ①离线设备在表格中用 Offline 标签 + 置灰行 ②设备恢复上线时自动刷新状态 | P2 |
| US-DP-09 | 测试工程师 | 支持无线 ADB 连接（IP:Port） | 不依赖 USB 线，远程操作设备 | ①输入 IP:Port → 执行 adb connect ②连接成功后自动注册设备 ③列表中标注连接方式（USB/无线） | P1 |

---

## 3. 功能需求详细说明

### 3.1 F-01：设备发现与注册

**触发条件**：
- 用户点击「扫描设备」按钮
- 页面首次加载时自动触发
- 前端 30 秒轮询心跳检测时

**业务规则**：

```
1. 执行 adb devices -l 获取已连接设备列表
2. 对每个设备：
   a. 已在 dp_devices 中 → 更新状态为 ONLINE，更新 last_seen
   b. 不在 dp_devices 中 → 创建记录（serial/name/model/resolution）
3. 对 dp_devices 中不在 adb 列表的设备：
   a. 状态为 BUSY → 保持 BUSY（保护进行中的任务）
   b. 状态为 ONLINE → 标记为 OFFLINE
4. 扫描完成后返回设备列表 + 当前活动设备
```

**设备信息采集**：连接成功后通过 uiautomator2 获取以下信息入库：
- `model`：设备型号（如 SM-G9980）
- `brand`：品牌（如 Samsung）
- `screen_w` / `screen_h`：屏幕分辨率
- `android_version`：系统版本
- `connection_type`：USB / WIFI

**前端展示**：

| 列 | 数据来源 | 格式 |
|----|---------|------|
| ☐ 勾选框 | — | 单选（radio）/ 多选（checkbox），无设备时隐藏 |
| 序列号 | Device.serial | 等宽字体，可复制，截断时 hover 显示全文 |
| 型号 | Device.model | 如为空显示「—」 |
| 分辨率 | Device.screen_w × screen_h | 如「1080×2400」 |
| 状态 | Device.status | ONLINE=绿色「在线」· BUSY=橙色「使用中」· OFFLINE=灰色「离线」 |
| 连接方式 | Device.connection_type | USB=数据线图标 · WIFI=无线图标 |
| 锁定用户 | Device.locked_by | BUSY 态显示「用户名（剩余 X 分钟）」，非 BUSY 显示「—」 |
| 最后在线 | Device.last_seen | 相对时间（如「3 分钟前」），离线超过 1 小时显示绝对时间 |
| 操作 | — | 见下表 |

**操作按钮矩阵**：

| 设备状态 | 切换 | 锁定 | 释放 | 断开 | 连接 |
|----------|:--:|:--:|:--:|:--:|:--:|
| ONLINE (非当前) | ✅ 切换 | ✅ 锁定 | — | ✅ 断开 | ✅ 连接 |
| ONLINE (当前) | ✅ 当前（已激活） | ✅ 锁定 | — | ✅ 断开 | ✅ 连接 |
| BUSY (我的锁) | ✅ 切换 | — | ✅ 释放 | ✅ 断开 | ✅ 连接 |
| BUSY (他人锁) | ❌ 禁用 | ❌ 禁用 | ❌ 禁用 | 🔴 强制断开(管理员) | ❌ 禁用 |
| OFFLINE | ❌ 禁用 | ❌ 禁用 | — | ✅ 断开 | ❌ 禁用 |

---

### 3.2 F-02：设备连接与实时画面

**触发条件**：用户勾选一台 ONLINE 设备，点击「连接设备」按钮。

**业务流程**：

```
用户勾选设备 → 点击「连接设备」
    ├─ 设备 OFFLINE → ❌ 提示「设备已离线，请重新扫描」
    ├─ 设备被他人锁定 → ❌ 提示「设备已被 XXX 锁定，剩余 X 分钟」
    └─ 设备可用 → 
        1. POST /api/devices/{serial} 建立 uiautomator2 连接
        2. 自动激活为当前设备 (activate)
        3. 自动锁定设备（如用户已登录，user_id=当前用户名，timeout=300s）
        4. 连接成功 → 前端跳转到 element-locator 页面
                     → 显示「已连接 {设备型号}」Toast
        5. 连接失败 →
            ├─ ADB 连接超时 → 提示「连接超时，请检查设备 USB/WiFi 连接」
            ├─ uiautomator2 服务未启动 → 提示「设备 ATX Agent 未运行，请在设备端启动 uiautomator2 服务」
            └─ 其他错误 → 提示具体错误信息
```

**前端跳转逻辑**：

```javascript
// 连接成功后，router push 到元素定位页，携带设备信息
router.push({
  path: '/elements',
  query: { serial: device.serial, autoStart: '1' }
})
```

**持续心跳**：连接成功后，前端维持 30s 间隔的心跳轮询：
- 每次轮询时后端检查设备是否仍在线
- 设备断连 → 前端弹出通知「设备 {serial} 已断开连接」

---

### 3.3 F-03：设备锁定机制

**业务场景**：测试工程师需要独占一台设备执行测试，防止他人同时操作。

**锁定流程**：

```
用户点击「锁定」→ 输入/确认用户标识
    ├─ 设备状态 = BUSY（有活跃锁）→ ❌ 返回冲突
    │   └─ 前端提示「设备已被 {locked_by} 锁定，剩余 {remaining} 秒」
    ├─ 设备状态 = OFFLINE → ❌ 提示「设备已离线」
    └─ 设备状态 = ONLINE → ✅
        1. INSERT INTO dp_device_locks (device_id, user_id, timeout_seconds)
        2. UPDATE dp_devices SET status='BUSY', locked_by=user_id, locked_at=NOW()
        3. 返回锁信息：{user_id, locked_at, timeout, remaining}
```

**超时自动释放**：

```
定时任务（每次 list_devices 或 heartbeat 时触发）：
  FOR EACH device WHERE status = 'BUSY':
      elapsed = NOW() - locked_at
      timeout = 取该设备最新 DeviceLock.timeout_seconds
      IF elapsed > timeout:
          执行释放逻辑（见 F-04）
          记录日志 [INFO] 设备 {serial} 锁已超时自动释放 (locked_by={user_id})
```

**业务规则**：
- 同一设备同一时间最多 **1 个有效锁**
- 同一用户可以同时持有 **多台设备** 的锁
- 默认超时时间 **300 秒（5 分钟）**，锁定时可自定义
- 超时释放后，锁记录**不删除**（保留审计），仅标记为 expired
- 管理员可以**强制释放**他人持有的锁（权限控制：仅 ADMIN 角色）

---

### 3.4 F-04：设备释放机制

**触发条件**：
- 用户手动点击「释放」
- 系统检测到锁超时自动释放
- 设备断开时强制释放
- 管理员强制释放他人锁

**释放流程**：

```
触发释放
    1. UPDATE dp_devices SET status='ONLINE', locked_by='', locked_at=NULL
       WHERE serial={serial} AND status='BUSY'
    2. UPDATE dp_device_locks SET status='released', released_at=NOW()
       WHERE device_id={device_id} AND status='active'
    3. 日志：[INFO] 设备 {serial} 已释放 (user={user_id}, reason=manual|timeout|disconnect|force)
    4. 返回释放结果
```

---

### 3.5 F-05：强制断开设备

**触发条件**：用户（通常是 QA 负责人或管理员）需要强制断开一台异常设备。

**断开流程**：

```
用户点击「断开」→ 二次确认弹窗「确定要断开 {serial} ({model}) 吗？」
    ├─ 取消 → 无操作
    └─ 确认 →
        1. 检查设备状态：
           ├─ BUSY（他人锁）→ 需管理员权限，否则拒绝
           └─ 其他状态 → 继续
        2. 执行 adb disconnect {serial}（无线）或忽略（USB）
        3. 清理 DevicePool 缓存：
           - 从 _instances 中移除该设备
           - 如为当前设备，清空 current_serial
        4. 强制释放该设备所有活跃锁（调用 F-04 逻辑）
        5. 标记设备为 DISCONNECTED（不删除记录）
        6. 日志：[WARNING] 设备 {serial} 已被 {user} 强制断开
        7. 前端刷新设备列表
```

**权限规则**：

| 操作 | 匿名用户 | 普通用户 | 管理员 |
|------|:--:|:--:|:--:|
| 断开自己的设备 | ✅ | ✅ | ✅ |
| 断开他人 ONLINE 设备 | ❌ | ❌ | ✅ |
| 断开他人 BUSY 设备 | ❌ | ❌ | ✅（需二次确认 + 填写原因） |

---

### 3.6 F-06：排队机制（v2）

**触发条件**：当用户试图锁定一台已被他人占用的设备时。

**业务规则**：

```
1. 锁请求被拒绝后，提供「加入排队」选项
2. 排队记录：(device_id, user_id, requested_at)
3. 设备释放时：
   a. 从队列中取出第一个等待用户
   b. 自动为该用户锁定设备（默认超时 300s）
   c. WebSocket 推送通知：「设备 {serial} 已可用，已为你自动锁定，剩余 300 秒」
4. 用户可随时取消排队
5. 排队超时：排队超过 600 秒（10 分钟）用户无响应 → 自动取消，顺延下一人
```

**前端展示**：页面顶部排队徽标 `排队 3`，点击展开排队详情面板。

---

## 4. 业务逻辑与状态机

### 4.1 设备状态定义

| 状态 | 常量 | 含义 | 用户可见标签 |
|------|------|------|-------------|
| ONLINE | `ONLINE` | 设备在线，无人使用，可连接 | 🟢 在线 |
| BUSY | `BUSY` | 设备在线，已被锁定，不可抢占 | 🟠 使用中 |
| OFFLINE | `OFFLINE` | 设备离线（USB 断开 / 网络断开 / 关机） | ⚫ 离线 |
| DISCONNECTED | `DISCONNECTED` | 被用户主动断开（v2） | 🔴 已断开 |

### 4.2 状态转换图

```
                         ┌──────────────────────────────────────┐
                         │                                      │
    ┌─── adb scan ──►  ONLINE  ◄──── release ────┐             │
    │                    │  ▲                     │             │
    │                    │  │                     │             │
    │              lock  │  │ timeout             │             │
    │                    │  │                     │             │
    │                    ▼  │                     │             │
    │    ┌────────────► BUSY ├────────────────────┘             │
    │    │              │   ▲                                    │
    │    │              │   │                                    │
    │    │   heartbeat  │   │ adb reconnect                      │
    │    │   fail       │   │                                    │
    │    │              ▼   │                                    │
    │    │           OFFLINE                                     │
    │    │              │                                        │
    │    │   disconnect │                                        │
    │    │              ▼                                        │
    │    │        DISCONNECTED ─── adb scan ─────────────────────┘
    │    │              ▲
    │    │              │
    │    └── disconnect ┘
    │
    └──── 新设备 (adb scan) ─────────────────────────────────────┘
```

### 4.3 状态转换规则表

| # | 当前状态 | 事件 | 目标状态 | 前置条件 | 副作用 |
|---|----------|------|----------|----------|--------|
| 1 | (不存在) | adb scan 发现新设备 | ONLINE | adb devices 列表中有该 serial | INSERT device 记录 |
| 2 | OFFLINE | adb scan 发现设备恢复 | ONLINE | adb devices 列表中有该 serial | 更新 last_seen |
| 3 | ONLINE | lock 请求 | BUSY | 设备无活跃锁 | INSERT lock 记录，更新 locked_by/locked_at |
| 4 | BUSY | release 请求 | ONLINE | 锁持有者或管理员 | 更新锁状态为 released |
| 5 | BUSY | timeout 超时 | ONLINE | elapsed > timeout_seconds | 自动释放，记录日志 |
| 6 | ONLINE | adb scan 未发现 | OFFLINE | 不在 adb devices 列表中 | 更新 last_seen |
| 7 | OFFLINE | disconnect 请求 | DISCONNECTED | — | adb disconnect + 清缓存 |
| 8 | ONLINE | disconnect 请求 | DISCONNECTED | — | adb disconnect + 释放锁 |
| 9 | BUSY | disconnect 请求 | DISCONNECTED | 管理员权限 | 强制释放锁 + adb disconnect |
| 10 | DISCONNECTED | adb scan 发现 | ONLINE | adb devices 列表中有 | 重新注册连接信息 |

### 4.4 并发控制

- **锁定竞争**：数据库行级锁 `SELECT ... FOR UPDATE` 或乐观锁（version 字段）
- **状态同步**：每次轮询时 re-check 真实设备状态，以 adb 为准修正
- **DevicePool 单例**：`threading.Lock` 保护 `_instances` dict 的读写

---

## 5. 数据模型

### 5.1 dp_devices（设备注册表）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | BigAutoField | PK | 自增主键 |
| `serial` | CharField(100) | UNIQUE, NOT NULL | ADB 设备序列号（如 `RF8N21MSW7A` 或 `192.168.1.100:5555`） |
| `name` | CharField(200) | default='' | 设备别名（用户自定义，便于识别） |
| `model` | CharField(200) | default='' | 设备型号（如 `SM-G9980`），从 uiautomator2 获取 |
| `brand` | CharField(100) | default='' | 品牌（如 `Samsung`） |
| `screen_w` | IntegerField | default=0 | 屏幕宽度（px） |
| `screen_h` | IntegerField | default=0 | 屏幕高度（px） |
| `android_version` | CharField(20) | default='' | Android 系统版本（如 `13`） |
| `connection_type` | CharField(10) | default='USB' | 连接方式：`USB` / `WIFI` |
| `status` | CharField(20) | default='ONLINE' | 设备状态：ONLINE / BUSY / OFFLINE / DISCONNECTED |
| `locked_by` | CharField(200) | default='' | 锁定者标识（用户名或 IP） |
| `locked_at` | DateTimeField | null=True | 锁定时间戳 |
| `last_seen` | DateTimeField | auto_now=True | 最后一次在线时间 |
| `created_at` | DateTimeField | auto_now_add | 创建时间 |

**索引**：
- `serial` (UNIQUE)
- `status` (普通索引，用于筛选在线/离线设备)

### 5.2 dp_device_locks（设备锁记录）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | BigAutoField | PK | 自增主键 |
| `device` | ForeignKey(Device) | CASCADE, related_name='locks' | 关联设备 |
| `user_id` | CharField(200) | NOT NULL | 锁定者标识 |
| `status` | CharField(20) | default='active' | 锁状态：active / released / expired |
| `locked_at` | DateTimeField | auto_now_add | 锁定时间 |
| `released_at` | DateTimeField | null=True | 释放时间 |
| `timeout_seconds` | IntegerField | default=300 | 超时秒数（默认 300 = 5 分钟） |
| `release_reason` | CharField(20) | default='' | 释放原因：manual / timeout / disconnect / force |

**索引**：
- `(device_id, status)` 联合索引（快速查找设备活跃锁）

### 5.3 dp_device_queue（排队表，v2）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | BigAutoField | PK | 自增主键 |
| `device` | ForeignKey(Device) | CASCADE | 关联设备 |
| `user_id` | CharField(200) | NOT NULL | 排队用户 |
| `requested_at` | DateTimeField | auto_now_add | 请求时间 |
| `status` | CharField(20) | default='waiting' | waiting / assigned / cancelled / timeout |
| `assigned_at` | DateTimeField | null=True | 分配时间 |

---

## 6. API 接口规格

### 6.1 接口总览

| # | 方法 | 路径 | 功能 | v1/v2 |
|---|------|------|------|:--:|
| 1 | GET | `/api/devices` | 设备列表 + 心跳状态同步 | v1 |
| 2 | POST | `/api/devices/scan` | ADB 扫描并注册设备 | v1 |
| 3 | POST | `/api/devices/{serial}` | 连接设备（建立 uiautomator2 连接） | v1 |
| 4 | GET | `/api/devices/current` | 获取当前活动设备信息 | v1 |
| 5 | POST | `/api/devices/{serial}/activate` | 切换当前活动设备 | v1 |
| 6 | POST | `/api/devices/{serial}/disconnect` | 断开设备 + 释放锁 | v1 |
| 7 | POST | `/api/devices/{serial}/lock` | 锁定设备 | v2 |
| 8 | POST | `/api/devices/{serial}/release` | 释放设备锁 | v2 |
| 9 | GET | `/api/devices/queue` | 排队状态 | v2 |
| 10 | GET | `/api/devices/heartbeat` | 手动触发心跳检测 | v2 |

### 6.2 接口详细规格

#### 6.2.1 GET /api/devices — 设备列表

**Request**: 无参数（未来支持 `?status=ONLINE` 筛选）

**Response 200**:
```json
{
  "ok": true,
  "current": "RF8N21MSW7A",
  "queue_length": 2,
  "devices": [
    {
      "id": 1,
      "serial": "RF8N21MSW7A",
      "name": "三星测试机",
      "model": "SM-G9980",
      "brand": "Samsung",
      "screen": "1080×2400",
      "status": "ONLINE",
      "connection_type": "USB",
      "locked_by": "",
      "locked_at": null,
      "last_seen": "2026-06-30T14:58:00+08:00",
      "is_current": true
    }
  ]
}
```

**业务逻辑**：
1. 执行 `_update_device_status()` — 对比 adb devices 列表与数据库，更新状态
2. 检查 BUSY 设备是否超时，超时则自动释放
3. 查询所有设备记录，排序：ONLINE > BUSY > OFFLINE > DISCONNECTED

---

#### 6.2.2 POST /api/devices/scan — 扫描设备

**Request**:
```json
{
  "target": "RF8N21MSW7A"
}
```
或
```json
{
  "target": "192.168.1.100:5555"
}
```

`target` 可选：指定 USB 串号直接连接，或 IP:port 无线连接。不传则全量扫描。

**Response 200**:
```json
{
  "ok": true,
  "count": 3,
  "newly_added": 1,
  "devices": [...]
}
```

**Response 400**:
```json
{
  "ok": false,
  "error": "无法连接到 192.168.1.100:5555，请检查设备网络和 ADB 服务"
}
```

---

#### 6.2.3 POST /api/devices/{serial} — 连接设备

**Request**:
```json
{
  "activate": true
}
```

**Response 200**:
```json
{
  "ok": true,
  "serial": "RF8N21MSW7A",
  "model": "SM-G9980",
  "screen_w": 1080,
  "screen_h": 2400,
  "android_version": "13"
}
```

**业务逻辑**：
1. 验证设备记录存在且 status != OFFLINE && status != DISCONNECTED
2. 检查 BUSY 状态下的锁是否属于当前用户（非当前用户拒绝连接）
3. 通过 uiautomator2 建立连接：`u2.connect(serial)`
4. 连接成功后自动 update_or_create 设备信息（model/brand/resolution/android_version）
5. 如果 `activate=true`，切换为当前设备
6. 返回设备信息

**错误码**：

| 情况 | HTTP | error 字段 |
|------|:--:|------|
| serial 不存在 | 404 | `设备 {serial} 未注册` |
| 设备离线 | 400 | `设备已离线，无法连接` |
| 设备被他人锁定 | 409 | `设备已被 {locked_by} 锁定` |
| ADB 连接超时 | 504 | `连接超时，请检查设备 USB/WiFi 连接` |
| uiautomator2 服务异常 | 502 | `设备 ATX Agent 未运行` |

---

#### 6.2.4 POST /api/devices/{serial}/lock — 锁定设备

**Request**:
```json
{
  "user_id": "aeron",
  "timeout": 600
}
```

- `user_id`：必填，锁定者标识
- `timeout`：可选，默认 300 秒

**Response 200**:
```json
{
  "ok": true,
  "serial": "RF8N21MSW7A",
  "user_id": "aeron",
  "locked_at": "2026-06-30T15:00:00+08:00",
  "timeout": 600,
  "remaining": 600
}
```

**Response 409（冲突）**:
```json
{
  "ok": false,
  "error": "设备已被 bob 锁定，剩余 180 秒",
  "locked_by": "bob",
  "remaining": 180
}
```

---

#### 6.2.5 POST /api/devices/{serial}/release — 释放设备

**Request**:
```json
{
  "user_id": "aeron",
  "reason": "manual"
}
```

- `user_id`：可选，释放者标识（管理员强制释放时传入）
- `reason`：`manual` / `timeout` / `disconnect` / `force`

**Response 200**:
```json
{
  "ok": true,
  "serial": "RF8N21MSW7A",
  "released": true
}
```

---

#### 6.2.6 POST /api/devices/{serial}/disconnect — 强制断开

**Request**:
```json
{
  "force": true,
  "reason": "设备无响应超过 10 分钟"
}
```

- `force`：是否强制（当断开他人设备时必填 true + 需管理员权限）
- `reason`：断开原因（管理员操作时必填）

**Response 200**:
```json
{
  "ok": true,
  "serial": "RF8N21MSW7A",
  "disconnected": true,
  "locks_released": 1
}
```

---

#### 6.2.7 其他接口

| 接口 | Request | Response |
|------|---------|----------|
| `GET /api/devices/current` | — | `{ok, serial, screen_w, screen_h, package}` |
| `POST /api/devices/{serial}/activate` | — | `{ok, current: serial}` |
| `GET /api/devices/queue` | — | `{ok, queue: [{user_id, serial, waited_seconds}], count}` |
| `GET /api/devices/heartbeat` | — | `{ok, updated: 1, offline: 0}` |

---

## 7. 前端交互设计

### 7.1 页面布局

```
┌─────────────────────────────────────────────────────────────┐
│  设备管理                                    [排队 2] [扫描] [刷新] │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────┐│
│  │ ☐ │ 序列号 ↑      │ 型号    │ 分辨率     │ 状态 │ 锁定用户 │ 操作 ││
│  ├─────────────────────────────────────────────────────────┤│
│  │ ○ │ RF8N21MSW7A   │ SM-G9980│ 1080×2400 │ 🟢在线│ —       │ 切换 锁定 断开 连接 ││
│  │ ○ │ 192.168.1.100 │ MI 11   │ 1080×2400 │ 🟠使用中│ bob(3分钟)│ 当前 释放 断开 连接 ││
│  │   │ 9A261FFBA001  │ Pixel 6 │ 1080×2340 │ ⚫离线 │ —       │ 断开 ││
│  └─────────────────────────────────────────────────────────┘│
│                                                             │
│  [连接选中设备]   ← 勾选设备后点击跳转 element-locator         │
└─────────────────────────────────────────────────────────────┘
```

### 7.2 交互细节

**勾选 + 连接流程**：
1. 列表首列 radio button 单选设备
2. 选中一行后，底部「连接选中设备」按钮从 disabled → primary
3. 点击按钮 → loading 状态 → 成功后 toast 通知 + 自动跳转 element-locator

**锁定设备弹窗**：
```
┌──────────────────────────┐
│  锁定设备 RF8N21MSW7A    │
│                          │
│  锁定用户 ID: [aeron  ]  │
│  锁定时长:    [300  ] 秒  │
│                          │
│  [取消]        [确认锁定] │
└──────────────────────────┘
```

**强制断开二次确认**：
```
┌──────────────────────────────────┐
│  ⚠️ 强制断开设备                  │
│                                  │
│  确定要断开 9A261FFBA001 吗？     │
│  该设备状态：BUSY（锁定者：bob）   │
│  断开后该设备所有锁将被强制释放。   │
│                                  │
│  断开原因：[                  ]  │
│                                  │
│  [取消]            [强制断开]     │
└──────────────────────────────────┘
```

### 7.3 轮询与实时更新

- 前端 30 秒间隔 `GET /api/devices` 轮询刷新
- 页面聚焦时自动刷新一次
- 设备状态变化时 anime.js 淡入动画标识变更行

---

## 8. 非功能需求

| 类别 | 指标 | 目标值 | 衡量方式 |
|------|------|:--:|------|
| **性能** | 设备列表接口响应时间 | ≤500ms | APM 监控 |
| **性能** | 设备扫描耗时 | ≤3s | 日志计时 |
| **可靠性** | 断连检测延迟 | ≤30s | 心跳间隔 |
| **可靠性** | 锁超时释放精度 | ±5s | 定时检查 |
| **并发** | 支持并发锁定请求 | ≥10 QPS | 压力测试 |
| **并发** | 锁竞争无死锁 | 0 死锁事件 | 压测 + 代码审查 |
| **安全** | API 认证覆盖率 | 100%（除 heartbeat 读操作） | JWT 中间件 |
| **安全** | 强制断开审计日志 | 100% 记录 | 日志检查 |
| **可用性** | 无设备时友好提示 | 不报错，显示「暂无设备」+ 扫描引导 | 手动验证 |
| **兼容性** | Android 版本 | 8.0 - 15 | 测试矩阵 ≥5 台 |
| **兼容性** | ADB 版本 | 33.0+ | 版本检测 |

---

## 9. 非目标（Non-goals）

以下功能**不在**本模块范围内：

| 功能 | 原因 | 归属模块 |
|------|------|----------|
| 远程安装 APK | 属于测试执行的预处理步骤 | test-runner |
| 设备性能监控（CPU/内存/温度） | 属于设备健康监控独立系统 | 独立模块 (v3+) |
| iOS 设备管理 | 当前阶段仅支持 Android | 独立模块 (v4+) |
| 设备云（远程真机租用） | 属于 SaaS 基础设施 | 独立产品 (v4+) |
| 批量操作（一键锁多台/一键释放全部） | 当前设计为单台操作 | 后续迭代评估 |
| 设备分组（按项目/团队分配设备池） | 依赖 project-hub 模块 | project-hub (v3) |
| 图形化 ADB 命令执行器 | 属于调试工具 | 独立工具 |

---

## 10. 风险与应对

| 风险 | 概率 | 影响 | 应对策略 |
|------|:--:|:--:|------|
| uiautomator2 连接不稳定，频繁断连 | 中 | 高 | ①自动重连机制（最多 3 次）②心跳检测及时发现断连 ③断连后自动释放锁 |
| 多用户并发锁同设备产生竞态 | 低 | 高 | ①数据库行级锁/乐观锁 ②API 层先检查再写入 ③压测验证 |
| ADB Server 崩溃导致所有设备离线 | 低 | 高 | ①捕获 adb 命令异常并友好提示 ②自动重启 adb server（可选） |
| 锁超时释放不及时，设备被"僵尸占用" | 中 | 中 | ①每次心跳检测时检查超时 ②管理员强制释放兜底 |
| 无线 ADB 网络波动导致截图延迟高 | 中 | 中 | ①连接质量检测（ping 延迟）②提示用户切换 USB 连接 |
| 设备型号/分辨率获取失败 | 低 | 低 | 字段允许为空，UI 显示「—」 |

---

## 11. 里程碑

| 阶段 | 版本 | 交付物 | 对应功能 |
|------|------|------|----------|
| Phase 1 | v1 | 设备扫描、列表展示、状态监控 (ONLINE/OFFLINE) | F-01 部分 |
| Phase 2 | v2.0-alpha | 锁定/释放机制、超时自动释放、排队基础 | F-03, F-04, F-06 |
| Phase 3 | v2.0-beta | 设备连接+实时画面跳转、强制断开 | F-02, F-05 |
| Phase 4 | v2.0 | 前端完整交互、轮询优化、错误处理完善 | 全部 F-01~F-06 |
| Phase 5 | v3.0 | 多项目设备分组、权限体系集成 | 全局PRD Phase 5 |

---

## 12. 变更记录

| 版本 | 日期 | 变更类型 | 变更摘要 |
|------|------|----------|----------|
| v1.0 | 2026-06-30 | — | 初始骨架版本：功能清单 + 用户故事 + API 端点 + 状态机 |
| v2.0 | 2026-06-30 | 重写 | 完整产品规格：补充业务逻辑、数据模型字段定义、API 请求/响应 schema、前端交互设计、错误码、并发控制、Non-goals、风险应对 |
