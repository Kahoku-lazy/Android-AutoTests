# PRD-01 — 仪表盘 (Dashboard)

> 关联模块：`apps/dashboard/` · 前端：`frontend/src/modules/dashboard/`
> 关联全局：[`需求大纲.md`](./需求大纲.md) §5.1
> 版本：v5.7 · 状态：评审中 · 日期：2026-08-21

**修订记录**

| 版本 | 日期 | 变更摘要 |
|------|------|----------|
| v5.7 | 2026-08-21 | AI 用量契约扩展：累计 token 前端以百万（M）、平均每对话 token 以千（K）展示；新增 DeepSeek 费用统计 `ai_usage.deepseek_cost`（官方价目可配置常量，高峰/空闲时段计费）；趋势数据新增 `charts.ai_tokens`（每日总 token + 缓存命中）与 `charts.deepseek_cost`（每日费用） |
| v5.6 | 2026-08-21 | 组件契约校正：StatsCard props 补 prefix/suffix/live；最近动态 agent 圆点色改为 --c-dashboard（原「主题状态黄色」令牌不存在） |
| v5.5 | 2026-08-19 | 设备口径统一（随 PRD-02 v6.2 两态化）：§4.1 在线/总数口径改「仅 ONLINE/BUSY 两态（离线即删），排除陈旧残留记录兜底」；§5.4 `offline`/`disconnected` 标注为 ⚠️ 兼容遗留字段（历史口径，通常为 0）；C-05 同步两态口径 |
| v5.4 | 2026-08-14 | 契约清理完成：v5.0 拍板批已实施（后端查询 34→27；前端删除新建用例系列/本周新建标签/"本周新增"文字/设备卡趋势装饰）；口径存档补 4 字段 |
| v5.3 | 2026-08-14 | 契约清理（已实施）：移除 10 个无前端消费字段（pass_rate 等），端点 3/4 保留；附已移除字段口径存档 |
| v5.2 | 2026-08-14 | 一致性校验修复：脉冲点颜色/卡片倾斜方向/数值字号与实现对齐；统一"汇总行"术语；补全智能体总数与任务执行记录总数口径；示例补齐 12 项约束 |
| v5.1 | 2026-08-14 | 移除「功能清单与用户故事」章节（产品决策：PRD 只保留功能规格） |
| v5.0 | 2026-08-13 | 按"只描述业务功能"重构：移除实现细节（文件行数/成熟度/实施状态/已知问题），补齐后端功能逻辑、API 接口、数据来源表、布局与视觉设计四章；**移除「新建用例」统计**（产品决策：趋势图与摘要只统计用例执行） |

---

## 1. 功能定位

仪表盘是平台首页聚合层。用户登录后一眼看到平台全局状态，并可一键跳转各模块。页面由五个区块自上而下排列：平台运营 → 测试用例 → 元素定位 → 趋势数据 → 最近动态。

**核心职责**：

- **统计** 平台运营指标：在线设备数、活跃智能体数、运行中任务数、工作流文件数
- **统计** 用例资产：安卓 / Web / API / 功能业务四类用例数量
- **统计** 元素资产：安卓 / Web / API 三类元素数量
- **统计** 任务执行结果：近 12 天执行成功 / 失败趋势 + 最近任务执行结果
- **展示** 跨模块最近动态
- **导航** 各卡片一键跳转对应模块

仪表盘是**纯只读聚合层**：无自有数据表，不提供任何写操作，所有操作入口均为跳转链接。

---

## 2. 功能详细规格

### 2.1 统计概览（F-01-01）

统计概览由页面五个纵向区块中的前三个组成（平台运营 → 测试用例 → 元素定位），共 11 张拍立得风格卡片。每个区块由区块标题 + 汇总行 + 卡片网格构成。数据加载中卡片显示骨架屏，数据到达后卡片数值触发数字滚动动画。

#### 2.1.1 平台运营（4 卡）

| 卡片 | 显示数据 | 含义 | 跳转 |
|------|------|------|------|
| 在线设备 | 在线设备数 | 可见设备中 ONLINE / BUSY 的数量（口径见 §4） | `/devices` |
| 活跃智能体 | 活跃智能体数 | 当前用户可见、状态为 active 的智能体数 | `/ai-assistant` |
| 运行中任务 | 运行中任务数 | 状态为 RUNNING 的任务数；>0 时显示红色脉冲点 | `/runner` |
| 工作流 | 工作流文件数 | 工作流工作台保存的文档总数 | `/workflow` |

区块汇总行展示四类汇总："设备 N · 智能体 N · 任务 N · 工作流 N"。

#### 2.1.2 测试用例（4 卡）

数据源 `stats.cases.breakdown[]`，按 `type` 拆分：

| 卡片 | 显示数据 | 含义 | 跳转 | type |
|------|------|------|------|------|
| Android 用例 | 用例数 | Android UI 自动化用例的总数 | `/cases` | `ui_automation` |
| Web 用例 | 用例数 | Web 自动化用例的总数 | `/cases` | `web_automation` |
| API 用例 | 用例数 | API 测试用例的总数 | `/cases` | `api_testing` |
| 功能业务 | 用例数 | 功能业务用例的总数 | `/cases` | `storage` |

所有卡片数字按当前用户可见性过滤（口径见 §4）。区块汇总行展示"共 N 个"（四类用例总数）。

#### 2.1.3 元素定位（3 卡）

数据源 `stats.elements.type_breakdown[]`，按 `type` 拆分：

| 卡片 | 显示数据 | 含义 | 跳转 | type |
|------|------|------|------|------|
| Android 元素 | 元素数 | Android 端已保存元素的总数 | `/elements` | `android` |
| Web 元素 | 元素数 | Web 端已保存元素的总数 | `/elements` | `web` |
| API 接口 | 接口数 | 已保存 API 接口的总数 | `/elements` | `api` |

区块汇总行展示"共 N 个 · N 个页面"。

**组件**：`StatsCard.vue`，props: label / value / prefix / suffix / color / path / loading / live（prefix/suffix 为数值前后缀；live 为右上角呼吸点，如「运行中任务」计数 >0 时置 true）。

#### 2.1.4 边界状态

| 场景 | 行为 |
|------|------|
| 数据加载中 | 每张卡片显示骨架屏 |
| 数据加载失败 | 页面顶部显示错误提示 + 重试按钮，点击重试重新加载全部数据 |
| 数据为空（新平台） | 各卡片显示 0，不显示空状态页 |

**验收标准**：

- 11 张卡片数字与后端返回字段一一对应，与对应模块页面查询结果一致
- 每张卡片可点击（含键盘 Enter/Space），跳转路径正确
- 首次加载显示骨架屏，数据到达后数字从 0 滚动到实际值（时长约 1.2s）
- 刷新按钮点击后按钮旋转，数据重新获取
- 接口失败时显示错误态，点击"重试"可恢复

### 2.2 任务执行结果（F-01-02）

左右并排布局：左侧趋势柱状图，右侧任务执行结果面板。

#### 2.2.1 趋势图

两系列分组柱状图，展示近 12 天（x 轴 `MM/DD`）执行趋势：

| 系列 | 柱子颜色 | 含义 |
|------|:--:|------|
| 执行成功 | `#6BCB77`（绿） | 当天执行结果为成功/通过的任务结果数 |
| 执行失败 | `#FFB5A7`（粉） | 当天执行结果为失败/异常的任务结果数 |

柱子顶部 2px 圆角、最大宽度 14px；两系列柱子依次错峰入场（延迟 40ms × 柱子序号，失败系列再 +60ms）；底部图例标注系列名称；hover 显示当天具体数值。

**组件**：`TrendBarChart.vue`，props: chart（`{ labels, success, failed }`）。ECharts Canvas 渲染，两色值为字面量（Canvas 不支持 CSS 变量，改色需改组件内常量，见约束 C-03）。

#### 2.2.2 任务执行结果面板

上方 2 个摘要标签 + 下方可滚动任务列表：

**摘要标签**：
- ✓ 成功（绿色边框，显示全部执行结果中成功的总数）
- ✗ 失败（红色边框，显示全部执行结果中失败的总数）

**任务列表**（最多 8 条），每行包含：
- 状态图标（✓ 全部通过 / ✗ 全部失败 / △ 部分失败 / ▶ 执行中 / ○ 未执行）
- 任务标题
- 用例图标行（每个用例一个小色块，颜色反映该用例执行结果）
- 统计文字（"成功 3 · 失败 1 · 共 4 次"，执行中任务不显示此行）
- 执行时间

列表最高显示 4 行，超出部分在面板内滚动。执行中任务行可点击，hover 时青色高亮，跳转到任务详情页 `/runner/task/{id}`；已完成任务跳转到 `/runner` 列表页。执行中状态图标带呼吸动画。

**组件**：`TaskResultPanel.vue`，props: tasks / summary。

#### 2.2.3 边界状态

| 场景 | 行为 |
|------|------|
| 无任何执行记录 | 面板显示空状态文案："暂无执行记录，前往执行引擎启动任务" |
| 有执行中任务 | 执行中任务排在列表最前，状态图标呼吸闪烁 |
| 超过 4 行 | 列表内部滚动，不撑高页面 |

**验收标准**：

- 趋势图仅含"执行成功 / 执行失败"两个系列，无"新建用例"系列
- 图表每日数值与执行记录逐日吻合
- 摘要标签仅含"成功 / 失败"两个，数值与全部执行结果统计一致
- 任务列表 = 执行中任务 + 最近执行记录，共不超过 8 条
- 执行中任务点击跳转详情页，已完成任务跳转执行引擎列表页

### 2.3 最近动态（F-01-03）

时间线样式的事件流，展示跨模块最近操作记录（最多 10 条，按时间倒序）。

| 字段 | 说明 | 示例 |
|------|------|------|
| action | 操作描述 | "智能体更新: 测试用例助手" |
| time | 发生时间 | "2026-07-24 22:20" |
| detail | 详细信息（可选） | "模型: dashscope/qwen-max" |
| tags | 标签数组（可选） | — |
| type | 事件类型 | run / agent |

事件类型与样式映射：

| type | 来源 | 圆点颜色（主题令牌） |
|------|------|------|
| `run` | 测试执行 | 主题状态紫色 |
| `agent` | 智能体更新 | 柠黄 `--c-dashboard`（#F7C948） |
| 枚举外值 | — | 默认灰色 |

时间线使用圆点 + 虚线连线连接各事件节点；数据更新时逐行渐入（每行间隔约 100ms）；空数据时显示"暂无活动记录"。

**组件**：`ActivityTimeline.vue`，props: items（`[{ action, time, detail, tags, type }]`）。

**验收标准**：

- 展示最近 10 条动态，按时间倒序
- 执行动态与智能体动态分别显示对应颜色圆点
- 空数据时显示"暂无活动记录"
- 数据更新时逐行动画入场

---

## 3. 布局与视觉设计

> 全部颜色/字号引用 Doodle Craft 主题令牌（[`frontend/AGENTS.md` §2](../../frontend/AGENTS.md)），本节只标令牌名；趋势图柱子 2 色为 Canvas 字面量例外（见约束 C-03）。

### 3.1 页面布局

```
┌─────────────────────────────────────────────┐
│ WorkbenchHeader（标题 + 刷新按钮）            │
├─────────────────────────────────────────────┤
│ ① 平台运营   汇总行 + 4 卡片                  │
│ ② 测试用例   汇总行 + 4 卡片                  │
│ ③ 元素定位   汇总行 + 3 卡片                  │
│ ④ 趋势数据   [趋势柱状图] [任务执行结果面板]   │
│ ⑤ 最近动态   时间线                           │
├─────────────────────────────────────────────┤
│ 页脚（最近更新时间 · 系统状态）               │
└─────────────────────────────────────────────┘
```

- 页面底色：米白纸纹（`--doodle-bg`），叠加圆点底纹（14px 网格点阵）
- 区块标题：展示字体、`--app-size-lg`、字重 700，下方手绘风格波浪下划线
- 趋势区左右分栏 1.4 : 1，窄屏（≤960px）变为上下单列
- 卡片网格 4 列，窄屏（≤520px）变为单列

### 3.2 卡片设计（拍立得风格）

| 属性 | 规格 |
|------|------|
| 形状 | 不规则圆角 `6px 10px 6px 10px`；墨色描边 2.5px（`--ink`）；投影 `--app-shadow-md` |
| 图钉 | 卡片顶部居中 9px 圆形图钉（渐变 token `--app-pushpin-*`） |
| 姿态 | 奇数卡逆时针倾斜 0.5°、偶数卡顺时针 0.5°；hover 归正并放大 1.03 |
| 照片区 | 卡片顶部 60px 高彩色区块，圆角 `3px 5px 3px 5px`，2px 墨边；底色 = 各模块主题色（见 §3.4） |
| 标题 | `--app-size-xs`、字重 700、居中 |
| 数值 | 展示字体（`--app-font-display`）、`--app-size-md`（紧凑网格覆盖后）、字重 700、墨色 |
| 进入按钮 | 圆角 `4px 8px 4px 8px`、2px 墨边、模块色渐变底；hover 高亮 |
| 动效 | 数值滚动：首次入场 1200ms、后续刷新 800ms；加载中显示骨架屏 |

无障碍：系统开启"减少动态效果"时禁用倾斜/缩放/滚动动画。

### 3.3 任务面板与时间线

| 元素 | 规格 |
|------|------|
| 摘要标签 | 圆角 `4px 8px 4px 8px`、2px 墨边；成功=绿色边框（`--app-status-success`）、失败=红色边框（`--app-status-danger`）；数值 `--app-size-md` 字重 800 |
| 任务行状态块 | 28px 方块，圆角 `4px 8px 4px 8px`、2px 墨边；成功绿（`--app-pass`）/ 失败粉（`--app-fail`）/ 部分失败黄 / 执行中紫（呼吸动画 1.5s）/ 未执行灰 |
| 任务行 hover | 背景青色高亮（rgba 主题青色 12%） |
| 用例小色块 | 20px 方块，圆角 `3px 6px 3px 6px`，颜色同任务状态色 |
| 运行中脉冲点 | 8px 圆点，2px 红边（`--app-live`），波纹脉冲 1.5s |
| 时间线圆点 | 16px 空心圆 + 6px 内点；圆点颜色按事件类型映射状态色（§2.3） |
| 时间线连线 | 虚线（点阵渐变）连接相邻事件 |
| 页脚 | 黄色底（`--app-footer-yellow`）、2.5px 墨边、圆角 `6px 10px 6px 10px`、展示字体 |

### 3.4 卡片配色（模块主题色）

| 卡片 | 主题色令牌 |
|------|------|
| 在线设备 / Android 用例 / Android 元素 | `app-green` |
| 活跃智能体 | `app-blue` |
| 运行中任务 / 功能业务用例 | `app-pink` |
| 工作流 | `purple` |
| Web 用例 / Web 元素 | `app-teal` |
| API 用例 / API 元素 | `app-yellow` |

---

## 4. 后端功能逻辑

仪表盘不存储自有数据，所有指标由后端聚合计算。各指标计算口径（业务规则）：

### 4.1 指标口径

| 模块类别 | 指标 | 计算口径 |
|------|------|----------|
| 平台运营/在线设备 | 在线设备数 | 设备仅 ONLINE / BUSY 两态（离线即删，见 PRD-02 §4.1）；统计 ONLINE + BUSY 为可见设备（统计时排除陈旧 OFFLINE / DISCONNECTED 残留记录兜底） |
| 平台运营/汇总行 | 设备总数 | 同上"可见设备"总数（不含 OFFLINE / DISCONNECTED 陈旧残留记录） |
| 平台运营/汇总行 | 智能体总数 | 当前用户可见的智能体总数（不受状态过滤） |
| 平台运营/汇总行 | 任务执行记录总数 | 任务执行记录总数（含运行中与已完成） |
| 平台运营/活跃智能体 | 活跃智能体数 | 当前用户可见的智能体中，状态为 active 的数量 |
| 平台运营/运行中任务 | 运行中任务数 | 任务执行记录中状态为 RUNNING 的数量 |
| 平台运营/工作流 | 工作流文件数 | 工作流工作台保存的文档总数 |
| 测试用例/4 卡片与汇总行 | 用例总数 / 各类用例数 | 四类用例表（Android / Web / API / 功能业务）分别计数，**按当前用户可见性过滤**（public 公开 / 本人创建 / restricted 且本人在白名单内） |
| 元素定位/3 卡片与汇总行 | 元素总数 / 各类元素数 | 安卓元素 + Web 元素 + API 接口三类分别计数；页面数 = 已保存页面总数 |
| 趋势数据/趋势图 | 执行趋势 | 近 12 天逐日统计执行结果：结果为 pass/passed 计入成功，fail/failed 计入失败；无数据的日期补 0 |
| 趋势数据/摘要标签 | 执行摘要 | 全部执行结果中成功总数、失败总数 |
| 趋势数据/任务列表 | 任务结果列表 | ① 当前执行中的任务（按启动时间排序）② 最近有执行活动的用例（最多 8 条）：取每用例最近一次执行往前 2 小时窗口内的成功/失败计数；状态派生规则：无成功无失败=未执行，有成功无失败=全部通过，无成功有失败=全部失败，两者皆有=部分失败 |
| 页脚 | 系统状态 | 无在线设备且存在可见设备 → `no_devices`（页脚显示"无设备连接"）；其余 → `normal`（显示"正常运行"） |
| 最近动态/时间线 | 最近动态 | 最近 5 条任务执行记录 + 最近 3 条智能体更新（均按当前用户可见），合并后按时间倒序取前 10 条 |

### 4.2 降级规则

| 场景 | 行为 |
|------|------|
| 某张数据表尚未创建 | 该指标计 0，不影响其他指标 |
| 执行中任务获取失败 | 跳过执行中任务部分，其余区块正常展示 |
| 任一区块数据缺失 | 页面其余区块照常展示，不整页失败 |

### 4.3 只读约束

仪表盘**只做跨模块只读查询，禁止任何写操作**（INSERT/UPDATE/DELETE）。所有指标的 ORM 查询均不修改数据。

---

## 5. API 接口功能

鉴权：全部端点需要 JWT Bearer 鉴权（公开路径除外）。响应统一 `{status, data}` / `{status, message}`。

### 5.1 端点总览

| # | 端点 | 功能 | 服务区块（对应 §2 功能点） |
|---|------|------|----------|
| 1 | `GET /api/dashboard/stats/` | 返回统计概览、任务执行结果、页脚状态所需的全部统计数据 | F-01-01 统计概览（平台运营 4 卡 · 测试用例 4 卡 · 元素定位 3 卡）；F-01-02 任务执行结果（趋势图 · 结果面板）；页脚（最近更新时间 · 系统状态） |
| 2 | `GET /api/dashboard/activities/` | 返回最近动态列表 | F-01-03 最近动态（时间线） |
| 3 | `GET /api/devices/stats/` | 设备池状态分布统计 | 无前端消费（已决策保留，见 5.6） |
| 4 | `GET /api/cases/stats/` | 用例启用/禁用分布统计 | 无前端消费（已决策保留，见 5.6） |

### 5.2 端点 1 — 统计总览

**接口地址**：`GET /api/dashboard/stats/`

**请求**：无参数。

**响应 data 字段**：

> 通用约束：所有计数字段（number）均为整数且 ≥0；来源数据表缺失时计 0（降级规则见 §4.2）。
> 字段分类：**业务** = 面向用户展示的业务数据；**技术** = 系统辅助字段（时间戳、状态标识）。

| 字段 | 类型 | 必填 | 约束 | 分类 | 说明 |
|------|------|:--:|------|:--:|------|
| `devices.online` | number | 是 | 整数 ≥0；`online ≤ total`；无可见设备时 = 0 | 业务 | 在线设备数 |
| `devices.total` | number | 是 | 整数 ≥0；无可见设备时 = 0 | 业务 | 可见设备总数 |
| `cases.total` | number | 是 | 整数 ≥0 | 业务 | 用例总数 |
| `cases.enabled` | number | 是 | 整数 ≥0；`enabled ≤ total` | 业务 | 用例启用数 |
| `cases.breakdown[]` | array | 是 | 恒 4 项、顺序固定；元素字段见子表① | 业务 | 四类用例计数 |
| `elements.total` | number | 是 | 整数 ≥0 | 业务 | 元素总数 |
| `elements.pages` | number | 是 | 整数 ≥0；空页面（0 个元素）也计入，与 `total` 无大小约束 | 业务 | 页面总数 |
| `elements.type_breakdown[]` | array | 是 | 恒 3 项、顺序固定；元素字段见子表② | 业务 | 三类元素计数 |
| `workflow.total` | number | 是 | 整数 ≥0 | 业务 | 工作流文档总数 |
| `runs.total` | number | 是 | 整数 ≥0 | 业务 | 任务执行记录总数 |
| `runs.active` | number | 是 | 整数 ≥0；`active ≤ total` | 业务 | 运行中任务数 |
| `agents.total` | number | 是 | 整数 ≥0 | 业务 | 当前用户可见智能体总数 |
| `agents.active` | number | 是 | 整数 ≥0；`active ≤ total` | 业务 | 活跃智能体数 |
| `ai_usage` | object | 是 | 内部字段见子表⑤ | 业务 | AI 用量聚合（今日/累计，含 DeepSeek 费用） |
| `charts.execution` | object | 是 | 内部字段见子表③ | 业务 | 执行趋势图数据 |
| `charts.ai_tokens` | object | 是 | 内部字段见子表⑥ | 业务 | 每日 token 用量趋势图数据 |
| `charts.deepseek_cost` | object | 是 | 内部字段见子表⑦ | 业务 | 每日 DeepSeek 费用趋势图数据 |
| `execution_summary.passed` | number | 是 | 整数 ≥0 | 业务 | 执行结果成功总数 |
| `execution_summary.failed` | number | 是 | 整数 ≥0 | 业务 | 执行结果失败总数 |
| `recent_tasks[]` | array | 是 | 长度 0~8；running 任务排在最前；元素字段见子表④ | 业务 | 任务结果列表 |
| `last_updated` | string | 是 | 固定 16 字符，格式 `YYYY-MM-DD HH:MM`；缺失时前端显示"暂无数据" | 技术 | 数据生成时间 |
| `system_status` | string | 是 | 枚举 `normal`/`no_devices`，≤16 字符；收到枚举外值按 `no_devices` 展示（显示"无设备连接"） | 技术 | 系统状态 |

**子表① `cases.breakdown[]` 元素字段**

| 字段 | 类型 | 必填 | 约束 | 说明 |
|------|------|:--:|------|------|
| `type` | string | 是 | 枚举 `ui_automation`/`web_automation`/`api_testing`/`storage`（≤15 字符）；不在枚举内视为异常数据，前端忽略该项 | 用例类型（卡片 type 匹配键） |
| `label` | string | 是 | 非空，≤20 字符 | 卡片显示名（Android/Web/API/功能业务） |
| `total` | number | 是 | 整数 ≥0 | 该类用例总数 |
| `enabled` | number | 是 | 整数 ≥0；`enabled ≤ total` | 该类用例启用数 |

**子表② `elements.type_breakdown[]` 元素字段**

| 字段 | 类型 | 必填 | 约束 | 说明 |
|------|------|:--:|------|------|
| `type` | string | 是 | 枚举 `android`/`web`/`api`（≤7 字符）；不在枚举内视为异常数据，前端忽略该项 | 元素类型（卡片 type 匹配键） |
| `label` | string | 是 | 非空，≤20 字符 | 卡片显示名（Android元素/Web元素/API接口） |
| `total` | number | 是 | 整数 ≥0 | 该类元素总数 |

**子表③ `charts.execution` 内部字段**

| 字段 | 类型 | 必填 | 约束 | 说明 |
|------|------|:--:|------|------|
| `labels[]` | array | 是 | 恒 12 项；每项为字符串，固定 5 字符，格式 `MM/DD` | x 轴日期（近 12 天，旧 → 新） |
| `success[]` | array | 是 | 恒 12 项；整数 ≥0；无数据日期补 0；禁止缺项或长度不足 | 每日执行成功数 |
| `failed[]` | array | 是 | 恒 12 项；整数 ≥0；无数据日期补 0；禁止缺项或长度不足 | 每日执行失败数 |

**子表④ `recent_tasks[]` 元素字段**

| 字段 | 类型 | 必填 | 约束 | 说明 |
|------|------|:--:|------|------|
| `id` | string/number | 是 | 非空；执行中任务为 run_id（string，≤200 字符），已完成任务为用例 id（number，正整数） | 任务标识 |
| `title` | string | 是 | 非空，≤500 字符（用例标题模型上限；执行中任务为"执行中 · 设备序列号"拼接） | 任务标题 |
| `status` | string | 是 | 枚举 `running`/`success`/`failed`/`partial`/`idle`；不在枚举内视为 `idle`（○ 未执行） | 执行状态 |
| `passed` | number | 是 | 整数 ≥0；running 时为 0 | 成功次数 |
| `failed` | number | 是 | 整数 ≥0；running 时为 0 | 失败次数 |
| `total` | number | 是 | 整数 ≥0；已完成任务 `total = passed + failed`；running 时为 0 | 总执行次数 |
| `time` | string | 是 | 固定 16 字符，格式 `YYYY-MM-DD HH:MM` | 执行时间 |
| `cases[]` | array | 是 | 长度 ≥1；元素含 `title`（string 必填，≤500 字符）、`status`（枚举同本表 status）、`passed`/`failed`（number 必填，≥0） | 用例明细（每项一个用例结果） |

**子表⑤ `ai_usage` 内部字段**（每个指标均为 `{today, total}` 对象，`today`=今日、`total`=累计，均 ≥0）

| 字段 | 类型 | 必填 | 约束 | 说明 |
|------|------|:--:|------|------|
| `conversation_count` | object | 是 | `today`/`total` 整数 ≥0 | 对话总数 |
| `input_tokens` | object | 是 | 整数 ≥0 | 输入 token 数 |
| `output_tokens` | object | 是 | 整数 ≥0 | 输出 token 数 |
| `total_tokens` | object | 是 | 整数 ≥0；`= input + output` | 总 token 数 |
| `cache_hit_tokens` | object | 是 | 整数 ≥0；`≤ input_tokens` | 缓存命中 token 数 |
| `cache_hit_rate` | object | 是 | 浮点 0~100，1 位小数；输入为 0 时 = 0 | 缓存命中率（%） |
| `avg_tokens_per_conversation` | object | 是 | 整数 ≥0；对话为 0 时 = 0 | 平均每对话 token（前端按 K 单位展示） |
| `deepseek_cost` | object | 是 | 浮点 ≥0，单位元；保留 4 位小数 | DeepSeek 模型累计/今日费用 |

**子表⑥ `charts.ai_tokens` 内部字段**

| 字段 | 类型 | 必填 | 约束 | 说明 |
|------|------|:--:|------|------|
| `labels[]` | array | 是 | 恒 12 项；每项字符串固定 5 字符，格式 `MM/DD` | x 轴日期（近 12 天，旧 → 新，与 execution 同桶） |
| `total_tokens[]` | array | 是 | 恒 12 项；整数 ≥0；无数据日期补 0 | 每日总 token 数（输入 + 输出） |
| `cache_tokens[]` | array | 是 | 恒 12 项；整数 ≥0；无数据日期补 0 | 每日缓存命中 token 数 |

**子表⑦ `charts.deepseek_cost` 内部字段**

| 字段 | 类型 | 必填 | 约束 | 说明 |
|------|------|:--:|------|------|
| `labels[]` | array | 是 | 恒 12 项；每项字符串固定 5 字符，格式 `MM/DD` | x 轴日期（近 12 天，旧 → 新） |
| `cost[]` | array | 是 | 恒 12 项；浮点 ≥0，单位元；保留 4 位小数；无数据日期补 0 | 每日 DeepSeek 费用 |

**响应示例**：

```json
{
  "status": true,
  "data": {
    "devices": { "online": 2, "total": 3 },
    "cases": {
      "total": 45,
      "enabled": 40,
      "breakdown": [
        { "type": "ui_automation", "label": "Android", "total": 20, "enabled": 18 },
        { "type": "web_automation", "label": "Web", "total": 10, "enabled": 9 },
        { "type": "api_testing", "label": "API", "total": 8, "enabled": 8 },
        { "type": "storage", "label": "功能业务", "total": 7, "enabled": 5 }
      ]
    },
    "elements": {
      "total": 120,
      "pages": 6,
      "type_breakdown": [
        { "type": "android", "label": "Android元素", "total": 80 },
        { "type": "web", "label": "Web元素", "total": 25 },
        { "type": "api", "label": "API接口", "total": 15 }
      ]
    },
    "workflow": { "total": 12 },
    "runs": { "total": 30, "active": 1 },
    "agents": { "total": 3, "active": 2 },
    "charts": {
      "execution": {
        "labels": ["08/02", "08/03", "08/04", "08/05", "08/06", "08/07", "08/08", "08/09", "08/10", "08/11", "08/12", "08/13"],
        "success": [0, 5, 3, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        "failed": [0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
      }
    },
    "execution_summary": { "passed": 210, "failed": 32 },
    "recent_tasks": [
      {
        "id": "run-20260813-001",
        "title": "执行中 · 设备 A",
        "status": "running",
        "passed": 0,
        "failed": 0,
        "total": 0,
        "time": "2026-08-13 09:30",
        "cases": [{ "title": "登录冒烟", "status": "running", "passed": 0, "failed": 0 }]
      }
    ],
    "last_updated": "2026-08-13 09:31",
    "system_status": "normal"
  }
}
```

### 5.3 端点 2 — 最近动态

**接口地址**：`GET /api/dashboard/activities/`

**请求**：无参数。

**响应 data 字段**：

| 字段 | 类型 | 必填 | 约束 | 分类 | 说明 |
|------|------|:--:|------|:--:|------|
| `data[]` | array | 是 | 长度 0~10；按 `time` 倒序 | 业务 | 最近动态列表 |

**data 元素字段**：

| 字段 | 类型 | 必填 | 约束 | 分类 | 说明 |
|------|------|:--:|------|:--:|------|
| `type` | string | 是 | 枚举 `run`/`agent`（≤5 字符）；不在枚举内按默认样式（灰）展示 | 业务 | 事件类型（run=测试执行，agent=智能体更新） |
| `action` | string | 是 | 非空，≤210 字符（"测试执行: " + run_id ≤200 / "智能体更新: " + 名称 ≤200） | 业务 | 操作描述 |
| `detail` | string | 否 | ≤240 字符（设备序列号 ≤200 拼接 / 模型名 ≤100 拼接） | 业务 | 详细信息 |
| `time` | string | 是 | 固定 16 字符，格式 `YYYY-MM-DD HH:MM`；当前实现执行记录可能透传 ISO 长格式（≤100 字符），实施时需归一化 | 技术 | 发生时间 |
| `tags` | array | 否 | 预留字段，当前后端不返回；若返回：每项 string 非空 ≤50 字符 | 业务 | 标签数组 |

**响应示例**：

```json
{
  "status": true,
  "data": [
    {
      "type": "run",
      "action": "测试执行: run-20260813-001",
      "detail": "设备: 设备A · 状态: RUNNING",
      "time": "2026-08-13 09:30"
    },
    {
      "type": "agent",
      "action": "智能体更新: 测试用例助手",
      "detail": "模型: dashscope/qwen-max",
      "time": "2026-08-12 22:20"
    }
  ]
}
```

### 5.4 端点 3 — 设备池统计

**接口地址**：`GET /api/devices/stats/`

**请求**：无参数。

**响应 data 字段**：

| 字段 | 类型 | 必填 | 约束 | 分类 | 说明 |
|------|------|:--:|------|:--:|------|
| `online` | number | 是 | 整数 ≥0；`busy ≤ online ≤ total` | 业务 | 在线设备数（可见设备中 ONLINE + BUSY） |
| `busy` | number | 是 | 整数 ≥0；`busy ≤ online` | 业务 | 忙碌设备数（BUSY） |
| `offline` | number | 是 | 整数 ≥0；与 `total` 无交集 | 业务 | ⚠️ 兼容遗留字段（离线设备数，OFFLINE）。设备已改为离线即删（PRD-02 v6.2），此字段通常为 0 或陈旧残留记录数 |
| `disconnected` | number | 是 | 整数 ≥0；与 `total` 无交集 | 业务 | ⚠️ 兼容遗留字段（断连设备数，DISCONNECTED），同 offline 为历史口径遗留 |
| `total` | number | 是 | 整数 ≥0；`offline + disconnected + total` 与全部设备记录数的差额为未归类状态设备 | 业务 | 可见设备总数（排除 OFFLINE / DISCONNECTED 陈旧残留） |

**响应示例**：

```json
{
  "status": true,
  "data": {
    "online": 2,
    "busy": 1,
    "offline": 3,
    "disconnected": 1,
    "total": 3
  }
}
```

### 5.5 端点 4 — 用例统计

**接口地址**：`GET /api/cases/stats/`

**请求**：无参数。

**响应 data 字段**：

| 字段 | 类型 | 必填 | 约束 | 分类 | 说明 |
|------|------|:--:|------|:--:|------|
| `total` | number | 是 | 整数 ≥0 | 业务 | 可见用例总数（4 类表合计） |
| `enabled` | number | 是 | 整数 ≥0；`enabled ≤ total` | 业务 | 用例启用数 |
| `disabled` | number | 是 | 整数 ≥0；`enabled + disabled = total` | 业务 | 用例禁用数 |

口径：4 类用例表合计，按当前用户可见性过滤（与端点 1 `cases` 字段口径一致）。

**响应示例**：

```json
{
  "status": true,
  "data": {
    "total": 45,
    "enabled": 40,
    "disabled": 5
  }
}
```

### 5.6 契约变更

| 版本 | 变更 | 内容 |
|------|------|------|
| v5.0 | 移除（v5.4 已实施） | `charts.execution.new_cases`、`execution_summary.new_cases_week`、`cases.trend`——产品决策：只统计用例执行 |
| v5.0 | 移除（v5.4 已实施） | `devices.trend`——原实现语义错误（后端传执行次数、前端按百分比展示） |
| v5.3 | 移除（已实施） | `pass_rate`、`charts.devices / charts.cases / charts.pass_rate`、`elements.breakdown`、`runs.trend`、`agents.trend`、`reports.total`、`workflow.page_flows / test_cases`——无前端消费，产品决策清理（2026-08-14） |
| v5.3 | 保留 | 端点 3/4（`/devices/stats/`、`/cases/stats/`，见 5.4、5.5）——产品决策保留（2026-08-14）：对外 API 面，零持有成本 |

**已移除字段口径存档**（重新启用时按此实现，无需考古代码）：

| 字段 | 计算口径 | 移除版本 |
|------|------|:--:|
| `pass_rate` | 全部执行结果中 pass/passed 占比，四舍五入 1 位小数；总数为 0 时 = 0 | v5.3 |
| `charts.devices` | 近 12 天每日执行结果数（TestResult.created_at 按天分组零填充）；全为 0 时返回 `[1]*12` 兜底 | v5.3 |
| `charts.cases` | 近 12 天每日新建 Android 用例数（TestDefinition.created_at）；同样带 `[1]*12` 兜底 | v5.3 |
| `charts.pass_rate` | 近 12 天每日通过率（当日 pass/passed ÷ 当日全部执行结果 ×100，1 位小数）；当日无数 = 0；全为 0 时返回 `[0]*12` | v5.3 |
| `elements.breakdown` | 全部页面按元素数降序：`{page_name, package, element_count, page_id}`；原 `elements.pages` 取该列表长度，移除后改为直接计数 el_pages | v5.3 |
| `runs.trend` | = `runs.total`（全部执行记录数） | v5.3 |
| `agents.trend` | = `agents.active`（活跃智能体数） | v5.3 |
| `reports.total` | rg_reports 表记录总数（移除后仪表盘不再读取 rg_reports） | v5.3 |
| `workflow.page_flows` | wf_documents 中 doc_type=page_flow 的文档数 | v5.3 |
| `workflow.test_cases` | wf_documents 中 doc_type=test_case 的文档数 | v5.3 |
| `charts.execution.new_cases` | 近 12 天每日新建 Android 用例数（TestDefinition.created_at 自然日分组零填充，与执行成功/失败同桶） | v5.4 |
| `execution_summary.new_cases_week` | 滚动 7 天新建用例总数（4 类用例表合计，按可见性过滤）；与 `cases.trend` 同值 | v5.4 |
| `cases.trend` | = 上述 7 天新建总数；前端曾显示为"本周新增" | v5.4 |
| `devices.trend` | 滚动 7 天执行结果总数（TestResult.created_at ≥ 7 天前）；前端曾将其当百分比展示（语义错位，v5.0 拍板移除） | v5.4 |

---

## 6. 数据来源表

仪表盘无自有数据表，以下为只读数据来源声明（表结构定义见各所属模块 PRD）：

| 来源表 | 表前缀 | 所属模块 | 读取用途 |
|------|:--:|------|------|
| `dp_devices` | dp_ | 设备管理 | 在线设备数、设备总数、系统状态判定 |
| `ai_agents` | ai_ | AI 助手 | 智能体总数、活跃数、最近动态 |
| `cm_test_definitions` | cm_ | 用例管理 | Android 用例计数 |
| `cm_web_testcases` | cm_ | 用例管理 | Web 用例计数 |
| `cm_api_testcases` | cm_ | 用例管理 | API 用例计数 |
| `cm_storage_testcases` | cm_ | 用例管理 | 功能业务用例计数 |
| `el_elements` | el_ | 元素定位 | Android 元素计数 |
| `el_web_elements` | el_ | 元素定位 | Web 元素计数 |
| `el_api_endpoints` | el_ | 元素定位 | API 接口计数 |
| `el_pages` | el_ | 元素定位 | 页面总数 |
| `tr_test_results` | tr_ | 执行引擎 | 执行趋势、执行摘要、任务结果列表 |
| `tr_test_runs` | tr_ | 执行引擎 | 运行中任务数、最近动态 |
| `wf_documents` | wf_ | 工作流工作台 | 工作流文件数 |

**只读声明**：以上全部为 SELECT 查询，无任何写操作；跨模块读取符合防火墙 #2（读放开，写收敛）。

---

## 7. 非功能需求

| 类别 | 指标 | 目标值 |
|------|------|:--:|
| 性能 | 统计接口响应时间 | ≤1s（普通数据量） |
| 容量 | 单页数据上限 | 卡片 11 张、任务行 8 条、动态 10 条 |
| 可靠性 | 部分数据缺失时页面可用性 | 任一区块失败不影响其余区块展示 |
| 兼容性 | 窄屏适配 | ≤960px 趋势区单列；≤520px 卡片单列 |
| 无障碍 | 减少动态效果 | 支持 `prefers-reduced-motion` |
| 刷新 | 数据更新方式 | 首次加载 + 手动刷新按钮（自动刷新待评审） |

---

## 8. 非目标（Non-goals）

| 不做的功能 | 原因 | 归属 |
|------|------|------|
| 任何写操作（创建/编辑/删除/执行） | 聚合层只读，写操作在各业务模块完成 | — |
| 仪表盘内嵌操作控件 | 所有操作入口为跳转链接，不内嵌写功能 | — |
| 数据导出（CSV/PDF） | 报告模块已有导出能力 | 测试报告模块 |
| 统计详情钻取（点击卡片携带筛选参数） | 保持首页轻量，卡片只跳模块首页 | — |
| 自动刷新轮询 | 待评审，当前仅手动刷新 | 开放问题 |

---

## 9. 关键约束速查

| 编号 | 约束 | 实施位置 |
|------|------|------|
| C-01 | 仪表盘只读：禁止 ORM 写操作 | `apps/dashboard/views.py` |
| C-02 | 用例/智能体计数必须按当前用户可见性过滤 | 统计接口实现 |
| C-03 | 颜色/字号全部引用 Doodle Craft 主题令牌；趋势图柱子 2 色为 Canvas 字面量例外（改色需改组件常量并同步本 PRD §2.2.1） | `DashboardView.style.css`、`TrendBarChart.vue` |
| C-04 | 响应统一 `{status, data}` / `{status, message}`，JSON 字段 snake_case | 全部端点 |
| C-05 | 设备口径：仅 ONLINE / BUSY 两态（离线即删），统计排除陈旧 OFFLINE / DISCONNECTED 残留记录，与设备管理页一致 | 统计接口实现 |
| C-06 | 动态事件 type 枚举：run / agent，前端样式与枚举同步 | 动态接口 + `ActivityTimeline.vue` |

---

## 10. 相关文件索引

| 层 | 文件 | 说明 |
|------|------|------|
| 前端 | `frontend/src/modules/dashboard/index.vue` | 页面编排 |
| 前端 | `frontend/src/modules/dashboard/DashboardView.logic.ts` | 卡片配置 / 数据映射 |
| 前端 | `frontend/src/modules/dashboard/DashboardView.style.css` | 页面样式（拍立得主题） |
| 前端 | `frontend/src/modules/dashboard/composables/useDashboardStats.ts` | 数据获取与状态管理 |
| 前端 | `frontend/src/modules/dashboard/components/StatsCard.vue` | 统计卡片 |
| 前端 | `frontend/src/modules/dashboard/components/TrendBarChart.vue` | 趋势柱状图 |
| 前端 | `frontend/src/modules/dashboard/components/TaskResultPanel.vue` | 任务执行结果面板 |
| 前端 | `frontend/src/modules/dashboard/components/ActivityTimeline.vue` | 活动时间线 |
| 前端 | `frontend/src/modules/dashboard/api.ts` | 数据层（2 端点） |
| 前端 | `frontend/src/shared/types/dashboard.ts` | 前端类型契约 |
| 前端 | `frontend/AGENTS.md` §2 + `tokens.css` | Doodle Craft 主题令牌 |
| 后端 | `apps/dashboard/views.py` | 4 个统计端点实现 |
| 后端 | `apps/dashboard/urls.py` | 路由注册 |

---

## 附录A：功能边界规则

| 边界 | 规则 |
|------|------|
| 我能做什么 | 查看全局统计、浏览最近动态、一键跳转各模块、手动刷新数据 |
| 我不能做什么 | 任何写操作：创建设备、创建用例、启动任务、修改配置等 |
| 如需越界 | 一律以跳转链接引导到对应业务模块页面完成操作（如"进入执行引擎启动任务"） |
| 数据可见性 | 用例、智能体、动态等计数均按当前登录用户可见范围过滤 |
