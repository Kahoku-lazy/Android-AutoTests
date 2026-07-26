# PRD-00 — 仪表盘 (Dashboard)

> 关联需求大纲：[`需求大纲.md`](./需求大纲.md) §5.8
> 版本：v4.0 · 日期：2026-07-25

---

## 1. 功能定位

仪表盘是首页聚合层。用户登录后一眼看到平台全局状态和快捷入口。页面由四个功能模块自上而下排列：统计概览 → 趋势数据 → 模块入口 → 最近动态。

---

## 2. 设计目录

```
frontend/src/modules/dashboard/
├── index.vue                         401 行 · 页面编排者
├── api.js                             12 行 · 数据层（2 端点）
├── routes.js                           8 行 · 路由定义
├── composables/
│   └── useDashboardStats.js          150 行 · 逻辑层
│        ├── loadData()      首次加载（loading 态 → 骨架屏）
│        ├── refreshData()   手动刷新（refreshing 态 → 按钮旋转）
│        └── mapStatsResponse()  后端 JSON → 前端结构 + ?? 默认值
└── components/
    ├── StatsCard.vue                  255 行 · KPI 统计卡片
    ├── TrendBarChart.vue               72 行 · 趋势柱状图
    ├── TaskResultPanel.vue            185 行 · 任务执行结果
    ├── ModuleNavigator.vue            239 行 · 8 模块入口
    └── ActivityTimeline.vue           182 行 · 活动时间线
```

**架构特征**：L3 成熟度，四层分离，零裸调 API，零跨模块 import。

---

## 3. 功能模块

### 3.1 统计概览

页面顶部 4 张拍立得风格卡片，展示平台核心指标。首次加载显示骨架屏（`SkeletonCard`），数据到达后触发 `countUpFormatted` 数字滚动动画。每张卡片可点击，跳转到对应模块。

#### 卡片 1：在线设备

| 项目 | 内容 |
|------|------|
| 显示数据 | `stats.devices.online / stats.devices.total`（如 `3 / 5`） |
| 辅助文字 | "ADB 扫描 · 连接锁定 · 排队调度" |
| 趋势 | ↑↓ + 百分比 + "近期活跃"（如 `↑12% 近期活跃`） |
| 跳转 | 点击 → `/devices`（设备管理页） |
| 图标 | 手机图标，绿色渐变背景 |
| 组件 | `StatsCard.vue`，props: value / label / desc / color / trend / path |

#### 卡片 2：测试用例

| 项目 | 内容 |
|------|------|
| 显示数据 | `stats.cases.total`（如 `11`） |
| 辅助文字 | "步骤编排 · 目录树 · YAML 导入导出" |
| 趋势 | ↑↓ + 百分比 + "本周新增" |
| 跳转 | 点击 → `/cases`（用例管理页） |
| 图标 | 文件代码图标，青绿渐变背景 |

#### 卡片 3：活跃智能体

| 项目 | 内容 |
|------|------|
| 显示数据 | `stats.agents.active`（如 `3`） |
| 辅助文字 | "自然语言驱动 · SSE 流式 · 知识库" |
| 趋势 | ↑↓ + 百分比 + "智能体"（如 `↑3% 智能体`） |
| 跳转 | 点击 → `/ai-assistant`（AI 助手页） |
| 图标 | 大脑图标，蓝紫渐变背景 |

#### 卡片 4：运行中任务

| 项目 | 内容 |
|------|------|
| 显示数据 | `stats.runs.active`（如 `0`） |
| 辅助文字 | "任务调度 · 实时进度 · WebSocket 日志" |
| 趋势 | ↑↓ + 百分比 + "执行中" |
| 跳转 | 点击 → `/runner`（执行引擎页） |
| 图标 | 播放按钮图标，粉红渐变背景 + 绿色脉冲点（任务 >0 时显示） |

---

### 3.2 趋势数据

左右并排布局：左侧 ECharts 柱状图，右侧任务执行结果面板。

#### 3.2.1 趋势图

三系列分组柱状图，展示近 12 期执行趋势：

| 系列 | 柱子颜色 | 含义 |
|------|:--:|------|
| 执行成功 | `#6BCB77`（绿） | 成功完成的任务数 |
| 执行失败 | `#FFB5A7`（粉） | 失败/异常的任务数 |
| 新建用例 | `#C9B6F2`（紫） | 本周新建的用例数 |

每条柱子有交错动画延时（延迟 0ms / 60ms / 120ms 依次出现），底部图例标注系列名称。hover 显示具体数值。

**组件**：`TrendBarChart.vue`，Canvas 渲染，颜色硬编码（不支持 CSS 变量），使用 `shared/composables/useECharts.js` 管理 ECharts 实例生命周期。

#### 3.2.2 任务执行结果

上方 3 个摘要标签 + 下方可滚动任务列表（最高 4 行）：

**摘要标签**：
- ✓ 成功（绿色边框，显示 `summary.passed`）
- ✗ 失败（红色边框，显示 `summary.failed`）
- + 本周新建（紫色边框，显示 `summary.new_cases_week`）

**任务列表**，每行包含：
- 状态图标（✓ 全部通过 / ✗ 全部失败 / △ 部分失败 / ▶ 执行中 / ○ 未执行）
- 任务标题
- 用例图标行（每个用例一个小色块，颜色反映执行结果）
- 统计文字（"成功 3 · 失败 1 · 共 4 次"）
- 执行时间

执行中任务行可点击，hover 时青色高亮，跳转到任务详情页 `/runner/task/{id}`。已完成任务跳转到 `/runner` 列表页。执行中状态图标带 pulse 呼吸动画。

**组件**：`TaskResultPanel.vue`，props: tasks / summary。

---

### 3.3 模块入口

8 张纸艺风格卡片，覆盖全平台模块。页面加载时 `staggerReveal` 交错入场动画（每张卡片 70ms 间隔）。

| 卡片 | 显示统计 | 跳转路径 | 图标 | 配色 |
|------|------|------|------|------|
| 仪表盘 | 8 个快捷入口 | `/dashboard` | layout-dashboard | 柠黄 |
| 设备管理 | 在线数 / 总数 | `/devices` | smartphone | 薄荷绿 |
| 元素定位 | 元素总数 | `/elements` | crosshair | 薰衣草紫 |
| 用例管理 | 用例总数 | `/cases` | layers | 青绿 |
| 执行引擎 | 运行中 / 总数 | `/runner` | play-circle | 桃粉 |
| 测试报告 | 报告总数 | `/reports` | file-bar-chart | 灰紫 |
| AI 助手 | 智能体总数 | `/ai-assistant` | bot | 柔粉 |
| 工作流工作台 | Demo | `/workflow` | git-branch | 天蓝 |

每张卡片布局：渐变色图标（左上）→ 模块名称 → 功能描述 → 统计数字 + "进入 →" 按钮。hover 时卡片下压（translate(1px,1px)）。配色取自 `shared/constants/module-colors.js`。

**组件**：`ModuleNavigator.vue`，props: stats。仪表盘专属，不进入 shared。

---

### 3.4 最近动态

时间线样式的事件流，展示跨模块最近操作记录。

| 字段 | 说明 | 示例 |
|------|------|------|
| action | 操作描述 | "智能体更新: 测试用例助手" |
| time | 发生时间 | "2026-07-24 22:20" |
| detail | 详细信息（可选） | "模型: dashscope/qwen-max" |
| tags | 标签数组（可选） | — |
| type | 事件类型 | success / warning / error / info |

时间线使用圆点 + 虚线连线连接各事件节点。三种状态颜色区分事件类型：绿色（success）、黄色（warning）、红色（error）、灰色（info）。空数据时显示"暂无活动记录"。数据更新时触发 `staggerReveal` 逐行动画。

**组件**：`ActivityTimeline.vue`，props: items（`[{ action, time, detail, tags, type }]`）。

---

## 4. 数据流

```
GET /dashboard/stats/      → 统计卡片 + 趋势图 + 任务结果
GET /dashboard/activities/ → 最近动态列表

useDashboardStats.js (composable)
  ├── loadData()        首次加载 → loading 态 → 骨架屏
  ├── refreshData()     手动刷新 → refreshing 态 → 按钮旋转
  └── mapStatsResponse() 后端 JSON → 前端结构（全字段 ?? 默认值）

index.vue (页面编排者)
  ├── stats.devices  ──→ StatsCard（在线设备）
  ├── stats.cases    ──→ StatsCard（测试用例）
  ├── stats.agents   ──→ StatsCard（活跃智能体）
  ├── stats.runs     ──→ StatsCard（运行中任务）
  ├── stats          ──→ ModuleNavigator（8 模块入口）
  ├── executionChart ──→ TrendBarChart（趋势图）
  ├── recentTasks    ──→ TaskResultPanel（任务结果）
  └── activities     ──→ ActivityTimeline（最近动态）
```

---

## 5. 验收汇总

| 功能编号 | 功能名称 | 验收项 | 通过 | 未验证 |
|:--:|------|:--:|:--:|:--:|
| F-01-01 | 统计概览（4 卡片） | 5 | | 5 |
| F-01-02 | 趋势数据（图表 + 任务结果） | 4 | | 4 |
| F-02-01 | 模块入口（8 卡片） | 6 | | 6 |
| F-02-02 | 最近动态（时间线） | 4 | | 4 |
| **合计** | | **19** | **0** | **19** |

---

## 附录A：测试优先级

| 优先级 | 覆盖范围 | 验收时机 |
|:--:|------|------|
| P0 | F-01-01~F-02-01（统计+趋势+入口） | 每次 MR 前 |
| P1 | F-02-02（最近动态） | 发版前 |

## 附录B：实施状态

全部功能已实现 ✅

## 附录C：已知问题与改进项

| 编号 | 问题 | 严重度 | 记录日期 |
|:--:|------|:--:|:--:|
| IMP-01 | 仪表盘缺少自动刷新。页面仅在 `onMounted` 和手动点击"刷新"按钮时更新数据，无 `setInterval` 轮询/WebSocket/`onActivated` | 🟡 | 2026-07-25 |
| IMP-02 | 任务结果卡片跳转：已完成任务使用 `case_id` 而非 `client_task_id`，临时降级为跳转 `/runner` | 🟠 | 2026-07-25 |
| IMP-03 | 大屏（>1600px）留白过大，已通过 `max-width: none` 修复 | 🟢 | 2026-07-25 |
