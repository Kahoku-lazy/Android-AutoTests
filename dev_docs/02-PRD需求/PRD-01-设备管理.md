# PRD-01 — 设备管理 (Device Pool)

> 关联需求大纲：[`需求大纲.md`](./需求大纲.md) §5.1
> 版本：v5.0 · 日期：2026-07-25

---

## 1. 功能定位

设备管理是平台的设备基础设施。用户在此扫描、连接、锁定、释放 Android 设备。页面由两个功能模块自上而下排列：统计概览 → 设备列表。

---

## 2. 设计目录

```
frontend/src/modules/device-pool/
├── index.vue                         620 行 · 页面编排者
├── api.js                             64 行 · 数据层（11 端点）
├── routes.js                           8 行 · 路由定义
├── store.js                          224 行 · Pinia 状态管理
├── constants.js                      107 行 · 常量/配置/工具函数
├── composables/
│   └── useDeviceActions.js             —  · 设备操作逻辑（锁定/释放/排队）
└── components/
    ├── DeviceCard.vue                  —  · 设备卡片（卡片视图）
    ├── DeviceStatusCell.vue            —  · 状态列渲染（表格视图）
    ├── DeviceActionsCell.vue           —  · 操作列渲染（锁定/释放/断开按钮）
    ├── QueuePanel.vue                  —  · 排队面板
    ├── DisconnectDialog.vue            —  · 强制断开确认弹窗
    └── NetworkConnectDialog.vue        —  · WiFi 局域网连接弹窗
```

**架构特征**：L4 全约束，四层分离（展示/逻辑/数据/基础设施），零跨模块 import，零裸调 API。项目仅有的两个 L4 模块之一（与 workflow 并列）。

---

## 3. 核心功能

### 3.1 统计概览（KpiCard × 4）

页面顶部 4 张拍立得风格卡片，展示设备状态分布。每张卡片包含：彩色几何图形（菱形/三角/方块/圆）→ 标签（加粗）→ 数字。微旋转排列，hover 时归正放大。

| 卡片 | 颜色 | 图形 | 含义 |
|------|:--:|:--:|------|
| 在线 | `#6BCB77` 薄荷绿 | ◆ 菱形 | `status === 'ONLINE'` 的设备数 |
| 使用中 | `#FFB5A7` 桃粉 | ▲ 三角 | `status === 'BUSY'` 的设备数 |
| 离线 | `#d4d8dc` 浅灰 | ■ 方块 | `status === 'OFFLINE' \|\| 'DISCONNECTED'` 的设备数 |
| 总计 | `var(--ink)` 墨黑 | ● 圆 | 全部设备总数 |

**组件**：`shared/components/KpiCard.vue`
- Props: value / label / color / shape
- 几何图形：菱形旋转 45°、三角 clip-path 裁剪、方块 Doodle Craft 不对称圆角、圆 border-radius 50%
- 标签 font-weight: 700，数字 font-weight: 800

### 3.2 设备列表

设备筛选 + 操作工具栏 + 表格/卡片双视图。

#### 3.2.1 工具栏

| 元素 | 位置 | 功能 |
|------|------|------|
| FilterTabs（全部/在线/使用中/离线） | 左侧 | 按状态筛选设备 |
| 视图切换（📋表格/📷卡片） | 右侧 | 表格视图 vs 分组卡片视图 |
| 设备计数 | 右侧 | "12 台" 实时数量 |
| 局域网连接 | 右侧 | 弹出 WiFi ADB 连接弹窗 |
| 刷新设备 | 右侧 | 重新扫描 ADB 设备，loading 态显示旋转 |

**组件**：`shared/components/FilterTabs.vue`（从 device-pool/components/ 迁入 shared，消除跨模块 import 违规）

#### 3.2.2 表格视图

8 列数据表格，通过 `shared/components/AppTable.vue` 渲染：

| 列 | 渲染方式 | 说明 |
|------|------|------|
| 序列号 | 等宽字体 + 当前设备高亮 ● | `record.serial` |
| 型号 | `displayModel(record)` | brand + model 组合 |
| 分辨率 | `record.screen` | — 时显示灰色 "—" |
| 状态 | `DeviceStatusCell` 子组件 | ONLINE/BUSY/OFFLINE/DISCONNECTED 四种标签 |
| 连接 | `connectionLabel(record.connection_type)` | USB 有线 / 无线 ADB |
| 锁定 | 锁定者用户名 / "共用" | 蓝底标签 vs 绿底标签 |
| 最后在线 | `formatRelativeTime(record.last_seen)` | 相对时间格式化 |
| 操作 | `DeviceActionsCell` 子组件 | 锁定/解除占用/断开，按状态条件禁用 |

离线设备行半透明（`opacity: 0.5`）。分页通过 `shared/composables/usePagination.js`，选项 [5, 10, 20]。

#### 3.2.3 卡片视图

按状态分 3 组展示（🟢 在线 / 🔴 使用中 / ⚫ 离线）。筛选为「全部设备」时三组同时显示，筛选为具体状态时仅显示对应组。每张卡片通过 `DeviceCard.vue` 渲染，包含序列号、型号、状态标签、操作按钮。空组自动隐藏。

---

## 4. 数据流

```
Pinia store (store.js)
  ├── devices[]         原始设备列表（来自 API）
  ├── loading/scanning  请求状态
  └── selectedSerial    当前选中设备

useDeviceActions (composable)
  ├── loadDevices()     API 扫描 + 心跳轮询
  ├── handleLockClick()  锁定设备
  ├── handleRelease()    释放设备
  └── handleJoinQueue()  加入排队

index.vue
  ├── kpiStats (computed)  ──→ KpiCard × 4
  ├── filteredDevices       ──→ FilterTabs + usePagination
  └── pagedDevices          ──→ AppTable / DeviceCard
```

---

## 5. 验收汇总

| 功能编号 | 功能名称 | 验收项 | 通过 | 未验证 |
|:--:|------|:--:|:--:|:--:|
| F-01-01 | ADB 扫描 | 5 | | 5 |
| F-01-02 | WiFi 连接 | 6 | | 6 |
| F-02-01 | 统计概览（KPI 卡片） | 4 | | 4 |
| F-02-02 | 设备表格/卡片展示 | 5 | | 5 |
| F-02-03 | 设备锁定 | 5 | | 5 |
| F-02-04 | 设备释放 | 4 | | 4 |
| F-02-05 | 强制断开 | 4 | | 4 |
| F-03-01 | 加入排队 | 4 | | 4 |
| F-03-02 | 取消排队 | 4 | | 4 |
| **合计** | | **41** | **0** | **41** |

---

## 附录A：测试优先级

| 优先级 | 覆盖范围 | 验收时机 |
|:--:|------|------|
| P0 | F-01-01~F-02-04（连接/锁定/释放/KPI） | 每次 MR 前 |
| P1 | F-03-01~F-03-02（排队）、WiFi 连接 | 发版前 |
| P2 | 超时边界、并发锁定 | 大版本前 |

## 附录B：实施状态

| 功能 | 状态 |
|------|:--:|
| ADB 扫描 + USB 连接 | ✅ |
| WiFi 局域网连接 | ✅ |
| 统计概览（拍立得 KPI 卡片） | ✅ v5.0 新设计 |
| 设备锁定/释放/排队 | ✅ |
| 强制断开 | ✅ |
| Dual 视图（表格/卡片） | ✅ |
| FilterTabs 迁入 shared | ✅ v5.0 |
| 模块背景统一点阵纸纹 | ✅ v5.0 |
| 全宽布局（移除 1600px 限制） | ✅ v5.0 |
| 设备分组/标签 | 📋 |

## 附录C：已知问题与改进项

| 编号 | 问题 | 严重度 | 记录日期 |
|:--:|------|:--:|:--:|
| IMP-01 | 仪表盘任务结果卡片跳转设备管理页时，已完成任务 ID 不兼容（后端 `case_id` vs 前端 `client_task_id`），临时降级为跳转列表页 | 🟠 | 2026-07-25 |
| IMP-02 | 离线设备较多时（12+），表格以离线行为主，视觉上缺乏活力 | 🟢 | 2026-07-25 |
