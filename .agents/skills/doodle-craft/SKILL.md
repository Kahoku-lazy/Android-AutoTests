---
name: doodle-craft
description: |
  Doodle Craft 主题前端 UI 开发与维护 — 做页面/组件/改样式。极简几何粗线涂鸦彩绘卡通风格，令牌唯一真相源 tokens.css，复制不发明、令牌不硬编码、四层不越界。
  默认口径：前端 UI 的新增与改版一律默认采用本技能方案；需求未明确提出新设计/新风格时，禁止自创视觉，直接按本技能的布局变体、组件规格与令牌落地。
  Keywords: Doodle Craft, 主题, 前端 UI, 组件, 样式, 设计令牌, tokens.css, 卡通风格, doodle, theme, UI, 默认设计, 设计口径, 界面默认方案
  Trigger: 任何前端 UI 工作（做页面/做组件/改样式/界面改版/新增交互界面）默认加载并按本技能方案落地；Doodle Craft 主题迭代时。
---

# Doodle Craft 主题

Doodle Craft 是本平台前端的**默认设计方案**：极简几何 · 粗线涂鸦 · 彩绘卡通 · 手稿纸。它不是一套可选皮肤，而是这个仓的 UI 基线——新增页面、新增组件、界面改版、写样式，第一步都是先按本技能落地，而不是从零设计一遍。

**权威顺序**（冲突时按此判定）：`frontend/src/shared/styles/tokens.css`（令牌值）→ `frontend/src/style.css`、`shared/styles/workbench-theme.css`、`shared/components/**`（皮肤实现）→ 本技能 `references/`（规格与口径）→ 其它文档。发现不一致时以代码为准，并把文档改齐。

## 默认设计口径（强制）

1. **默认即采用**：新增页面、新增组件、界面改版、写样式，第一步先查本技能参考 → 复制最接近的模板 → 只改内容字段。**「先随便做一版看看」不是允许路径**；不确定要不要设计时，按默认做，不要反过来问需求方要风格。
2. **不自创**：不做需求没要求的视觉决定——配色、字体、字号、间距、圆角、阴影、动效、层次手法一律取令牌与既有规格。没有对应模板时，优先用 `shared/` 共享零件组合；仍无则**先按本技能规则新增模板并登记**，再复用，禁止就地写一次性样式。
3. **偏离的唯一入口**：只有需求方**明确提出**新设计（换风格 / 参考某站点或某张图 / 指定配色版式）时才偏离默认。偏离时先说清范围与影响面，落地后**必须**把新规则登记回 `references/tokens.md` + `tokens.css`（涉及组件或版式时同步 `references/components/`、`references/page-layout.md`），不得只改一个组件了事。
4. **默认可否决**：需求没提设计要求 ≠ 可以自由发挥；按默认落地后，在交付说明里用一句话交代「采用了哪套既有默认」，供需求方否决或微调。
5. **可机械验证优先**：能被工具判定的（色值、字号、圆角、阴影、令牌引用）一律交给门禁，不靠人眼；判不了的（卡片微倾、层次手法）在自检里逐条过。

## 线型规则（强制）：虚线是组件皮肤，不是页面装饰

**默认实线。** 只有下列 **已登记的组件样式** 允许虚线；判定看**组件**，不看页面、不看功能名。同一组件被复用到任何页面、任何业务场景，虚线都随之成立；反过来，把这个组件的虚线样式**抄到别的组件里不算数**。

| 允许虚线的样式 | 承载组件 / 落点 | 长什么样 |
| --- | --- | --- |
| 助手颜料片 | `AssistantCard`（`.assistant-card`） | 上边沿笔色图钉 + 头像或笔色圆 + 用户名 + Agent 配置名；卡内「配置 / 对话」动作按钮（外框 2.5px，动作 1.5px）。同一组件另出**工作流形体**（名称 + 「执行 → 验收」+「配置 / 任务」），见 [components/assistant-marker-card.md](references/components/assistant-marker-card.md) §3.1 |
| 助手对话栏面板 | `AssistantLanePanel`（`.lane-panel`） | 对话页左栏：标题「对话栏」+ 笔色双波浪线 + 对话栏列表；外框 `1.5px dashed` 浅墨、**不倾斜**，见 [components/assistant-marker-card.md](references/components/assistant-marker-card.md) §5 |
| 运行日志卡 | `ThreadLogPanel`（`.thread-log__card`） | 对话页日志：一轮一张，`1.5px dashed` 笔色 + 顶部居中胶带 + `4px 4px` 硬影，**0° 不倾斜**，见 [components/assistant-marker-card.md](references/components/assistant-marker-card.md) §5.2 |
| 页面分区虚线 | `SectionDivider`（`.section-divider`） | 两段并列内容之间的一条 `1.5px dashed` 浅墨横线（`color-mix(ink 38%)`），**只做分区**；外边距由使用方给根节点加，组件不预设 |
| 助手角色卡 | `AgentRouteCard`（`.route-card`，DoodleNote 皮） | 头像 + 职责 + 配置入口（助手看板 Agent-01 / Agent-02） |
| 手稿控件皮肤 | `Sketched UI Kit`（`.sketch-kit` 作用域，`shared/styles/sketched-kit.css`） | 按钮描边态 + 输入框 / 多行框 / 下拉框边框，见 [components/sketched-ui-kit.md](references/components/sketched-ui-kit.md) |

> **2026-11-09 变更**：`KpiCard`（核心指标卡 / 统计汇总卡）按需求由虚线改为**实线**，描边色 = 硬阴影色 `var(--kpi-accent)`（`2.5px solid var(--kpi-accent)`）。
> 它**已移出虚线白名单**（门禁 `tests/check-dashed-whitelist.mjs` 的 OWNERS 同步移除）；若将来要回到虚线，需先在 SKILL.md 本表重新登记并放回 OWNERS。
>
> **2026-11-16 变更**：新增分类 `Sketched UI Kit`（需求方提供按钮五态 / 输入四态参考图），虚线从「只属于助手角色卡」扩到「**控件级**：按钮描边态 + 输入框」。门禁 OWNERS 同步加入 `shared/styles/sketched-kit.css`。**卡片 / 表纸 / 弹窗 / 抽屉外框 / 页面装饰仍然一律实线**，这一条没有放宽。
>
> **2026-11-16 变更 2**：需求方提供 Five Marker Colors 的 Wavy Underline 参考图，对话页左栏从实线细框改为 **浅墨虚线卡**（`1.5px dashed color-mix(ink 38%)` + 笔色双波浪线，**不倾斜**）。落点是新组件 `AssistantLanePanel.vue`，OWNERS 同步加入；对话页其它部分（气泡、输入框、按钮）仍实线。
>
> **2026-11-16 变更 3**：需求方提供手绘虚线卡参考图（虚线外框 + 顶部胶带 + 偏移阴影），对话页**运行日志**改为一轮一张虚线卡（`1.5px dashed color-mix(笔色 70%, 纸色)`，**0° 不倾斜**，明确不要胶带倾斜）。落点是 `modules/ai-assistant/components/ThreadLogPanel.vue`，OWNERS 同步加入。**其它卡片 / 表纸 / 弹窗 / 抽屉 / 页面装饰仍然一律实线**。

判据按顺序问，命中即止：

1. 这段虚线的元素，是不是由 `AssistantCard`、`AssistantLanePanel`、`ThreadLogPanel`、`SectionDivider` 或 `AgentRouteCard` 渲染出来的？→ 是，**允许虚线**，且换页面复用照样允许
2. 这段虚线的元素，是不是 `.sketch-kit` 作用域内的按钮或输入框？→ 是，**允许虚线**，但必须来自 `sketched-kit.css`，不得就地手写
3. 是不是把它们的虚线 CSS 复制到了别的组件 / 就地手写了一遍同款卡片？→ **不算白名单**，要么改用组件，要么写实线
4. 其它所有 UI —— 图表卡、表格卡、入口卡、条目卡、任务卡、对话框、抽屉、表纸、缩略图、证据块、列表分隔、聚焦轮廓 → **实线**

**实线口径**：`1px solid color-mix(in srgb, var(--ink) 10%, transparent)`；圆角取 `--app-radius-*`；不再用 1.5px / 2px / 2.5px 实线粗描边分层，层级靠「页面底 → 卡片 → 浅底内嵌 → 白卡」四层背景拉开。

**虚线口径**（仅白名单）：

- 助手颜料片：`2.5px dashed var(--ink)`（外框）/ `1.5px dashed var(--ink)`（卡内动作），由 `AssistantCard.vue` 自己声明。
- 助手对话栏面板：`1.5px dashed color-mix(in srgb, var(--ink) 38%, transparent)`，**只此一档、不倾斜**，由 `AssistantLanePanel.vue` 自己声明。
- 运行日志卡：`1.5px dashed color-mix(in srgb, var(--assistant-marker) 70%, var(--paper))`，**只此一档、0° 不倾斜**，由 `ThreadLogPanel.vue` 自己声明；胶带与硬影用同一笔色派生。
- 助手角色卡：`2.5px dashed var(--ink)`，**只此一档**，由 `AgentRouteCard.vue` 自己声明。
- 手稿控件（kit）：按钮描边态 `1.5px dashed var(--comp-kit-line)`，输入框 `1.5px dashed var(--comp-kit-line-soft)`，禁用态 `var(--comp-kit-border-faint)`；一律经 `--comp-kit-*` 令牌声明，不写裸 `dashed` 颜色。
- 不得靠全局选择器给白名单以外的组件批量染色。

**违规判定**：`grep -rn "dashed" frontend/src` 的结果里，只有 `AssistantCard.vue`、`AssistantLanePanel.vue`、`ThreadLogPanel.vue`、`AgentRouteCard.vue`、`SectionDivider.vue` 与 `shared/styles/sketched-kit.css` 可以出现 `dashed`（与门禁 `check-dashed-whitelist.mjs` 的 OWNERS 一一对应）；其它文件（含全局 `workbench-theme.css` / `style.css` / `tokens.css`）出现即违规。

**存量待迁移**（规则已生效、代码尚未改完；动到下列文件时顺手改实线，不要新写虚线）：`workbench-theme.css` 的 `.wb-shell .ac-card` 全局虚线（连带 11 个 AppCard 实例）、`style.css` 的 `.el-dialog` / `.el-drawer`、`tokens.css` 的 `--comp-sheet-border` / `--comp-dialog-border`、`DoodleNote` 基类虚线（应下沉到 `AgentRouteCard` 自持，`TaskBoard` 的任务卡随之改实线）、`SketchCard`、`StepLogCheck`、`StepLogEvidence`、`TaskAttemptCard`、`CaseStepList`、`WorkflowDirTree`、`PageFlowNode`、`DashboardView`、`ActivityTimeline`、`DisconnectDialog`、`VoiceConsole`、`TranscriptPanel`、`CaseFileSheet`、`WifiPortPanel`、`LoginView` 内的本地 `dashed`。

## 先选场景

| 场景 | 入口 |
| --- | --- |
| **平台内 Vue 页面 / 组件**（真实代码，Element Plus + `shared/` 共享件，走 openspec 验收） | [references/vue-project.md](references/vue-project.md) |
| **单文件 HTML**（预览稿 / 原型 / 报告，无构建步骤，手写组件样式） | [references/standalone-html.md](references/standalone-html.md) |

两个场景共用下面的风格口径、令牌分组、组件目录与硬规则。

## 一段话说清风格

暖白纸面（`--paper` `#f3efe2`，不是纯白），墨色粗线勾边（`--ink` `#1e1e24`，2.5px 描边；**实线为主，虚线只留助手颜料片 / 对话栏面板 / 运行日志卡 / 手稿控件皮肤（`.sketch-kit`）四处**，见上节），立体感一律靠**硬偏移阴影**（模糊半径恒为 0），圆角是刻意**两角不同**的二值写法（按钮 `4px 8px`、卡片 `6px 10px`、胶囊 `4px 10px 6px 8px`），八支模块彩笔只做描边 / 图标 / 图表色与硬阴影色源，卡片网格按序号微倾 ±0.4°~1.5° 并在悬停时回正抬起，动效只走 `0.12 / 0.15 / 0.25s` 三档；全站字体一套（英文 Cascadia Mono 等宽 + 中文思源黑体），字号 7 档（12–48px）。

## 设计令牌

**值刻意不在本技能里复述**：唯一真相源是 `frontend/src/shared/styles/tokens.css`（T0 原子 `--color-*` / `--font-size-*` / `--space-*` / `--radius-*` / `--shadow-*`，兼容别名 `--app-*`，通用组件 `--comp-*`，EP 覆盖 `--el-*`）。本技能的 [references/tokens.md](references/tokens.md) 是它的**检索表**（分组 / 用途 / 精确值），改视觉属性时查它。

| 要改什么 | 落点 | 检索 |
| --- | --- | --- |
| 颜色 | `tokens.css` 的颜色原子（按色相命名，同值只登记一次） | [tokens.md](references/tokens.md) §1.1–1.3 |
| 字号 / 字体 | `--font-size-*` / `--app-font*` | [tokens.md](references/tokens.md) §1.4–1.5 |
| 圆角 / 阴影 / 间距 / 动效 | `--radius-*` / `--shadow-*` / `--space-*` / `--duration-*` | [tokens.md](references/tokens.md) §1.6–1.9 |
| Element Plus 外观 | `tokens.css` 的 `--el-*` 段（值只能是 `var(...)`）；模块确需差异才写 `:deep()` | [tokens.md](references/tokens.md) §1.17 |
| 模块专属色板 | `modules/<模块>/tokens.css`，作用域 = 该模块页面根类 | [tokens.md](references/tokens.md) §1.14 |

**11 支彩笔令牌**（跨技能对齐的语义映射，记错就穿帮，故留在入口）：

| 令牌 | 变量 | 色值 | 现消费方 |
| --- | --- | --- | --- |
| 仪表盘 | `--c-dashboard` | `#F7C948` 柠黄 | dashboard |
| 设备 | `--c-device` | `#6BCB77` 薄荷绿 | device-pool、侧栏「设备管理」 |
| 靛紫 | `--c-element` | `#A78BFA` 薰衣草紫 | report-generator、device-pool、dashboard、ai-assistant、侧栏「Agent 配置」 |
| 用例 | `--c-case` | `#4ECDC4` 青绿 | case-manager |
| 桃粉 | `--c-runner` | `#FFB5A7` | report-generator、dashboard |
| 报告 | `--c-report` | `#7C6F83` 灰紫 | report-generator |
| AI | `--c-ai` | `#E879F9` 柔粉紫 | ai-assistant、侧栏「AI 助手」 |
| 流程 | `--c-workflow` | `#89CFF0` 天蓝 | workflow、侧栏「串口日志」 |
| 运营 | `--c-ops` | `#B2710C` 赭橙 | ops-console（运营后台）、侧栏「模型配置」 |
| 账号 | `--c-account` | `#7A8FE2` 靛蓝（原子 `--color-blue-68-s64`）| **仅**侧栏「用户管理」 |
| 任务 | `--c-task` | `#C050D0` 紫（原子 `--color-purple-56`）| **仅**侧栏「任务清单」 |

> `--c-element` / `--c-runner` 已无同名模块页面，但仍被共享表格、看板卡片与报告页引用，**不得**当死令牌删除。
>
> **2026-11-17 新增 `--c-account` / `--c-task`**：需求方要求侧栏各入口不同色（原来运营三项同为赭橙、串口与设备同为薄荷绿）。这两个是**入口级**色，只用于侧栏图标底色与 active 书签条，不扩散到页面；都复用调色板已有原子，**不新增** `--color-*`（调色板按 `frontend-l0-design-tokens` 只降不增）。侧栏同分组内入口 **MUST NOT** 同色，由 `frontend/tests/shared/p0/sidebarNavConfig.spec.ts` 断言锁住。

## 组件目录

组件规格按类目拆在 `references/components/` 下（维度 × 实际规格，**以代码为准**；标「未覆盖」= 该维度没有主题声明、走 Element Plus 出厂值）：

| 类目 | 组件 | 参考 |
| --- | --- | --- |
| 通用 | Button（EP + `wb-btn` 变体）、DoodleBtn、ConfirmButton、Tag | [general.md](references/components/general.md) |
| 布局 | WorkbenchHeader、WorkbenchCrumbs、AppSidebar、`.doc-section`、AppTabs / FilterTabs | [layout.md](references/components/layout.md) |
| 卡片 | AppCard 钉板卡、SketchCard 撕纸卡、KpiCard 指标卡、DoodleNote 涂鸦条目卡 | [cards.md](references/components/cards.md) |
| AI 助手（专有） | AssistantCard 颜料片、配置弹窗、测试对话页（一卡一色 + 笔色渐变） | [assistant-marker-card.md](references/components/assistant-marker-card.md) |
| 表单控件 | Form / Input、Select、Cascader、el-switch、el-radio-button 分段控件 | [form-controls.md](references/components/form-controls.md) |
| 手稿控件（分类） | **Sketched UI Kit**：按钮五态（Primary / Danger / Highlight / Disabled / Teal）+ 输入四态 + label，作用域 `.sketch-kit` | [sketched-ui-kit.md](references/components/sketched-ui-kit.md) |
| 数据展示 | Table（EP 皮肤）、AppTable 表纸、分页 `usePagination`、**表格字号三档 16 / 14 / 12** | [data-display.md](references/components/data-display.md) §1.1 |
| 浮层 | Dialog / Drawer、ElMessageBox 确认框 | [overlays.md](references/components/overlays.md) |
| 反馈 | SkeletonCard、ErrorState、EmptyState、el-message / el-alert | [feedback.md](references/components/feedback.md) |
| 装饰 | PaperDoodles 纸面涂鸦、微旋转机制、图钉 / 胶带 | [decorative.md](references/components/decorative.md) |

**选型判据**（照表用，不自创）：

| 你要做的东西 | 用什么 | 别用 |
| --- | --- | --- |
| 页面级分区（带标题的一大段） | `.doc-section` | AppCard |
| 可复用数据块（图表卡 / 表格卡 / 指标组） | `AppCard` | 裸 `el-card` |
| 资源入口卡（用例） | `SketchCard` | 顶条彩色卡 |
| 单个指标 | `KpiCard` | 自造清新风统计卡 |
| 列表条目 / 线路卡 | `DoodleNote` | AppCard |
| 多行多列列表 | `AppTable` | 原生 `el-table`、`el-card` 外套 |
| 分页 | `usePagination` + 自绘控件 | EP 分页皮肤、自写状态机 |
| 页头 | `WorkbenchHeader` | 第二套页头 |
| 子页返回 / 面包屑 | `WorkbenchCrumbs`（放 `.doc-body` 顶部） | 页头内的 nav、正文 `.back-btn` |
| 内容卡操作按钮 | `DoodleBtn` | 改页头 `wb-btn` |
| 手稿/纸片语境的表单与工具条（虚线描边 + 无影） | 容器加 `.sketch-kit`，按钮仍用 `DoodleBtn` | 另造一套按钮组件、把虚线用到卡片/弹窗 |
| 删除确认 | `ConfirmButton` / `ElMessageBox` | `window.confirm` |
| 弹窗 / 抽屉 | EP `el-dialog` / `el-drawer`（全局皮肤） | 自建遮罩 |
| 加载 / 失败 / 空 | `SkeletonCard` / `ErrorState` / `EmptyState` | 私有 shimmer、`el-alert` 顶替错误态 |

页面层（骨架、分区、滚动、宽度、页面变体）见 [references/page-layout.md](references/page-layout.md)；**别照抄的清单**（现存缺口与已退役写法）见 [references/known-gaps.md](references/known-gaps.md)。

## 硬规则（违反即 bug）

1. 颜色一律 `var(--xxx)`，不写字面量（ECharts / canvas 绘制色例外）；确需新色先复用最接近的原子，再登记 `tokens.css`。→ 门禁 G1 / G2
2. 字号只取 7 档刻度（12–48px），最小 12px，不写 `font-size` 字面量。图形 / 展示级例外仅三处：树节点图标 18px、空态 emoji 40px、404 数字 96px。→ 门禁 批 1（字号下限）
3. 间距只取 6 档刻度（4 / 8 / 16 / 24 / 32 / 48），不写 `padding: 15px`、`gap: 20px` 一类随意值。
4. 圆角取令牌或登记例外（真实圆形 `50%`、纸角 `2px`）；禁止对称大圆角（`999px` / `50px` / `12px`），禁止与令牌等价的四值展开（`4px 8px 4px 8px`）。→ 门禁 G13
5. 阴影模糊半径必须为 0，禁止外发光与 `0 0 <blur>` 扩散；强调硬影统一 `4px 4px 0 0 <模块色或墨色>`。→ 门禁 G12
6. 引用的令牌必须已声明：未声明的 `--x` 会在 computed-value 阶段静默失效（元素看起来"样式没生效"，SVG 描边甚至整条消失）。→ 门禁 G4
7. 页面根必须带主题作用域 `wb-shell`（工作流页为 `workflow-workbench`）：`.ac-card` / `.sketch-sheet` / `.ac-tabs` 的皮肤只在该作用域内生效，忘带就退化成 Element Plus 出厂皮肤。
8. 卡片网格必须有微旋转（±0.4°~1.5° 按序号轮转，走 `sketchTiltAt(i)` 或 `nth-child` 三值轮转）；**禁止所有卡片 0° 排排坐**，也禁止就地写行内 `transform` 压掉 hover 回正。
9. 纸面是暖白实色（`--paper`）：禁止点阵纸纹、横线本、网格纹理当背景；唯一装饰是主内容区稀疏手绘涂鸦（`PaperDoodles`），侧栏不挂。
10. 中间层不得 `overflow: hidden` 裁剪内容；纵向滚动只留在 `.doc-body`（`flex: 1 1 0` + `min-height: 0` + `overflow-y: auto` 三者缺一不可），表格只做横向滚动，卡片与弹窗内部不滚动。
11. 一个零件只有一套皮肤：禁自建第二套卡片 / 表格 / 弹窗 / 分页 / 图标；改 EP 外观只动 `style.css` + `tokens.css` 的 `--el-*`，模块确需差异才写 `.<模块根类> :deep()`。**已登记的皮肤分类是唯一例外**：`Sketched UI Kit`（`.sketch-kit`）由 `shared/styles/sketched-kit.css` 统一提供，复用它 ≠ 自建第二套；在别处就地手写同款虚线按钮仍算违规。
12. 三态必须用共享件（加载 `SkeletonCard` / 失败 `ErrorState` / 空 `EmptyState`），**加载期间不得渲染空态**（假空态）。
13. 凡 `transition` 里动了 `transform` 的样式，必须提供 `@media (prefers-reduced-motion: reduce)` 降级块（只动颜色 / 边框色的可免）。
14. 模块色（`--c-*`）只用于描边装饰、图标色、图表系列色、浅色底块、硬阴影色源；**禁止**铺正文大面积，**禁止**当普通卡片底色。
15. 新建 `.vue` ≤ 500 行（超了先拆样式层再拆逻辑层）；组件只负责渲染与事件绑定，解析与算法下沉 `helpers/`。

## 提交前自检

```
[ ] 未自创视觉：用到的骨架/零件/配色均来自本技能与 shared/（有新增则已登记回本技能参考）
[ ] 未越界：页面根带 wb-shell；没写第二套卡片/表格/弹窗皮肤；模块差异才用 :deep()
[ ] 手稿控件：用了 `.sketch-kit` 就走 kit 全套（虚线描边态无影 + 填充态硬影），不与其外的实线输入框混用
[ ] 线型：虚线只出现在 OWNERS 登记的组件（AssistantCard / AssistantLanePanel / ThreadLogPanel / AgentRouteCard / sketched-kit.css）；cards/表格/弹窗仍实线
[ ] 令牌：颜色全 var(--xxx) 且引用已声明；字号/间距/圆角/阴影全取刻度
[ ] 微倾：卡片网格按序号轮转（非全 0deg）；hover 能回正
[ ] 纸面：暖白实色 + 主区稀疏涂鸦；无点阵/横线本；无 backdrop-filter
[ ] 滚动：页面只靠 .doc-body 纵向滚动；缩小窗口验证不裁剪
[ ] 三态齐备：加载/失败/空各有共享件，且加载期间不渲染空态
[ ] 门禁：cd frontend && npm run lint:styles（批 1 字号下限 · 批 2 token 唯一性与引用完整性 · 批 4 几何尺度）+ npx vue-tsc --noEmit
[ ] 交付：新 .vue ≤ 500 行；说明里交代了采用的是哪套既有默认
```

> 工程门禁（布局裁剪 / 契约 / 可达性 / 四态）与前端编码规范（Vue / TS / 文件组织）遵循 `frontend/AGENTS.md`；样式硬门禁跑 `cd frontend && npm run lint:styles`；验收契约见 `openspec/specs/frontend-l*`、`frontend-doodle-*`。
