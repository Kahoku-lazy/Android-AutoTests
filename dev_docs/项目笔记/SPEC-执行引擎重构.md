# SPEC — 执行引擎模块重构

> 基于 SPEC-模块重构规范.md，针对 test-runner 模块的逐阶段执行计划。
> 版本：v1.0 · 日期：2026-07-25

---

## 当前状态快照

```
frontend/src/modules/test-runner/
├── index.vue                         761 行 · 页面编排者（超标 261 行）
├── api.js                             30 行 · 数据层（5 端点，偏薄）
├── routes.js                          14 行
├── constants.js                      143 行 · L4 达标
├── composables/
│   ├── taskUtils.js                  165 行 · 任务工具函数
│   ├── useTaskWebSocket.js           319 行 · WS 连接管理（超标！模块内第二大文件）
│   ├── useDebouncedSave.js            36 行 · 任务保存防抖
│   └── useQueuePoller.js              63 行 · 排队轮询
└── components/
    ├── NewTaskDialog.vue              143 行 · 新建任务弹窗
    └── TaskDetail.vue                 781 行 · 任务详情页（超标 281 行）
```

**已完成的改进**（前期重构）：

| 改进 | 状态 |
|------|:--:|
| KPI 卡片替换为 shared KpiCard | ✅ |
| FilterTabs 替换为 shared FilterTabs | ✅ |
| useDebouncedSave 提取 | ✅ |
| useQueuePoller 提取 | ✅ |
| NewTaskDialog 子组件提取 | ✅ |
| catch(_){} 全部替换 | ✅ |

**当前问题**：

| 问题 | 严重度 | 说明 |
|------|:--:|------|
| 页面布局**单 section**，KPI 在工具栏下方 | 🟡 | 应拆为「统计概览」+「任务列表」双 section |
| index.vue 761 行 | 🟠 | 超标 261 行，模板仍有 ~110 行可拆 |
| useTaskWebSocket.js 319 行 | 🟠 | 超出 .py 400 行标准（.js 也应参照） |
| TaskDetail.vue 781 行 | 🟠 | 独立超标 |
| 跨模块 import case-manager api | 🟡 | 合规（api.js 白名单）但耦合度偏高 |
| 任务卡片/行可点击但无视觉反馈 | 🟡 | 应有 hover 青色高亮 |
| 视图切换按钮样式未使用模块主色 | 🟢 | 当前用 `var(--ink)` 而非 `var(--c-runner)` |

---

## 阶段 1：基础设施统一 — 已完成 ✅

- 背景点阵纸纹：全局 `style.css` 已修复，test-runner 自动受益
- 全局 max-width：已移除，test-runner 自动全宽

---

## 阶段 2：布局重构 — 双 Section 改造

### 现状

```
┌─────────────────────────────┐
│  WorkbenchHeader            │
├─────────────────────────────┤
│  搜索 + FilterTabs + 视图切换 + 新建按钮  │  ← 全部混在一行
│  KPI 卡片 × 4               │  ← 在工具栏下方
│  表格 / 卡片视图             │
└─────────────────────────────┘
```

### 目标

```
┌─────────────────────────────┐
│  WorkbenchHeader            │
├─────────────────────────────┤
│  Section 1: 统计概览         │
│  - section 标题 + 手绘下划线  │
│  - KPI 卡片 × 4              │
├─────────────────────────────┤
│  Section 2: 任务列表         │
│  - 搜索 + FilterTabs + 视图切换 + 计数 + 新建 │
│  - 表格 / 卡片视图            │
└─────────────────────────────┘
```

### 模板改动

```html
<div class="doc-body">
  <!-- 统计概览 -->
  <section class="doc-section runner-stats">
    <div class="doc-section__header">
      <h3 class="doc-section__title">统计概览 <span class="doc-tag">Overview</span></h3>
      <span class="doc-section__label">任务执行状态与进度总览</span>
    </div>
    <div class="kpi-row">
      <KpiCard :value="kpiStats.running" label="执行中" color="var(--c-ai)" shape="diamond" />
      <KpiCard :value="kpiStats.waiting" label="等待中" color="var(--c-dashboard)" shape="triangle" />
      <KpiCard :value="kpiStats.completed" label="已完成" color="var(--c-device)" shape="square" />
      <KpiCard :value="kpiStats.incomplete" label="失败/未完成" color="var(--c-runner)" shape="circle" />
    </div>
  </section>

  <!-- 任务列表 -->
  <section class="doc-section runner-tasks">
    <div class="runner-toolbar">
      <el-input v-model="searchQuery" placeholder="搜索..." />
      <FilterTabs :tabs="filterAppTabs" v-model="activeTab" />
      <div class="runner-toolbar__right">
        <div class="view-toggle">...</div>
        <span class="filter-count">{{ filteredTasks.length }} 任务</span>
        <el-button type="primary" @click="openNewTask">＋ 新建任务</el-button>
      </div>
    </div>
    <!-- 表格/卡片 -->
  </section>
</div>
```

---

## 阶段 3：KPI 卡片 — 已完成 ✅

已使用 shared KpiCard × 4，颜色与形状配置正确：

| 卡片 | 颜色 | 图形 |
|------|------|:--:|
| 执行中 | `var(--c-ai)` 柔粉 | ◆ 菱形 |
| 等待中 | `var(--c-dashboard)` 柠黄 | ▲ 三角 |
| 已完成 | `var(--c-device)` 薄荷绿 | ■ 方块 |
| 失败/未完成 | `var(--c-runner)` 桃粉 | ● 圆 |

---

## 阶段 4：模块颜色收束

### 检查

```bash
grep -rn "var(--c-workflow)\|var(--c-case)\|var(--c-device)" modules/test-runner/
```

### 修正

| 当前 | 应该 | 位置 |
|------|------|------|
| 视图切换按钮 `var(--ink)` | `var(--c-runner)` `#FFB5A7` | `.view-btn.active` |
| 表格卡片边框 `var(--ink)` | `var(--c-runner)` | `.table-card` |

### 目标 CSS

```css
/* 视图切换 — 使用模块主色 */
.view-toggle { border-color: var(--c-runner); }
.view-btn.active { background: var(--c-runner); color: #fff; }
.view-btn:hover:not(.active) { color: var(--c-runner); }

/* 表格卡片 — 使用模块主色 */
.table-card {
  border-color: var(--c-runner);
  box-shadow: 2px 3px 0 rgba(255,181,167,0.15);
}
```

---

## 阶段 5：任务行交互增强

### 5.1 表格行 hover 效果

```css
.device-table-wrapper :deep(.el-table tbody tr) {
  cursor: pointer;
  transition: background var(--app-duration-fast) var(--app-ease);
}
.device-table-wrapper :deep(.el-table tbody tr:hover) {
  background: rgba(255,181,167,0.08);  /* 模块色 8% 透明 */
}
```

### 5.2 卡片视图 hover 效果

```css
.task-card {
  cursor: pointer;
  transition: all var(--app-duration) var(--app-ease);
}
.task-card:hover {
  background: rgba(255,181,167,0.08);
  transform: translateY(-2px);
}
```

---

## 阶段 6：超大文件拆分

### 6.1 useTaskWebSocket.js (319 行)

**问题**：WebSocket 连接管理 + 消息处理 + 重连逻辑全部在一个文件。

**拆分方案**：

```
composables/
├── useTaskWebSocket.js         ~150 行 · 连接/断开/重连/生命周期
├── wsMessageHandlers.js        ~100 行 · 消息类型路由 + 各 handler
└── taskUtils.js                ~165 行 · 保持不变
```

### 6.2 TaskDetail.vue (781 行)

**问题**：详情页包含 4 个 Tab（日志/用例/步骤/错误）+ 头部元数据 + 操作栏。

**拆分方案**：

```
components/
├── TaskDetail.vue              ~350 行 · 编排者（头部 + Tab 容器）
├── TaskDetailHeader.vue         ~80 行 · 任务元数据条
├── TaskDetailLogs.vue           ~80 行 · 日志 Tab 内容
├── TaskDetailCases.vue         ~120 行 · 用例 Tab 内容
└── TaskDetailActions.vue        ~60 行 · 操作栏
```

### 6.3 index.vue (761 行 → ~580 行)

已完成双 section 拆分后，仍需处理：

- 表格列模板（`#cell-*`）可拆出 `components/TaskTableCells.vue`
- 卡片视图模板可拆出 `components/TaskCardView.vue`

---

## 阶段 7：跨模块 import 评估

| Import | 合规？ | 说明 |
|------|:--:|------|
| `case-manager/api/apiTesting.js` | ✅ | api.js 白名单，合规 |
| `case-manager/api/webAutomation.js` | ✅ | 同上 |

无违规。但如果未来 case-manager 改 api 签名，test-runner 会受影响。可考虑通过 shared 层间接引用。

---

## 阶段 8：PRD 更新

参照 PRD-00 格式更新 PRD-04-执行引擎.md：

1. §2 设计目录：完整文件树 + 架构特征
2. §3 核心功能：统计概览 + 任务列表 + 新建任务弹窗
3. §4 数据流：API → composable → 子组件分发
4. 附录：已知问题与改进项

---

## 执行顺序

```
1. 布局重构（双 section）        →  1h  ─ 最大视觉收益
2. 模块颜色收束                  →  0.5h ─ CSS 替换
3. 任务行交互增强                →  0.5h ─ hover 效果
4. useTaskWebSocket 拆分          →  2h  ─ 319→150 行
5. TaskDetail 拆分                →  3h  ─ 781→350 行
6. index.vue 表格/卡片模板拆出    →  2h  ─ 761→580 行
7. PRD 更新                      →  1h
                                ─────
                                 10h
```

## 验证

```bash
# 每阶段后
npx vite build --mode development

# 完成后
find modules/test-runner -name "*.vue" -o -name "*.js" | xargs wc -l | sort -rn
grep -rn "@/modules/" modules/test-runner/ | grep -v "api.js\|api/"
```
