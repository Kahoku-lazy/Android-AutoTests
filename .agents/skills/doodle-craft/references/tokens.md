# Doodle Craft 视觉皮肤层 — 全局主题变量使用指南

> **令牌值的唯一真相源是 `frontend/src/shared/styles/tokens.css`（下称 T0）**，本文件只是它的检索表与用法口径。
> 改值流程：先改 T0 → 再同步本文件；两者冲突时**以 T0 为准**（本文件为 2026-09-23 对齐代码后的版本）。
> 命名分层：T0 原子（`--color-*` / `--font-*` / `--space-*` / `--radius-*` / `--shadow-*`）→ 兼容别名（`--app-*`，= `var(原子)`）→ 通用组件令牌（`--comp-*`）→ 模块令牌（T1，落 `modules/<模块>/tokens.css`）。
> 相邻参考：组件级规格（哪个组件用了哪些令牌、哪些维度没覆盖）见 [components/](components/)；页面层骨架与滚动见 [page-layout.md](page-layout.md)；别照抄的清单见 [known-gaps.md](known-gaps.md)。

## 1.1 核心色（纸面三原色 + 背景/边框/文字）

| CSS 变量 | 实际值 | 来源原子 | 用途 |
|----------|--------|----------|------|
| `--ink` | `#1e1e24` | `--color-indigo-13` | 正文、标题、图标、**实色描边** |
| `--paper` | `#fffef5` | `--color-lime-94` | L0 纸面底色：页面背景、侧栏、**页头底色** |
| `--dot` | `#d8d2c4` | `--color-orange-76` | 暖灰点/纹理色（纸面本身**不画点阵**，见 1.16）|
| `--app-bg-card` | `#ffffff` | `--color-white` | 卡片/纸张面（唯一的"白"）|
| `--app-bg-input` | `#ffffff` | `--color-white` | 输入框底色 |
| `--app-bg-subtle` | `#fffef5` | `--color-lime-94` | 表头、浅底块（与纸面同值，靠描边走层次）|
| `--app-border-light` | `#ffffff` | `--color-white` | **只作占位**，禁止当可见边框色（见 1.16）|
| `--app-border-lighter` | `#fffef5` | `--color-lime-94` | 同上 |
| `--app-highlight` | `#fcdc6b` | `--color-yellow-70` | hover 高亮底（default 按钮 hover、下拉项 hover）|
| `--app-text` | = `--ink` | — | 正文文字 |
| `--app-text-secondary` | `#96918c` | `--color-ink-57` | 辅助文字、占位符、禁用态 |
| `--app-text-muted` | `#c9cacc` | `--color-ink-79` | 更弱的次要文字 |
| `--app-nav-text` | `#5d5950` | `--color-ink-34` | 暖灰次级文字（实际消费点：设备管理卡片/工具栏、AI 工具箱）。⚠️ 侧栏导航未激活文字实际取 `--ink`，不是这个令牌 |
| `--app-stat-text` | `#5d5950` | `--color-ink-34` | 统计卡主文字 |
| `--app-marker-red` | `#f56b6a` | `--color-red-69` | 马克笔红：**仅**危险 CTA（侧栏退出）|

## 1.2 8 模块色

| 模块 | CSS 变量 | 色值 |
|------|----------|------|
| dashboard | `--c-dashboard` | `#F7C948` |
| device-pool | `--c-device` | `#6BCB77` |
| element-locator | `--c-element` | `#A78BFA` |
| case-manager | `--c-case` | `#4ECDC4` |
| test-runner | `--c-runner` | `#FFB5A7` |
| report-generator | `--c-report` | `#7C6F83` |
| ai-assistant | `--c-ai` | `#E879F9` |
| workflow | `--c-workflow` | `#89CFF0` |

允许用途：描边装饰、图标色、图表系列色、浅色底块、硬阴影色源。**禁止**铺正文大面积，**禁止**当普通卡片底色。

## 1.3 状态色

| 状态 | 描边/图标 | 底色 | 文字 | 令牌 |
|------|-----------|------|------|------|
| 成功/在线 | `#6bcb77` | `#c8f5d0` | `#2d7a31` | `--app-status-success` / `-bg` / `-text` |
| 危险/失败 | `#ffb5a7` | `#ffe9e8` | `#b23838` | `--app-status-danger` / `-bg` / `-text` |
| 紫色/锁定 | `#c7b6f8` | `#f6eafe` | `#5b45a4` | `--app-status-purple` / `-bg` / `-text` |
| 警告/等待 | `#f7c948` | `#fff8e0` | `#826208` | `--app-status-warning-bg` / `--app-warning-text` |
| 离线/禁用 | `#c9cacc` | `#fffef5` | `#96918c` | `--app-offline` / `--app-text-secondary` |
| 通过（旧档） | `#c8f5d0` | — | `#1a5c2a` | `--app-pass` / `--app-pass-text` |
| 失败（旧档） | `#ffe9e8` | — | `#7a1c1c` | `--app-fail` / `--app-fail-text` |
| 待定（旧档） | `#cbe8fd` | — | `#1a426f` | `--app-pending` / `--app-pending-text` |
| 实时/错误 | `#f56b6a` | `#ffe9e8` | — | `--app-live` / `--app-error` / `--app-error-bg` |

对比度：交互文本（按钮文字、分段控件选中态、表单校验提示、错误面文字）与自身背景 **≥ 4.5:1**；`--el-color-danger` 取 `--color-red-46`（不是 EP 默认 `#f56c6c`）就是为了这条。

## 1.4 字号刻度

字号最小 **12px**，只允许 7 档，**禁止硬编码 `font-size` 字面量**。

| 刻度 | CSS 变量 | 值 | 场景 |
|------|----------|:--:|------|
| xs | `--app-size-xs` | 12px | 按钮文字、表格列头、标签、Badge、时间戳 |
| sm | `--app-size-sm` | 14px | UI 正文（默认阅读字号） |
| md | `--app-size-md` | 16px | 卡片标题、表单标签、模块标题、分区块标题 |
| lg | `--app-size-lg` | 20px | 段落标题、弹窗标题 |
| xl | `--app-size-xl` | 24px | 页面标题 |
| 2xl | `--app-size-2xl` | 32px | KPI 数字、Hero 数字 |
| 3xl | `--app-size-3xl` | 48px | 品牌展示级（唯一消费点：登录页 Hero 标题）|

图形/展示级例外（允许字面量，判定语：表达图形尺寸而非文本层级）：树节点图标 18px · 空态 emoji 40px · 404 数字 96px。

## 1.5 字体层级

| 层级 | 字体令牌 | 字重 | 字号 |
|------|----------|:--:|------|
| 页面标题 | `--app-font-display` | 700 | `--app-size-xl` 24px |
| 段落标题 | `--app-font-display` | 700 | `--app-size-lg` 20px |
| 品牌文字 | `--app-font-brand` Ziku FeiYang（字库星球飞扬体，仅 400）| 400 | 22–48px（登录页 Hero / 侧栏品牌）|
| KPI 数字 | `--app-font` | 800 | `--app-size-2xl` 32px |
| UI 正文 | `--app-font` | 500 | `--app-size-sm` 14px |
| 辅助文字 | `--app-font` | 500 | `--app-size-xs` 12px |
| 按钮/标签 | `--app-font` | 600–800 | `--app-size-xs` 12px |
| 代码 | `--app-font-mono` Cascadia Mono | 400–700 | `--app-size-xs` 12px |

`--app-font-display` = `--app-font`（同一套字族，没有第二套显示字体）。全局字体：英文 **Cascadia Mono**（等宽，本机已装则零下载，否则 jsDelivr woff2），中文 **思源黑体 Noto Sans SC**（Google Fonts 分片加载）。品牌字例外用 Ziku FeiYang（本地 `/fonts/ziku-feiyang.ttf`，已子集化，仅 Regular）。
Blockly 等 JS 画布渲染不解析 CSS 变量，字体用字面量——改全局字体时需同步 `TestCaseBlockly.vue` 的 `fontStyle.family`。

## 1.6 圆角 — 几何不对称（**二值写法，禁四值展开**）

| 场景 | CSS 变量 | 值 |
|------|----------|-----|
| 按钮 / 输入框 | `--app-radius-sm`（原子 `--radius-sm`）| `4px 8px` |
| 卡片 / 弹窗 | `--app-radius-md`（原子 `--radius-md`）| `6px 10px` |
| 大块容器 | `--app-radius-lg`（原子 `--radius-lg`）| `8px 14px` |
| 胶囊 / 导航芯片 | `--app-radius-pill`（原子 `--radius-pill`）| `4px 10px 6px 8px` |
| 表格 | `--app-radius-table`（原子 `--radius-table`）| `4px 10px` |
| EP 基值 | `--el-border-radius-base` | `4px 8px` |
| EP 小值 | `--el-border-radius-small` | `3px 6px` |
| EP round | `--el-border-radius-round` | `4px 10px 6px 8px` |

**登记例外**（可写字面量）：真实圆形 `50%` · 近直角纸角 2px（`--comp-note-radius` / `--comp-kpi-radius` / `--comp-sheet-radius` = `2px 6px 2px 4px`）· 图形量 1px / 3px / 5px · `0` 重置 · 登录页已登记的独立造型。
**禁止**：对称大圆角 `999px` / `8px` / `12px` / `50px`；与令牌等价的四值展开（`4px 8px 4px 8px`、`6px 10px 6px 10px`、`3px 6px 3px 6px`）——门禁直接拦截。

## 1.7 阴影层级 — 扁平硬偏移，**模糊半径必须为 0**

| 层级 | CSS 变量 | 值 | 场景 |
|:--:|------|------|------|
| sm | `--app-shadow-sm` | `2px 2px 0 rgba(0,0,0,0.04)` | 卡片默认、纸艺卡片 |
| md | `--app-shadow-md` | `2px 3px 0 rgba(0,0,0,0.05)` | 拍立得卡片、KPI 卡 |
| lg | `--app-shadow-lg` | `3px 4px 0 rgba(0,0,0,0.06)` | 弹窗 |
| 强调硬影 | `--comp-*-shadow`（如 `--comp-sheet-shadow-x/y`、`--comp-dialog-shadow`）| `4px 4px 0 0 <模块色或墨色>` | 钉板卡 / 表纸 / 弹窗 |

禁止模糊阴影、外发光（`0 0 <blur>`）、大扩散；经自定义属性间接声明的阴影同样受此约束。

## 1.8 间距刻度

| 刻度 | 值 | CSS 变量 | 场景 |
|------|:--:|------|------|
| xs | 4px | `--app-space-xs` | 图标与文字紧贴 |
| sm | 8px | `--app-space-sm` | 标签之间、Badge 内边距 |
| md | 16px | `--app-space-md` | 卡片/面板 padding |
| lg | 24px | `--app-space-lg` | 卡片之间、页头与正文的左内边距 |
| xl | 32px | `--app-space-xl` | 内容区 padding |
| 2xl | 48px | `--app-space-2xl` | 页面顶部/底部留白 |

**强制用变量**，禁止 `padding: 15px` `gap: 20px` 一类随意值。

## 1.9 动效

| 用途 | 时长 | CSS 变量 |
|------|:--:|------|
| hover 变色、图标缩放、按钮按下 | 0.12s | `--app-duration-fast` |
| 卡片抬起、展开/收起 | 0.15s | `--app-duration` |
| 路由切换、弹窗进出 | 0.25s | `--app-duration-slow` |

easing：`--app-ease: cubic-bezier(0.25,0.1,0.25,1)`、`--app-spring: cubic-bezier(0.34,1.56,0.64,1)`。

`prefers-reduced-motion: reduce` 时：`.fade-slide-*` 路由过渡 `transition: none` 直接切页；`shared/animations.ts` 的 JS 编排跳过过程、落到终态（void 函数写终值；返回句柄的函数 `duration: 0`）；**凡 `transition` 里动了 `transform` 的文件都必须提供降级块**（只动颜色/边框色的可免）。已登记的循环装饰动效例外：骨架 shimmer `1.4s`、状态脉冲 `1.5s`。

**已降级**（有 `@media (prefers-reduced-motion: reduce)` 块）：`.el-button:active` · `.ac-card` · `.fade-slide-*` · AppCard / SketchCard / KpiCard / DoodleNote / DoodleBtn / WorkbenchCrumbs · SkeletonCard。

**未降级**（现存缺口，别照抄；见 [known-gaps.md](known-gaps.md)）：侧栏微倾 · `.wb-shell .el-card` hover 位移 · `.ac-tabs` · `wb-btn` · 输入框 focus 环 · `ErrorState` 按钮 · `FilterTabs`。

## 1.10 颜色使用规则

| 颜色 | 允许用途 | 禁止用途 |
|------|---------|---------|
| `--ink` | 正文、标题、图标、实色边框 | — |
| `--app-text-secondary` / `--app-text-muted` | 辅助文字、占位符、禁用态 | 正文、标题 |
| `--c-*` 模块色 | 描边装饰、图标色、图表系列色、浅色底块、硬阴影色源 | 正文大面积、普通卡片底色 |
| 状态色 | Badge、状态标签、告警提示 | 正文、普通卡片底色 |
| `--app-highlight` | hover 高亮背景 | 默认背景色 |

> 速查：改颜色 → 查 1.1 / 1.2 / 1.3 → 用 `var(--xxx)` → 禁止字面量；确需新色值先按 1.14 登记。

## 1.11 仪表盘统计卡（奶油低饱和）

| CSS 变量 | 实际值 | 用途 |
|----------|--------|------|
| `--app-stat-text` | `#5d5950` | 卡片主文字 |

## 1.12 层叠 z-index 档位

| CSS 变量 | 值 | 用途 |
|----------|:--:|------|
| `--z-base` | 1 | 普通流内的层叠基准 |
| `--z-raised` | 2 | 局部浮起 |
| `--z-header` | 10 | 页头 `.wb-header` |
| `--z-popup` | 60 | 浮层（下拉、上下文菜单） |
| `--z-overlay` | 80 | 模块内高位浮层 |
| `--z-modal-backdrop` | 9990 | EP 模态遮罩 |
| `--z-modal` | 9991 | EP 模态本体 |

`z-index` 优先取上表令牌；未纳入档位的一次性值可留字面量，但必须在 T0 的层叠段登记用途。**引用了未声明的 `--z-*` 会在 computed-value 阶段静默失效回落 `auto`**（门禁拦截悬空引用）。

## 1.13 布局尺寸与断点

| CSS 变量 | 值 | 用途 |
|----------|:--:|------|
| `--app-topbar-h` | 96px | 页头/侧栏品牌区高度（两者底边对齐）|
| `--side-w` | 228px | 侧栏宽度**兜底值**——运行时由 JS 写在 `documentElement` 上：默认 260px，可拖拽 180–360，折叠 64px。`228px` 只在初始化前生效 |
| `--app-border-width` | 3px | 粗描边基准 |
| `--layout-pane-left` | 280px | 左树/左栏统一宽度 |
| `--layout-ratio-chart` | `1.5fr 1fr` | 主/副图表行比例 |
| `--layout-kpi-cols` | `repeat(4, minmax(0,1fr))` | KPI 指标行（3 项行用 auto-fit 自适应，属登记例外）|

断点档位（桌面优先，`max-width`）：**sm 768px**（KPI 4→2 列、登录页留白）· **md 1024px**（工作台双栏→单列）· **lg 1200px**（宽屏双栏切换）。
⚠️ media query 内不能用 `var()`，断点只登记档位；存量值 1200/1100/960/900/800/768 待迁移到档位，**改值会改变折叠时机，必须视觉确认**。

## 1.14 令牌命名与落点（加新值前必读）

| 层 | 落点 | 命名 | 规则 |
|----|------|------|------|
| T0 原子 | `shared/styles/tokens.css` 的 `:root` | `--color-<色相>-<明度>[-s<饱和>][-a<alpha>]` · `--font-*` · `--space-*` · `--radius-*` · `--shadow-*` · `--duration-*` · `--ease` · `--size-*` · `--z-*` | **字面量色值的唯一登记处**；同一色值只声明一次；原子名不得含模块名或场景名 |
| 兼容别名 | 同上 | `--app-*` | 值 = `var(原子)`；消费点可继续用，避免大改 |
| 通用组件 | 同上 | `--comp-<组件>-<场景>` | `shared/components/**` 跨模块复用的配色；值必须引用颜色原子 |
| 模块令牌（T1）| `modules/<模块>/tokens.css` | `--<模块前缀>-*` | 作用域必须是**该模块页面根类**（`.ai-workbench` / `.case-workbench` / `.inspector-workbench` / `.locator-workbench` / `.workflow-workbench`），**不得**提升到 `:root`；值必须引用 T0 原子；模块不得借用别的模块的家族 |
| EP 覆盖 | `shared/styles/tokens.css` 的 EP 段 | `--el-*` | 值**只能**是 `var(...)`，不得写字面量 |

新增颜色的正确顺序：**先复用最接近的原子（感知聚类 ΔE ≤ 8）→ 确需新增才登记原子 → 消费处 `var()` 引用**。颜色原子总数只降不增，禁止序号兜底名（`-2`…`-9`）。
脚本里传令牌字符串**不许带字面量兜底**（`var(--x, #fff)`）。

## 1.15 样式门禁（提交前会被机械校验）

| 编号 | 校验点 |
|:--:|------|
| 批 1 | **字号下限**：样式侧 `font-size` 字面量不得低于 12px；画布侧（ECharts / VueFlow 的 JS 配置）单独计量、只降不增 |
| G1 | 颜色原子唯一：同一色值只声明一次（`--color-*` 必须是色值，消费处为 `var()`）|
| G2 | 非原子声明不得出现纯色字面量（ECharts / canvas 绘制色与已登记的分类色板例外）|
| G2b | 复合值（阴影 / 渐变）内嵌颜色允许，但需登记 |
| G3 | 模块家族令牌只做组合：模块前缀声明不得直接持有字面量 |
| G4 | **引用完整性**：`var()` 引用必须能在 T0 找到声明（防 `--el-*` 覆盖改 `var` 后静默回退）|
| G8–G10 | 颜色原子必须属于调色板、形状合法、不得是序号兜底名（`-2`…`-9`）|
| G11 | 颜色原子总数不得超过调色板上限（只降不增）|
| G12 | 阴影模糊半径必须为 0 |
| G13 | 圆角必须取 `--app-radius-*` / `--radius-*`，或属已登记的图形量与独立造型（禁止等价四值展开）|
| G14 | 动效时长必须取 `--app-duration-*`（`transition` / `animation` 简写里的裸时长同样受管）|

命令：`cd frontend && npm run lint:styles`（真相源：`frontend/tests/check-style-gates.mjs`；编号与判定口径以该脚本为准）。

## 1.16 纸面与纹理（与令牌直接相关）

- L0 纸面 = `--paper` **暖白实色**，**禁止**点阵 / 横线本 / 网格纹理（历史版本有"点阵纸纹"说法，已作废）
- 唯一装饰来源是 `shared/components/PaperDoodles.vue`（稀疏手绘 SVG，`pointer-events: none`，只挂主内容区，不进侧栏）
- 页头（`.wb-header`）底色同样取 `--paper`，与侧栏、正文同纸面，靠底部墨线分隔
- `--app-border-light` / `--app-border-lighter` 与纸面近同色，**只能当占位**，不得当可见边框色；确需占位时写 `transparent` 并注明意图

## 1.17 Element Plus 变量映射（41 条，值全部为 `var()`，禁字面量）

声明在 `tokens.css` 的 EP 段；改 EP 外观只改这里，不在模块里重复皮肤。

| 组 | 关键映射 |
|----|----------|
| 主色 | `--el-color-primary` → `--color-yellow-63`（柠黄，**不是 EP 蓝**）；AI 模块在 `.ai-workbench` 内改写为 `--color-purple-73` |
| danger / error | `--el-color-danger`/`-error` → `--color-red-46`（不是 EP `#f56c6c`），使实心底与校验文字都满足 4.5:1；plain 描边 → `--color-red-85`、plain 底 → `--color-red-95` |
| 背景 | `--el-bg-color`/`-page` → `--paper`；`--el-fill-color`/`-darker` → `--color-orange-76`（替代 EP 冷灰 `#f0f2f5`）；`--el-fill-color-light` → `--color-lime-94`；`--el-bg-color-overlay` → 白 |
| 文字 | `--el-text-color-primary`/`-regular` → `--ink`；`-secondary` → `--color-ink-57` |
| 边框 | `--el-border-color` → `--ink`；`--el-border-color-light` → `--color-lime-94` |
| 圆角 | `--el-border-radius-base` = `4px 8px`；`-small` = `3px 6px`；`-round` = `4px 10px 6px 8px` |
| 阴影 / 字体 | `--el-box-shadow-light`/`-`/`-dark` → `--shadow-sm`/`md`/`lg`；`--el-font-family` → `--app-font` |
| 开关 | `--el-switch-on-color`/`-off-color` → 成功色 / 离线灰 |

**未映射**（仍走 EP 出厂值，改主题时注意）：`--el-text-color-placeholder`、`--el-border-color-lighter`/`-dark`/`-extra-light`、`--el-table-*`、`--el-disabled-*`、success / warning / info 的 light/dark 档。
