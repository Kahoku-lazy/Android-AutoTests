# PRD-02 — 设备管理 (Device Pool)

> 关联模块：`apps/device_pool/` · 前端：`frontend/src/modules/device-pool/`
> 关联全局：[`需求大纲.md`](./需求大纲.md) §5.2
> 版本：v6.5 · 状态：评审中 · 日期：2026-08-21

**修订记录**

| 版本 | 日期 | 变更摘要 |
|------|------|----------|
| v6.5 | 2026-08-21 | 以代码为真相源偏差登记：权限 403 校验未实施（删除/锁定/释放）、locked 字段补入契约、release_reason 枚举校正、锁超时按占用方区分（300/1800/3600s）、信封示例改 {status,data}、connect timeout/user_id 标注、disconnect-observe 消费方校正、C-08 实施位置修正 |
| v6.0 | 2026-08-14 | 按仪表盘 PRD 格式重构：移除实现细节（文件行数/实施状态/已知问题），补齐功能详细规格（F-XX-XX 逐项 + 边界状态 + 验收标准）、布局与视觉设计、后端功能逻辑、API 字段级契约（13 端点）、数据来源表、非功能/非目标/关键约束/文件索引；同步代码真相（Pinia→composable、.js→.ts、views.py→views/ 包、动森→Doodle Craft） |
| v6.1 | 2026-08-17 | DRF 化 + 写收敛：views/ → views.py + service.py；响应信封统一 `{status, data}`（前端解包 data）；修 connect 用户锁误设 BUSY；移除前端 is_admin 冗余字段 |
| v6.2 | 2026-08-17 | 移除离线设备记录：设备离线即删除（BUSY 保护）；状态统计 4 卡→3 卡、筛选 4 tab→3 tab、卡片 3 组→2 组；状态机收敛为 ONLINE/BUSY 两态 |
| v6.3 | 2026-08-17 | 操作功能重构：设备锁定改为「锁定/公开」可见性（USB 恒公开无锁定、局域网默认锁定、仅管理员+锁定者可见、登录用户只操作自己的局域网设备）；设备释放改为「强制释放」且仅释放设备检查器占用；设备断开改为「删除」（在线可删、使用中置灰、USB 无删除键）；删除加入排队/取消排队功能（端点 13→10） |
| v6.4 | 2026-08-18 | observe 契约改为「连接即占用」：connect `mode=observe` 置 BUSY（使用中），`disconnect-observe` 释放为 ONLINE（在线） |
| v5.0 | 2026-07-25 | 拍立得 KPI 卡片、Dual 视图（表格/卡片）、FilterTabs 迁入 shared、模块背景点阵纸纹、全宽布局 |

---

## 1. 功能定位

设备管理是平台的**设备基础设施层**，是唯一直接与 Android 设备通信的模块。用户在此扫描、连接、锁定、释放 Android 设备。页面由两个区块自上而下排列：统计概览 → 设备列表。

**核心职责**：

- **设备发现**：通过扫描 ADB 设备（USB / 无线）发现设备，按序列号去重后注册到设备池
- **设备连接**：通过 uiautomator2 + Airtest 双连接，采集设备元信息
- **设备锁定 / 释放**：锁定 / 公开控制设备可见性；强制释放解除设备检查器占用
- **设备断开**：删除局域网设备（在线可删、使用中置灰）
- **状态统计**：设备状态分布（在线 / 使用中 / 总计）

设备管理是**管理模块（有写操作）**：区别于仪表盘的只读聚合，所有写操作走 `api.ts` → djangoClient，组件不直连 HTTP。

---

## 2. 功能详细规格

### 2.1 设备发现（F-01-01）

点击「刷新」按钮，扫描当前 ADB 可见的全部设备（USB / 无线），注册到设备池并采集元信息。

**设备唯一性**：以设备序列号（serial）判断是否同一台设备；USB 设备直接取序列号，无线设备通过 `adb -s <IP:port> shell getprop ro.serialno` 获取序列号。

**去重规则**：

- 相同序列号的设备只允许添加一次
- 局域网添加同样查重；设备已存在时提示「设备已存在」+ 被谁添加 + 设备信息

**组件**：`index.vue` 刷新按钮（`handleRefresh` → `loadDevices`）。

**边界状态**：

| 场景 | 行为 |
|------|------|
| adb 无设备 | 返回空列表，前端显示空态「暂无设备」 |
| 设备已存在（重复添加） | 提示「设备已存在」；局域网设备附「被谁添加 + 设备信息」，不重复注册 |

**验收标准**：

- 全量扫描返回 `count` 与 `newly_added` 与列表一致
- 新设备首次扫描后元信息（model/brand/screen）已采集
- 相同序列号的设备只注册一次，重复添加提示「设备已存在」

### 2.2 连接无线设备（F-01-02）

通过 IP 地址与端口连接无线调试设备。用户点击「局域网连接」按钮，在弹窗中填写 IP 与端口，校验通过后系统建立连接并将设备加入设备池。

| 字段 | 校验 |
|------|------|
| IP 地址 | IPv4 点分十进制，每段 0–255 |
| 端口 | 1–65535 整数（默认 5555） |

**组件**：`NetworkConnectDialog.vue`（弹窗表单，聚焦第一个非法字段）。

**边界状态**：

| 场景 | 行为 |
|------|------|
| IP 格式非法 | 表单内提示「请输入合法的 IPv4 地址」，不发送请求 |
| 无法连接目标设备 | 提示「无法连接到目标设备」 |
| 连接超时 | 提示「连接超时」 |

**验收标准**：

- IP/端口前端与后端双重校验
- 连接成功后设备出现在列表，连接方式显示「无线」
- 提交中 loading 态防止重复提交

### 2.3 状态统计（F-02-01）

页面顶部 3 张拍立得 KPI 卡片，展示设备状态分布。每张卡片由「几何图形 + 标签 + 数字」组成，微旋转排列，hover 归正放大。

| 卡片 | 颜色 | 图形 | 口径 |
|------|:--:|:--:|------|
| 在线 | 薄荷绿 `#6BCB77` | ◆ 菱形 | 状态为「在线」的设备数 |
| 使用中 | 桃粉 `#FFB5A7` | ▲ 三角 | 状态为「使用中」的设备数 |
| 总计 | 墨黑 `var(--ink)` | ● 圆 | 全部设备总数 |

**组件**：`KpiCard.vue`。

**边界状态**：

| 场景 | 行为 |
|------|------|
| 无设备 | 三卡均显示 0 |
| 数据加载中 | 列表 loading 态，KPI 由已加载数据派生 |

**验收标准**：

- 三卡数值与设备列表一致（在线 + 使用中 = 总计）
- 卡片图形（菱形/三角/圆）与颜色映射正确

### 2.4 设备列表（F-02-02）

设备列表支持状态筛选、表格 / 卡片双视图与分页，顶部工具栏提供筛选与操作入口。

**工具栏**：

| 元素 | 位置 | 功能 |
|------|------|------|
| 状态筛选（全部 / 在线 / 使用中） | 左 | 按状态筛选设备 |
| 视图切换（表格 / 卡片） | 右 | 双视图切换 |
| 设备计数「N 台」 | 右 | 实时数量 |
| 局域网连接 | 右 | 打开无线连接弹窗 |
| 刷新 | 右 | 重新扫描设备，loading 旋转 |

**表格视图**（10 列）：

| 列 | 说明 |
|------|------|
| 设备地址 | 原始 adb devices 传输地址（USB 即序列号，无线为 IP:port / mDNS） |
| 序列号 | 设备序列号，等宽字体，当前设备加 ● 标记 |
| 型号 | 品牌 + 型号 |
| 分辨率 | 屏幕分辨率，空显示灰「—」 |
| 状态 | 运行状态标签：在线 / 使用中 |
| 连接 | USB 有线 / 局域网连接（备注「局域网连接：IP 地址」，如 10.162.95.96:44517） |
| 锁定 | 锁定者 / 「共用」，紫底 / 绿底标签 |
| 设备连接时间点 | 设备连接到平台的时间点 |
| 最后在线 | 相对时间 |
| 操作 | 设备操作按钮：锁定 / 强制释放 / 删除，按设备状态与权限条件显示（详见 §2.5 操作功能详细说明） |

**卡片视图**：按状态分 2 组（🟢在线 / 🔴使用中），空组自动隐藏。卡片标题显示设备序列号；卡片主体逐字段以「列名：内容」格式展示：

| 字段 | 说明 |
|------|------|
| 设备地址 | 原始 adb devices 传输地址（USB 即序列号，无线为 IP:port / mDNS） |
| 型号 | 品牌 + 型号 |
| 分辨率 | 屏幕分辨率，空显示灰「—」 |
| 状态 | 运行状态标签：在线 / 使用中 |
| 最后在线 | 相对时间 |

卡片操作按钮与表格「操作」列完全一致（锁定 / 强制释放 / 删除），按设备状态与权限条件显示（详见 §2.5 操作功能详细说明）。

**边界状态**：

| 场景 | 行为 |
|------|------|
| 列表为空 | 空态「暂无设备，点击刷新扫描」/「没有匹配的设备」 |
| 分页 | 每页 [5, 10, 20] 条可选 |

**验收标准**：

- 表格 / 卡片双视图切换后筛选、分页状态一致
- 设备按「在线 > 使用中」排序
- 卡片可键盘操作
- 卡片字段以「列名：内容」展示，操作按钮与表格「操作」列一致

### 2.5 操作功能详细说明

以下 F-02-03 ~ F-02-05 均为**设备操作**，由设备列表「操作」列按钮触发：

| 功能 | 操作入口 |
|------|---------|
| 设备锁定 | 操作列「已锁定 / 公开」切换按钮（仅局域网设备） |
| 设备释放 | 操作列「强制释放」按钮（仅设备被占用时显示） |
| 设备断开 | 操作列「删除」按钮（仅局域网在线设备） |

#### 2.5.1 设备锁定（F-02-03）

**功能设计目的**：便于用户管理手机——通过「锁定 / 公开」控制设备对其他用户的可见性与使用权。

**权限逻辑**：

| 逻辑 | 说明 |
|------|------|
| 管理员 | 可查看所有用户通过局域网配置的设备（无论锁定 / 公开） |
| 登录用户 | 只能对自己通过局域网配置的设备执行「公开 / 锁定」操作 |
| 锁定 / 公开 | 锁定：除管理员与有锁定权限的用户外，其他用户无法使用、设备列表不显示；公开：所有用户可见可用 |

**默认可见性**：

- USB 连接的设备：默认**公开**，不支持锁定（操作栏不显示锁定按钮）
- 局域网配置的设备：默认**已锁定**，点击后才公开

**组件**：设备操作列的「已锁定 / 公开」切换按钮（仅局域网设备显示）。

**边界状态**：

| 场景 | 行为 | 触发方式 |
|------|------|---------|
| 已锁定 | 除管理员与有锁定权限的用户外，其他用户无法使用、设备列表不显示 | 局域网设备注册后的默认状态 |
| 公开 | 所有用户可见可用 | 点击「已锁定」按钮切换 |
| USB 设备 | 恒为公开，操作栏无锁定按钮 | USB 连接（无锁定能力） |

**验收标准**：

- USB 设备不显示锁定按钮，恒为公开
- 局域网设备默认已锁定，点击按钮在「已锁定 / 公开」间切换
- 登录用户只能对自己配置的局域网设备执行「公开 / 锁定」，无法操作他人设备 ⚠️ 未实施（见 §4.6 偏差登记）
- 锁定时，除管理员与有锁定权限的用户外，其他用户列表不显示该设备
- 每次锁定 / 公开切换记录审计

#### 2.5.2 设备释放（F-02-04）

**功能定义**：

| 项 | 说明 |
|----|------|
| 关联状态 | 设备检查器 / 执行引擎调用设备时，设备标记「使用中」，其他用户无法使用 |
| 释放范围 | 仅释放设备检查器调用的设备（执行引擎占用受保护，不可释放） |
| 释放行为 | 强退出使用中的用户、断开设备连接，设备检查器中选中的设备被取消 |
| 权限 | 仅管理员，或配置了该局域网设备的用户 |

**组件**：设备操作列的「强制释放」按钮（设备未被占用时不显示）。

**边界状态**：

| 场景 | 行为 | 触发方式 |
|------|------|---------|
| 设备检查器占用中 | 释放后强退出使用中用户、断开连接、检查器选中设备被取消 | 点击「强制释放」 |
| 执行引擎占用中 | 不显示释放按钮（受保护，不可释放） | 执行引擎占用 |
| 设备未被占用 | 不显示释放按钮 | 设备空闲 |

**验收标准**：

- 仅管理员或局域网设备配置者可释放 ⚠️ 未实施（见 §4.6 偏差登记）
- 设备未被占用时不显示「强制释放」按钮
- 释放设备检查器占用的设备后，强退出使用中用户、断开连接、检查器选中设备被取消
- 执行引擎占用的设备不可释放（受保护）

#### 2.5.3 设备断开（F-02-05）

**功能定义**：删除局域网设备——仅「在线」状态可删除；「使用中」状态删除键置灰、不可交互。

**权限**：

- 管理员：可删除设备
- 配置局域网连接的用户：只能删除自己的设备
- USB 设备：无删除键

**组件**：设备操作列的「删除」按钮（仅局域网在线设备可点）。

**边界状态**：

| 场景 | 行为 | 触发方式 |
|------|------|---------|
| 在线（局域网） | 删除键可点，删除设备记录 | 设备在线 |
| 使用中 | 删除键置灰、不可交互 | 设备被占用 |
| USB 设备 | 无删除键 | USB 连接 |

**验收标准**：

- 仅管理员或局域网设备配置者可删除，配置者只能删除自己的设备 ⚠️ 未实施（见 §4.6 偏差登记）
- USB 设备不显示删除键
- 使用中设备删除键置灰、不可交互
- 删除后设备记录移除、连接缓存清理

---

## 3. 布局与视觉设计

> 全部颜色/字号引用 Doodle Craft 主题令牌（[`frontend/CLAUDE.md` §2](../../frontend/CLAUDE.md)）。KPI 卡片颜色为 hex 字面量（见约束 C-03）。

### 3.1 页面布局

```
┌─────────────────────────────────────────────┐
│ WorkbenchHeader（标题）                        │
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
| 状态边 | 在线绿 / 使用中粉（`--app-status-success` / `--app-status-danger`） |

### 3.3 状态与组件规格

| 元素 | 规格 |
|------|------|
| 状态 el-tag | 不对称圆角 `4px 8px` + 1.5px 状态色边 + 状态色底 |
| 状态 Badge | 执行中粉 / 占用中黄 / 已锁定紫，圆角 `3px 6px` |
| 视图切换 | 2px 模块色边圆角容器，active 填模块色白字 |
| 操作按钮 | 圆角 `4px 8px` + 2px 边 + 状态色（锁定紫 / 删除红） |

### 3.4 KPI 配色（模块状态色）

| 卡片 | 色值 |
|------|------|
| 在线 | `#6BCB77`（薄荷绿） |
| 使用中 | `#FFB5A7`（桃粉） |
| 总计 | `var(--ink)`（墨黑） |

---

## 4. 后端功能逻辑

### 4.1 设备状态机

```
(new) → ONLINE ──占用──→ BUSY ──释放/超时──→ ONLINE
                     │
    adb 不可见且锁超时
                     ↓
                （删除记录）
```

| 状态 | 含义 | 进入条件 |
|------|------|---------|
| `ONLINE` | 在线可用 | adb 可见且未被占用 |
| `BUSY` | 使用中 | 进程占用（设备检查器 / 执行引擎） |

> ⚠️ 设备不在 adb 列表时：BUSY 保护进行中任务（锁超时后删除），非 BUSY 直接删除记录——不保留离线/DISCONNECTED 墓碑。

### 4.2 锁口径

| 项 | 说明 |
|------|------|
| 锁语义 | 锁定 / 公开（可见性，不改 status）+ 占用（设备检查器 / 执行引擎，改 BUSY） |
| lock_type | `user`（锁定/公开）· `observe`（设备检查器观察占用）· `process`（执行引擎占用） |
| 审计 | DeviceLock 永不删除，通过 `status`（active/released/expired）追踪生命周期 |
| 并发 | 数据库 UNIQUE 约束保证同一设备同时最多 1 个活跃锁 |
| 超时 | 按占用方区分：用户锁 300s（`models.py:69` 默认）/ observe 1800s（`service.py:26` OBSERVE_LOCK_TTL）/ 执行引擎 3600s（见 PRD-06 §4.3）；`remaining_seconds` 计算剩余时长 |
| 释放原因 | manual / timeout / disconnect / offline / purge（无 force；`service.py:175/189/192/248/441/472/500`） |

### 4.4 心跳与状态同步

- 前端每 30s 轮询 `heartbeat`（`HEARTBEAT_INTERVAL`）
- `_update_device_status`：同步 adb 真实状态 → DB；设备离线即删除（BUSY 保护），BUSY 锁超时自动释放

### 4.5 降级规则

| 场景 | 行为 |
|------|------|
| adb 不可用 | `_adb_device_serials` 返回空集，非 BUSY 设备删除记录，BUSY 设备锁超时后删除 |
| 设备信息采集失败 | 记录 warning，不影响注册 |
| 心跳失败 | 前端 debug 日志，不打断 UI |

### 4.6 已知偏差登记

| 偏差 | 说明 |
|------|------|
| ⚠️ 删除设备权限 403 未实施 | `views.py:300-313` disconnect 仅判 USB（400）/BUSY（409），未校验「仅管理员或局域网配置者可删」（产品口径见 §2.5.3） |
| ⚠️ 锁定/公开权限 403 未实施 | `service.py:423-443` set_device_lock 仅判 USB（400）/锁冲突（409），未校验「登录用户只能操作自己的局域网设备」（产品口径见 §2.5.1） |
| ⚠️ 释放权限 403 未实施 | `service.py:464-473` release_occupy 仅判 runner 前缀（409）/空（400），未校验「仅管理员或配置者可释放」（产品口径见 §2.5.2） |
| 心跳响应兼容占位字段 | `offline_count`/`disconnected` 恒 0（`service.py:537-538`）；`offline` 返回本次同步删除数 `removed`（`service.py:534`），非「离线设备数」 |
| connect `timeout`/`user_id` 不读 | `views.py:244-246` 仅取 JWT `user_id` 用于 observe 锁/claim；请求体 `timeout`/`user_id` 未消费 |
| OFFLINE/DISCONNECTED 残留 | 前端 `constants.ts:48-53` 仍定义 OFFLINE/DISCONNECTED 状态映射；`service.py:244-249` purge_disconnected_devices 残留清理逻辑——属已声明技术债（PRD-03 v1.1 同源） |

---

## 5. API 接口功能

鉴权：全部端点需要 JWT Bearer 鉴权（公开路径除外）。响应统一 `{status, data}` / `{status, message}`，JSON 字段 snake_case。

### 5.1 端点总览

| # | 方法 | 端点 | 功能 | 前端消费 |
|---|------|------|------|:--:|
| 1 | GET | `/api/devices/` | 设备列表 + 当前设备 | ✅ |
| 2 | POST | `/api/devices/scan` | ADB 扫描注册（F-01-01） | ✅ |
| 3 | GET | `/api/devices/current` | 当前活动设备信息 | ❌ |
| 4 | GET | `/api/devices/heartbeat` | 心跳检测 + 状态同步 | ✅ |
| 5 | POST | `/api/devices/{serial}` | 连接设备（F-01-02） | ✅ |
| 6 | POST | `/api/devices/{serial}/disconnect` | 删除设备（F-02-05） | ✅ |
| 7 | POST | `/api/devices/{serial}/disconnect-observe` | 释放观察占用（observe） | ✅ |
| 8 | POST | `/api/devices/{serial}/activate` | 激活设备 | ✅ |
| 9 | POST | `/api/devices/{serial}/lock` | 锁定设备（F-02-03） | ✅ |
| 10 | POST | `/api/devices/{serial}/release` | 释放设备（F-02-04） | ✅ |

> 端点 3（`/current`）前端未消费；端点 7（`/disconnect-observe`）由 case-manager 调试设备在断开观察连接时消费（`case-manager/api/uiAutomation.ts:76`；设备检查器 v1.7 起不再调用，见 PRD-03 §5.1）。

### 5.2 端点 1 — 设备列表

**接口地址**：`GET /api/devices/`

**请求**：无参数。

**响应 data 字段**：

| 字段 | 类型 | 必填 | 约束 | 说明 |
|------|------|:--:|------|------|
| `devices[]` | array | 是 | 按 ONLINE > BUSY 排序 | 设备列表 |
| `current` | string \| null | 是 | 当前激活设备 serial，无则 null | 当前设备 |

**devices 元素字段**：

| 字段 | 类型 | 必填 | 约束 | 说明 |
|------|------|:--:|------|------|
| `id` | number | 是 | 整数 | 设备记录 ID |
| `serial` | string | 是 | 非空，≤100 字符，唯一 | 序列号 |
| `name` | string | 是 | 可空 | 设备名 |
| `model` | string | 是 | 可空 | 型号 |
| `brand` | string | 是 | 可空 | 品牌 |
| `screen` | string | 是 | 可空，格式 `WxH` | 分辨率 |
| `status` | string | 是 | 枚举 `ONLINE`/`BUSY`（离线设备即删除，不返回） | 状态 |
| `connection_type` | string | 是 | 枚举 `USB`/`WIFI` | 连接类型 |
| `locked_by` | string | 是 | 可空 | 锁定者用户 |
| `locked` | boolean | 是 | `locked_by` 非空且 WIFI 时为 true | 锁定/公开标记（`service.py:361`，前端 `useDeviceActions.ts` 消费） |
| `locked_at` | string \| null | 是 | ISO 时间或 null | 锁定时间 |
| `occupied_by` | string | 是 | 可空 | 占用进程 |
| `occupied_at` | string \| null | 是 | ISO 时间或 null | 占用时间 |
| `last_seen` | string \| null | 是 | ISO 时间或 null | 最后在线 |
| `is_current` | boolean | 是 | — | 是否当前激活 |
| `remaining` | number | 是 | 整数 ≥0；BUSY 时剩余秒 | 锁剩余时长 |
| `connection_addr` | string | 是 | 无线设备为 `IP:port` | 连接地址（列表「局域网连接：IP」显示） |
| `connected_at` | string \| null | 是 | ISO 时间或 null | 设备连接时间点 |
| `added_by` | string | 是 | 可空 | 添加人（去重提示「被谁添加」） |

**响应示例**：

```json
{
  "status": true,
  "data": {
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
        "locked": false,
        "locked_by": "",
        "locked_at": null,
        "occupied_by": "",
        "occupied_at": null,
        "last_seen": "2026-08-14T10:00:00",
        "is_current": true,
        "remaining": 0
      }
    ],
    "current": "emulator-5554"
  }
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

**去重**：以设备序列号判断唯一性，无线设备通过 `adb -s <IP:port> shell getprop ro.serialno` 获取序列号；相同序列号不重复注册。

**响应示例**：

```json
{ "status": true, "data": { "count": 1, "newly_added": 0, "devices": [ { "serial": "emulator-5554", "status": "ONLINE" } ] } }
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
| `online` / `busy` | number | 当前 ONLINE / BUSY 状态计数 |
| `offline` | number | ⚠️ 兼容占位：返回本次同步删除数 `removed`（非「离线设备数」，`service.py:534`） |
| `offline_count` / `disconnected` | number | ⚠️ 兼容占位：恒 0（`service.py:537-538`） |
| `total` | number | 状态计数总和 |

### 5.6 端点 5 — 连接设备

**接口地址**：`POST /api/devices/{serial}`

**请求字段**：

| 字段 | 类型 | 必填 | 约束 | 说明 |
|------|------|:--:|------|------|
| `activate` | boolean | 否 | 默认 true | 是否自动激活 |
| `mode` | string | 否 | `observe` 检查器连接（置使用中 BUSY） | 连接模式 |
| `user_id` | string | 否 | ⚠️ 代码当前不读（实际取 JWT `user_id`） | 操作用户 |
| `timeout` | number | 否 | ⚠️ 代码当前不读 | 锁超时秒 |

**响应 data 字段**：`serial` / `model` / `screen_w` / `screen_h` / `android_version`。

**错误**：设备未注册 404；他人锁定 409 ⚠️ 未实施（`views.py:249-250` 只判 BUSY）；ATX Agent 未运行 502；连接超时 504。

### 5.7 端点 6 — 删除设备

**接口地址**：`POST /api/devices/{serial}/disconnect`

**请求字段**：无（操作用户由 JWT 注入）。

**响应 data 字段**：`serial` / `deleted`（bool）。

**错误**：未注册 404；设备使用中 409（删除键置灰不可交互）；USB 设备 400（无删除键）；无权限 403 ⚠️ 未实施（见 §4.6 偏差登记）。

### 5.8 端点 7 — 释放观察占用（observe）

**接口地址**：`POST /api/devices/{serial}/disconnect-observe`

清理 uiautomator2 连接缓存，并释放观察占用（仅当占用者为观察连接时恢复 ONLINE；执行引擎占用受保护，不释放）。供 case-manager 调试设备断开观察连接时消费（设备检查器 v1.7 起不再调用）。

**响应 data 字段**：`serial` / `message`。

### 5.9 端点 8 — 激活设备

**接口地址**：`POST /api/devices/{serial}/activate`

切换 DevicePool 当前设备指针。响应 `{status, current}`。

### 5.10 端点 9 — 锁定 / 公开设备

**接口地址**：`POST /api/devices/{serial}/lock`

**请求字段**：

| 字段 | 类型 | 必填 | 约束 | 说明 |
|------|------|:--:|------|------|
| `locked` | boolean | 是 | true=锁定，false=公开 | 切换设备可见性 |

**响应 data 字段**：`serial` / `locked`（bool）。

**错误**：未注册 404；USB 设备 400（无锁定能力）；无权限 403（仅管理员或局域网设备配置者）⚠️ 未实施（见 §4.6 偏差登记）。

### 5.11 端点 10 — 释放设备

**接口地址**：`POST /api/devices/{serial}/release`

**请求字段**：无（操作用户由 JWT 注入）。

**响应 data 字段**：`serial` / `released`（bool）。

**错误**：未注册 404；执行引擎占用 409（受保护，不可释放）；设备未被占用 400；无权限 403 ⚠️ 未实施（见 §4.6 偏差登记）。

### 5.12 契约变更

| 版本 | 变更 |
|------|------|
| v5.0 | 锁定语义拆分 user / occupy（`lock_type`）；释放增加 `unlock`/`force` 参数 |
| v6.0 | 端点清单校正：10 端点（前端消费 8，`/current`、`/disconnect-observe` 为 observe 后端接口） |

---

## 6. 数据来源表

| 表 | 表前缀 | 说明 |
|------|:--:|------|
| `dp_devices` | dp_ | 设备注册表（serial 唯一 + 元信息 + 状态 + 绑定/占用） |
| `dp_device_locks` | dp_ | 锁审计表（永不删除，status 追踪生命周期） |

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
| 离线 / 断开设备持久化历史 | 设备离线或断开即删记录，无墓碑 |

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
| C-08 | 心跳超时 300s 自动释放 | `service.py`（`update_device_status` / `heartbeat_sync`） |

---

## 10. 相关文件索引

| 层 | 文件 | 说明 |
|------|------|------|
| 前端 | `frontend/src/modules/device-pool/index.vue` | 页面编排（241 行） |
| 前端 | `frontend/src/modules/device-pool/DevicePoolView.logic.ts` | 编排器 useDevicePoolView |
| 前端 | `frontend/src/modules/device-pool/DevicePoolView.style.css` | 页面样式（Doodle Craft） |
| 前端 | `frontend/src/modules/device-pool/api.ts` | 数据层（8 端点） |
| 前端 | `frontend/src/modules/device-pool/constants.ts` | 状态映射/列/分组配置 |
| 前端 | `frontend/src/modules/device-pool/helpers.ts` | 纯函数 |
| 前端 | `frontend/src/modules/device-pool/composables/` | useDevicePoolState / useDeviceActions / useHeartbeat |
| 前端 | `frontend/src/modules/device-pool/components/` | DeviceCard / DeviceStatusCell / DeviceActionsCell / DisconnectDialog / NetworkConnectDialog |
| 后端 | `apps/device_pool/models.py` | 2 表定义 |
| 后端 | `apps/device_pool/urls.py` | 10 端点路由 |
| 后端 | `apps/device_pool/views.py` | DRF 入口（@api_view，10 端点） |
| 后端 | `apps/device_pool/service.py` | 内部业务逻辑 + ORM 写收敛 |
| 后端 | `apps/device_pool/api.py` | 跨模块写操作白名单 |
| 后端 | `apps/device_pool/pool.py` | DevicePool 单例（Airtest + u2） |

---

## 附录A：功能边界规则

| 边界 | 规则 |
|------|------|
| 我能做什么 | 扫描/连接/锁定/释放/断开设备、查看状态分布 |
| 我不能做什么 | 在设备上执行用例（执行引擎）、定位元素（元素定位）、AI 操控（AI 助手） |
| 如需越界 | 由 element-locator / test-runner / AI 助手通过 api.py / DevicePool 调用本模块能力 |
| 数据可见性 | 设备列表按当前 ADB 可见性 + DB 状态展示 |
