# PRD-04 — 执行引擎 (Test Runner)

> 关联需求大纲：[`需求大纲.md`](./需求大纲.md) §5.4
> 版本：v7.1 · 日期：2026-07-27

---

## 1. 功能定位

执行引擎是任务调度与执行中枢。用户创建任务卡片、选择设备和用例、一键执行，通过 WebSocket 实时监控进度。页面由两个功能模块自上而下排列：统计概览 → 任务列表。

---

## 2. 设计目录

```
frontend/src/modules/test-runner/
├── index.vue                         808 行 · 页面编排者
├── api.js                             56 行 · 数据层（11 端点 + 跨模块封装）
├── routes.js                          14 行 · 路由定义
├── constants.js                      143 行 · L4 达标
├── composables/
│   ├── taskUtils.js                  165 行 · 任务工具函数（ID 生成/状态判定/进度计算）
│   ├── useTaskWebSocket.js           319 行 · WS 连接 + 消息处理 + 重连
│   ├── useDebouncedSave.js            43 行 · 任务保存防抖 + cleanup
│   └── useQueuePoller.js              63 行 · 排队轮询（依赖注入 getActiveRuns）
└── components/
    ├── NewTaskDialog.vue              143 行 · 新建任务弹窗（表单 + 设备/用例选择）
    └── TaskDetail.vue                 769 行 · 任务详情页（useExpandCollapse 接入）
```

**架构特征**：L4 全约束。四层分离，零裸调 API，跨模块 import 收敛到 api.js。shared FilterTabs/KpiCard/useExpandCollapse 接入完成。

---

## 3. 核心功能

### 3.1 统计概览（KpiCard × 4）

页面顶部 4 张拍立得风格卡片，展示任务状态分布。每张卡片包含：彩色几何图形 → 标签（加粗）→ 数字。微旋转排列，hover 归正放大。

| 卡片 | 颜色 | 图形 | 含义 |
|------|:--:|:--:|------|
| 执行中 | `var(--c-ai)` 柔粉 | ◆ 菱形 | `deriveTaskStatus === 'running'` |
| 等待中 | `var(--c-dashboard)` 柠黄 | ▲ 三角 | `isTaskQueued` 为 true |
| 已完成 | `var(--c-device)` 薄荷绿 | ■ 方块 | `taskBucket === 'completed'` |
| 失败/未完成 | `var(--c-runner)` 桃粉 | ● 圆 | `taskBucket === 'incomplete' \|\| status === 'idle'` |

**组件**：`shared/components/KpiCard.vue`

### 3.2 任务列表

筛选 + 操作工具栏 + 表格/卡片双视图。

#### 3.2.1 工具栏

| 元素 | 位置 | 功能 |
|------|------|------|
| 搜索框 | 左侧 | 按任务名称/ID/设备搜索 |
| FilterTabs（6 Tab） | 右侧 | 全部/⚡执行中/⏳等待中/✅已完成/⏹未完成/📝未执行 |
| 视图切换（📋表格/📷卡片） | 右侧 | 表格视图 vs 分组卡片视图 |
| 任务计数 | 右侧 | "N 任务" 实时数量 |
| ＋ 新建任务 | 右侧 | 打开 NewTaskDialog |

**组件**：`shared/components/FilterTabs.vue`

#### 3.2.2 表格视图

8 列数据表格，通过 `shared/components/AppTable.vue` 渲染：

| 列 | 渲染 | 说明 |
|------|------|------|
| 任务ID | 等宽字体 | `record.id`（如 ID-1） |
| 名称 | 加粗 | `record.name \|\| record.id` |
| 设备 | 📱 + 序列号 | `record.deviceSerial \|\| '—'` |
| 用例 | 数字 | `record.caseIds?.length` |
| 进度 | 迷你进度条 + 百分比 | 排队中显示"排队" |
| 状态 | 彩色标签 | 执行中/等待/完成/失败 各有对应颜色 |
| 时间 | 格式化 | `formatTime(record.createdAt)` |
| 操作 | 2×2 网格按钮 | 执行/重跑/报告/删除（非运行态）/ 停止（运行态）/ 取消排队（排队态） |

操作列按钮为 2×2 grid 布局，4 按钮时上下两行对齐；单按钮（停止/取消排队）占满整行。表格行 hover 淡桃粉底色（模块色 8% 透明）。

**交互**：点击任务行 → `openTaskDetail` → 跳转 `/runner/task/{id}` 详情页。

#### 3.2.3 卡片视图

按状态分 4 组展示（🟣 执行中 / 🟡 等待中 / 🟢 已完成 / 🔴 失败/未完成）。筛选为「全部」时四组同时显示。每张卡片包含：ID + 状态标签 → 名称 → 元数据行（设备/用例数/轮数）→ 进度条 → 统计行（完成数/总数/百分比/时间）→ 操作按钮。hover 上浮 2px + 阴影加深。

### 3.3 新建任务弹窗

表单弹窗，包含：任务名称 → 任务类型（UI/API/Web 三选一）→ 设备选择（仅 UI 类型）→ 用例多选（按类型过滤）→ 循环次数（1-10000）→ 轮间间隔（5-300 秒）→ 执行方式（立即/定时）。表单校验：名称必填、UI 类型必选设备、至少一个用例、间隔 ≥5 秒。

**组件**：`NewTaskDialog.vue`（已从 index.vue 拆出，143 行）

---

## 4. 数据流

```
本地状态 (ref)
  ├── tasks[]            任务列表（含本地创建的 ID-1/ID-2 等）
  ├── cases[]            用例定义（来自 API）
  └── devices[]          设备列表（来自 API）

composables
  ├── taskUtils           纯函数工具（状态判定/进度计算/ID 生成）
  ├── useDebouncedSave    变更防抖 → POST /runner/tasks/save
  ├── useQueuePoller      setInterval 轮询 /runner/active → 排队→执行
  └── useTaskWebSocket    WS 连接 /ws/test-run/{taskId} → 实时进度推送

index.vue
  ├── kpiStats (computed)   ──→ KpiCard × 4
  ├── filteredTasks          ──→ FilterTabs + searchQuery
  ├── groupedTasks           ──→ 卡片视图分组
  └── pagedDevices           ──→ AppTable（表格视图）
```

---

## 5. 验收汇总

| 功能编号 | 功能名称 | 验收项 | 通过 | 未验证 |
|:--:|------|:--:|:--:|:--:|
| F-01-01 | 创建任务 | 7 | | 7 |
| F-01-02 | 统计概览（KPI 卡片） | 4 | | 4 |
| F-01-03 | 任务列表与 Tab | 7 | | 7 |
| F-02-01 | 一键执行 | 5 | | 5 |
| F-02-02 | 实时进度 | 5 | | 5 |
| F-03-01 | 停止执行 | 5 | | 5 |
| F-03-02 | 重新执行 | 5 | | 5 |
| F-03-03 | 取消排队 | 4 | | 4 |
| **合计** | | **42** | **0** | **42** |

---

## 附录A：测试优先级

| 优先级 | 覆盖范围 | 验收时机 |
|:--:|------|------|
| P0 | F-01-01~F-03-01（创建+执行+停止+KPI） | 每次 MR 前 |
| P1 | F-03-02~F-03-03（重跑+取消排队） | 发版前 |
| P2 | 服务器重启恢复、定时执行 | 大版本前 |

## 附录B：实施状态

| 功能 | 状态 |
|------|:--:|
| 任务卡片 CRUD + 6 Tab | ✅ |
| 统计概览（拍立得 KPI 卡片） | ✅ v7.0 新设计 |
| 双 section 布局 + 手绘下划线标题 | ✅ v7.0 |
| 智能调度 + 排队 | ✅ |
| WebSocket 实时进度 | ✅ |
| 停止/重跑/取消排队 | ✅ |
| FilterTabs/KpiCard 接入 shared | ✅ v7.0 |
| 模块色桃粉统一 + 表格/卡片 hover 效果 | ✅ v7.0 |
| 操作按钮 2×2 网格布局 | ✅ v7.0 |
| 分层违规清零（裸 client 收敛到 api.js） | ✅ v7.1 |
| 跨模块 import 收敛（case-manager/api → api.js） | ✅ v7.1 |
| useExpandCollapse 接入（消除手写 Set-toggle） | ✅ v7.1 |
| useDebouncedSave.cleanup() 暴露（修复 _saveTimer 引用错） | ✅ v7.1 |
| 定时执行 (scheduled) | 📋 |
| 队列持久化（重启恢复） | ⚠️ 内存队列 |
| useTaskWebSocket 拆分 (319→150) | 📋 |
| TaskDetail 拆分 (769→350) | 📋 |

## 附录C：已知问题与改进项

| 编号 | 问题 | 严重度 | 记录日期 |
|:--:|------|:--:|:--:|
| IMP-01 | useTaskWebSocket.js 319 行超标，应拆出 wsMessageHandlers.js | 🟠 | 2026-07-25 |
| IMP-02 | TaskDetail.vue 769 行超标，4 个 Tab 内容可拆子组件 | 🟠 | 2026-07-25 |
| IMP-03 | 队列基于内存，服务重启后排队任务丢失 | 🟡 | 2026-07-16 |
| IMP-04 | 跨模块 import case-manager/api — **已修复 v7.1**：收敛到 test-runner/api.js | ✅ | 2026-07-27 |
