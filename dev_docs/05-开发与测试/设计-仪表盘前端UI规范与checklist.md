# 仪表盘前端 UI 规范与 Checklist

> 版本 v1 · 2026-08-14
> 适用范围：`frontend/src/modules/dashboard/`（index.vue / DashboardView.logic.ts / api.ts / composables / components×4）及共享依赖（WorkbenchHeader / StatsCard / ActivityTimeline 等）
> 设计语言：Paper × Polaroid（纸艺拍立得 · 点阵纸底 · 手绘波浪线），与 Doodle Craft 同源
> 唯一真相源：`frontend/src/shared/styles/tokens.css`（令牌）、`frontend/DESIGN_SYSTEM.md`（设计系统）、`.claude/skills/doodle-craft/references/components.md`（组件像素级规格）

---

## 1. 组件归属

| 项 | 说明 |
|----|------|
| 模块位置 | `frontend/src/modules/dashboard/` —— 路由 `/dashboard`（routes.ts，meta title「总览」） |
| 页面骨架 | `index.vue`（薄组件，仅渲染）→ `DashboardView.logic.ts`（编排器，组合 composable + 展示配置） |
| 数据层 | `composables/useDashboardStats.ts`（四态状态机 + 响应映射）→ `api.ts`（仅 2 个 GET） |
| 业务组件 | `StatsCard`（方角涂鸦统计卡）、`TrendBarChart`（ECharts 趋势柱图）、`TaskResultPanel`（任务结果）、`ActivityTimeline`（最近动态） |
| 共享依赖 | `WorkbenchHeader`（页面顶栏）、`ErrorState` / `SkeletonCard`（三态）、`shared/icons`、`shared/animations`（countUpFormatted / staggerReveal）、`shared/constants/module-colors`、`shared/composables/useECharts`、`shared/types/dashboard` |
| 架构约束 | **dashboard 是纯聚合层**（architecture.md §四）：无自有数据表、**只读**——前端只允许 GET，禁止任何写操作入口 |

---

## 2. 字体规范

### 2.1 字体系列（只允许 2 种）

| 字体 | CSS 变量 | 用途 | 字重限制 |
|------|----------|------|---------|
| Cascadia Mono + 思源黑体（display） | `--app-font-display` | 页面标题（wb-header）、章节标题、KPI 数字、时间线标题、页脚 | 600–800 |
| Cascadia Mono + 思源黑体（正文） | `--app-font` | 其余全部（卡片标签/正文/按钮/时间线/空态） | 400–800 |

> ⚠️ ECharts 渲染在 Canvas，**不解析 CSS 变量**（frontend.md §4）：TrendBarChart 内字号/色值为字面量，改全局字体/色板时须同步 §3.2 对照表。

### 2.2 字号层级（设计系统最小 12px）

| 字号 | 写法 | 元素 |
|------|------|------|
| 26px | 字面量（WorkbenchHeader 既有值） | wb-header 页面标题 |
| 32px | `var(--app-size-2xl)` ✅ | KPI 数字（stats-card__stat strong） |
| 20px | `var(--app-size-lg)` ✅ | 章节标题（doc-section__title） |
| 16px | `var(--app-size-md)` ✅ | 时间线标题、summary-chip 数值 |
| 14px | `var(--app-size-sm)` ✅ | 页脚/任务行标题/时间线正文/空态 |
| 12px | `var(--app-size-xs)` ✅ | 统计卡标签、卡片 desc、doc-tag、时间戳、标签、按钮、chip |

> ⚠️ 低于 12px 的现有值见 §8 已知偏差：wb-header 副标题 11px（CSS）、ECharts 轴标签 10px / 图例 11px（画布）。

### 2.3 字重规则

| 元素 | 字重 |
|------|------|
| 页面/章节/KPI 标题 | 700 |
| 统计卡标签、进入按钮、chip 数值/图标、wb-header 操作按钮 | 800 |
| 任务行标题、页脚 | 700 |
| 辅助文字（desc/时间戳/副标题/任务统计） | 600 |
| 时间线 action | 600 |

---

## 3. 颜色规范

### 3.1 必须使用 token，禁止硬编码色值

| 用途 | Token | 值 |
|------|-------|-----|
| 描边 / 文字（主） | `var(--ink)` | #1e1e24 |
| 页面底色 / 点阵圆点 | `--doodle-bg` / `var(--app-paper-dot)` | #faf5ee / #d4cdc0 |
| 白纸卡底 | `var(--app-bg-card)` | #ffffff |
| 辅助文字 | `var(--app-ink-muted)` | #999 |
| 内部浅分割线（tag/任务行/时间线标签描边） | `var(--app-border-light)` | #e8ecf1 |
| 微妙底色（chip 图标底 / idle 态） | `var(--app-bg-subtle)` | #f8f6f2 |
| hover 荧光黄 | `var(--app-highlight)` | #FFE066 |
| 页脚胶带 | `var(--app-footer-yellow)` / `var(--app-footer-yellow-text)` | #FFE066 / #5a4e20 |
| 图钉（三阶） | `var(--app-pushpin-light/mid/dark)` | #e8e0d5 / #c0b8a8 / #a09080 |
| live 呼吸点 | `var(--app-live)` | #f87171 |
| 时间线圆点 | `var(--app-timeline-dot)` | #999 |
| 通过 / 失败块 | `var(--app-pass/-text)` / `var(--app-fail/-text)` | #C8F5D0/#1a5c2a / #FFE0DB/#7a1c1c |
| 状态色系列 | `var(--app-status-success/-danger/-warning-bg/-purple/-purple-bg)` | #6BCB77 / #FFB5A7 / #FFF9E0 / #C9B6F2 / #E8DDF8 |
| 图标底（teal/purple/orange） | `var(--app-icon-teal-bg/-purple-bg/-orange-bg)` | #D4F5F0 / #F0E8FF / #FFE8D0 |
| 阴影 | `var(--app-shadow-md)`（卡片）/ `--app-shadow-lg`（hover） | 2px 3px 0 / 3px 4px 0 扁平 |
| 统计卡线条/文字 | `--app-stat-line` / `--app-stat-text` / `--app-stat-line-soft` | #7a7874 / #5f5d59 / #9e9994 软灰系 |
| 统计卡 hover / 投影 | `--app-stat-hover` / `--app-stat-shadow(-hover)` | #f5eecf / rgba(122,120,116,.14) |
| 统计卡填充 7 色 | `--app-stat-sage/gray/rose/pale/deep/cream/dust` | #e6f0ea/#dedfdc/#f4e8e1/#f0f6e7/#cdd9d3/#fdf7ed/#d0c5c1 |

**白名单字面量**（沿用既有惯例，与 token 同值或装饰性）：

- `#fff`：wb-header 底、按钮底（WorkbenchHeader 共享组件）
- `#FFE066`：WorkbenchHeader 品牌块默认底 / 按钮 hover（= `--app-highlight` 同值）
- `#999`：wb-header 副标题（= `--app-ink-muted` 同值）
- 装饰 rgba：图钉投影 `rgba(0,0,0,0.08)`、统计卡排线笔触 `rgba(122,120,116,0.10)`/`rgba(255,255,255,0.55)`、图标 chip 底 `rgba(255,255,255,0.85)`、livePulse 扩散 `rgba(248,113,113,0.45)`（纹理/动效，Canvas/动效豁免）

### 3.2 卡片配色映射（StatsCard + ECharts 画布）

**StatsCard**：`color` prop（`sage`/`gray`/`rose`/`pale`/`deep`/`cream`/`dust`）→ 组件内 `STAT_FILLS` 映射 → `--app-stat-*` token → `--fill` CSS 变量注入填充带。`MODULE_COLORS` 已无消费方（ModuleNavigator 已删、统计卡已改 `STAT_FILLS`）——`module-colors.ts` 为孤儿常量，待清理。

仪表盘分配：在线设备 `sage`、活跃智能体 `gray`、运行中任务 `rose`（带呼吸点）、工作流 `pale`；用例：Android `deep`/Web `sage`/API `cream`/功能业务 `dust`；元素：Android `deep`/Web `sage`/API `cream`。PAGE_HEADER 图标渐变 `linear-gradient(135deg,#F4D35E,#f0c06a)`（柠黄系字面量）。

**ECharts 画布字面量 ↔ token 对照**（改 tokens.css 后必须同步 TrendBarChart.vue，frontend.md §4）：

| 画布字面量 | 对应 token |
|-----------|-----------|
| `#1e1e24`（图例文字） | `--ink` |
| `#e8ecf1`（x 轴线） | `--app-border-light` |
| `#f0ede8`（分割线） | `--app-border-lighter` |
| `#999`（轴标签） | `--app-ink-muted` |
| `#6BCB77`（成功柱） | `--c-device` |
| `#FFB5A7`（失败柱） | `--c-runner` |

### 3.3 时间线类型色

| 事件类型 | 圆点边框/内芯 |
|---------|--------------|
| `run`（测试执行） | `--app-status-purple` |
| `agent`（智能体更新） | `--c-dashboard` |
| 枚举外值 | 默认灰（`--app-timeline-dot` / `--app-ink-muted`） |

---

## 4. 风格语言（Paper × Polaroid）

| 风格元素 | 规格 | 应用处 |
|---------|------|--------|
| 统计卡（方角十字涂鸦） | 2.5px 软灰边 + **方角（无圆角）** + 四角十字交叉笔触 + 扁平投影 + 内嵌奶油色排线填充带（2px 直线描边、内容居中） | 三组统计卡片 |
| 拍立得卡片 | 2.5px ink 边 + 圆角 6px 10px + `--app-shadow-md` 扁平投影 + `::before` 图钉 | 趋势两卡、页脚 |
| 微旋转 | 趋势卡 -0.3°/+0.4°、标题 -0.5°、品牌块 -2° | 趋势卡/标题/品牌块 |
| hover 抬卡 | `translate(-1px,-1px)` + 阴影加深；进入按钮 hover 奶油黄 | 统计卡 |
| 点阵纸底 | radial-gradient 0.8px 圆点 / 14px 网格 / `--doodle-bg` | doc-page 全局 |
| 手绘波浪线 | 章节标题 `::after` SVG data URI（3px 高波浪路径，40px 周期重复） | 四个 doc-section 标题 |
| doc-tag | 英文小标签：12px/700、圆角 4px 8px、1.5px 浅边框 | 章节标题右侧 |
| 荧光黄 hover | 背景 `--app-highlight`、按下 `translate(1px,1px)` | wb-header 按钮 |
| live 呼吸点 | 8px 圆点 2px `--app-live` 边 + box-shadow 扩散动画 1.5s | 运行中任务卡片填充带右上角 |
| 页脚胶带条 | 黄底 + 2.5px ink 边 + 圆角 6px 10px + 700 | dashboard__footer |
| 时间线 | 16px 圆点（类型色边）+ 1.5px 虚线（repeating-linear-gradient 3/3）+ 类型色内芯 | ActivityTimeline |
| 状态 chip/图标 | 2px ink 边 + 状态色底（success/failed/partial/running/idle） | TaskResultPanel |
| 空态/错误态 | 居中文案（EmptyState / 行内空态），错误用共享 ErrorState + 重试 | 时间线/任务面板/整页 |
| 动效 | 入场 staggerReveal、数字 countUpFormatted、`prefers-reduced-motion` 降级（StatsCard 已实现） | 全局 |
| 禁止项 | ❌ 模糊阴影 ❌ 对称大圆角 ❌ 玻璃态（backdrop-filter）❌ 全屏 spinner | — |

---

## 5. 布局规格

| 区域 | 规格 |
|------|------|
| 页面骨架 | `wb-shell`：wb-header（96px，`flex-shrink:0`，2.5px ink 底边）+ `doc-body`（`flex:1; min-height:0; overflow-y:auto`，点阵底，padding 0 20px 20px） |
| 章节流 | 平台运营 → 测试用例 → 元素定位 → 趋势数据 → 最近动态 → 页脚，`gap: 18px` |
| 统计网格 | `repeat(auto-fill, 148px)` gap 14px —— 148px 方形卡（约 6 个中文字符宽），列数随窗口自动增减 |
| 趋势区 | `1.4fr 1fr` 双卡 gap 14px；**≤960px 断点** → 单列；卡片 body 内 `flex:1; min-height:0` |
| 任务列表 | `max-height: calc(68px × 4 + 6px × 3)` 内部滚动（`flex:1; min-height:0; overflow-y:auto`） |
| 时间线 | `flex:1; overflow-y:auto` 内部滚动，条目 padding-bottom 20px |
| 页脚 | 居中双列（最近更新 / 系统状态），gap 24px |
| 键盘可达 | StatsCard / task-row 均有 `role="button"` + `tabindex` + Enter/Space（div 可点击但带键盘角色，合规） |

---

## 6. 数据与协议（只读聚合）

| 项 | 说明 |
|----|------|
| 只读红线 | 前端仅 2 个 GET；**禁止新增任何写端点调用**（architecture.md §四） |
| 端点 1 | `GET /api/dashboard/stats/`（api.ts → djangoClient）↔ 后端 `apps/dashboard/urls.py` `dashboard/stats/` ✅ |
| 端点 2 | `GET /api/dashboard/activities/` ↔ `dashboard/activities/` ✅ |
| 信封 | `{status, data}`（DjangoResponse），stats 与 activities 独立解包，单侧失败不阻断另一侧（Promise.allSettled） |
| 字段映射 | snake_case → camelCase 统一在 `mapStatsResponse`（`type_breakdown`→`typeBreakdown`、`execution_summary`、`recent_tasks`、`last_updated`、`system_status`），组件不感知原始字段 |
| 三态 | loading（SkeletonCard 骨架）/ error（ErrorState + 重试）/ 空态（行内文案）；刷新独立 `refreshing` 态（按钮 loading，不清空已展示数据） |
| 数字动效 | 首入卡片 `countUpFormatted` 1200ms；值变更 800ms 补间 |

---

## 7. 前端 Checklist（改仪表盘必查）

### 7.1 字体

- [ ] 标题/KPI/页脚用 `--app-font-display`，正文用 `--app-font`，无第三字体
- [ ] CSS 字号全部走 `--app-size-*`（≥12px）；仅 wb-header 26px 为既有字面量
- [ ] 无新增 <12px 的 CSS 字号（§8 已知偏差收敛前不新增）
- [ ] 改字体后同步 TrendBarChart 画布字面量（ECharts 不解析 CSS 变量）

### 7.2 颜色

- [ ] 无新增硬编码 hex/rgba（grep `#[0-9a-fA-F]{3,8}` / `rgba(`，仅 §3.1 白名单）
- [ ] 改 tokens.css 色值后同步 §3.2 ECharts 对照表
- [ ] 新增统计卡配色走 `--app-stat-*` 并登记 `STAT_FILLS`，不新造渐变字面量
- [ ] 状态色走 `--app-status-*` / `--app-pass` / `--app-fail` 系列
- [ ] 统计卡颜色走 `--app-stat-*` token（色名 sage/gray/rose/pale/deep/cream/dust 已登记 `STAT_FILLS`）

### 7.3 风格

- [ ] 统计卡：方角（无圆角）+ 四角十字收角 + 2.5px 软灰边 + 扁平投影 + 内嵌填充带（直线描边、图标+标签居中）
- [ ] 拍立得卡（仅趋势区）：圆角 6px 10px + 图钉 + 微旋转，hover 荧光黄/抬卡
- [ ] 章节标题有手绘波浪线 ::after 与 doc-tag
- [ ] 无玻璃态 / 对称大圆角 / 全屏 spinner

### 7.4 布局与交互

- [ ] `doc-body` 滚动出口保持：`flex:1; min-height:0; overflow-y:auto`
- [ ] 960px 断点实测：趋势区单列；统计网格 auto-fill 各宽度无横向溢出
- [ ] 任务列表 4 行 max-height 内部滚动，超出可滚
- [ ] 可点击元素键盘可达（role/tabindex/Enter/Space）或为原生 button/a
- [ ] 三态完整：loading 骨架 / error 重试 / 空态文案
- [ ] `prefers-reduced-motion` 降级不回归
- [ ] **只读红线**：diff 中无任何写操作调用（POST/PUT/DELETE）

### 7.5 验证方式

- [ ] 浏览器实测（非仅看代码）：DevTools computed style 抽查字号/字体/颜色
- [ ] 缩窗验证两个断点 + ECharts resize 正常
- [ ] 数字滚动动效、时间线入场动效实测
- [ ] 检查测试未依赖被改样式（`grep -rn "stats-card\|timeline\|task-row\|doc-section" frontend/tests/`）

---

## 8. 已知偏差（待收敛，当前不阻塞）

| # | 位置 | 偏差 | 建议 |
|---|------|------|------|
| 1 | WorkbenchHeader `.brand-sub` 11px | CSS 字号 < 12px，违反 DESIGN_SYSTEM 最小字号（共享组件，非仅仪表盘） | 收敛为 `--app-size-xs` 12px |
| 2 | TrendBarChart 轴标签 10px / 图例 11px | 画布字面量 < 12px（canvas 豁免存争议） | 若严格执行最小字号 → 12px |
| 3 | TaskResultPanel `.task-row--clickable:hover` `rgba(78,205,196,0.12)` | 硬编码交互色（青绿 12%） | 换 `color-mix(in srgb, var(--c-case) 12%, transparent)`，零视觉变化 |
| 4 | WorkbenchHeader `#FFE066`/`#999`/`#fff` 字面量 | 与 token 同值未走变量（共享组件） | 与侧边栏终审同法收敛 |
| 5 | components.md 规格残留 10/11px（Button/Tag/筛选标签） | 设计系统文档与 tokens.md「最小 12px」冲突 | 文档层收敛，组件落地按 tokens |

---

## 9. 变更记录

| 日期 | 变更 |
|------|------|
| 2026-08-14 | 文档创建 v1：组件归属 / 字体 / 颜色 / 风格 / 布局 / 协议 / checklist / 已知偏差，全部基于现有代码实测值 |
| 2026-08-14 | 统计卡重绘（原型落地）：方角 + 四角十字收角、奶油低饱和排线填充带（`--app-stat-*` token）、数值/填充区居中、148px 紧凑方形网格；章节标题加主题图标（新增 IconMonitor/IconClipboardCheck）；恢复 trend/trendLabel 显示契约；StatsCard 双源配色问题随之消除 |
| 2026-08-14 | 文档同步终审：live 呼吸点硬编码 `#e09595` → `--app-live`；字号/字重表修正（统计卡标签归 12px/800）；白名单修正（去照片区白图标、补排线/chip rgba）；MODULE_COLORS 孤儿常量标注；荧光黄 hover 与 live 位置描述对齐实际代码 |
