## Why

前排分析得出四个布局缺口：① 无栅格/断点体系（45 处 `grid-template-columns` 各写各的，断点 6 个值无令牌）；② 同模式多取值（左固定栏 280/240/300px、主副图 1.5fr/1.4fr、KPI 行两套写法）；③ 骨架类被模块重定义（`ai-assistant/index.style.css` 又定义了一遍 `.doc-body`）；④ 页面级滚动与内层滚动并存，而切换开关是**主题类** `.wb-shell`。本变更按"先零风险、再收敛"的顺序修这四个缺口。

## What Changes

- **④ 滚动策略显式化（行为等价）**：新增 `.doc-page--fixed` 作为"视口固定 + 内层滚动"的显式开关；`.doc-page.wb-shell` 名下的滚动与变体规则全部迁到它下面；**8 个工作台页面根**加该类；`.wb-shell` 回归纯主题作用域（不再兼任滚动开关）
- **③ 骨架类作用域化（行为等价）**：`ai-assistant/index.style.css` 的 `.doc-body` 变体限定为 `.ai-workbench .doc-body`（该样式为 scoped，命中元素不变，但不再重定义全局骨架类）
- **② 取值收敛（含 3 处轻微视觉变化）**：新增布局令牌 `--layout-pane-left:280px` · `--layout-ratio-chart:1.5fr 1fr` · `--layout-kpi-cols:repeat(4, minmax(0,1fr))`，10 处使用点改为令牌
  - 变化：工具箱左栏 240→280px · 会话列表 300→280px · 仪表盘图表行 1.4fr→1.5fr
  - 归一：KPI 行统一 `minmax(0,1fr)`（防内容撑破；仅内容溢出时可见差异）
  - **登记例外**：3 项 KPI 行（用例分解页）保留 `auto-fit minmax(180px,1fr)`
- **① 断点体系（仅登记规范，不改值）**：tokens.css 新增「布局」分区，写清断点 3 档（sm 768 / md 1024 / lg 1200）与现状 6 值 → 3 档的映射
  - ⚠️ **技术限制**：CSS media query 内不能使用 `var()`，断点**无法真正令牌化**；改值会改变折叠时机，属需视觉确认项，故本批只登记
- 同步两处因本次改动而失效的注释（`style.css` 策略说明、`TaskDetailPage.vue` 覆盖注释）

## 关联文档

- 无 PRD/ARCH 关联：设计系统批 3 的"零风险半"，依据 = frontend.md CSS 铁律第 3 条
- 承接：`2026-09-11-dead-token-cleanup-and-type-floor`（批 1）· `2026-09-11-tokenize-equal-spacing-and-declare-scroll-policy`（批 2）

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

（无）

> 结构性去歧义 + 令牌化，无需求级行为变化：`.openspec.yaml` 已设 `skip_specs: true`。

## Impact

- 改动 **18 个文件**：tokens.css · style.css · 8 个页面根（device-inspector / device-pool / dashboard / report-generator/index / ai-assistant×4）· `ai-assistant/index.style.css` · SkillViewerPage.style.css · ToolboxPanel.style.css · ChatView.css · DashboardView.style.css · report-generator{index,ReportDetail,TaskReport}.vue · KnowledgeBase.vue
- 验证：
  - postcss 全量 **95 个样式块 → 0 语法错误**（过程修正 1 处：替换 KPI 令牌时**我漏写了分号**，由 postcss 检查抓到并修好）
  - Vite dev server（5173）5/5 改动模块返回 **200**，且 `doc-page--fixed` / `--layout-*` / `.ai-workbench .doc-body` 标识均到位
  - `vue-tsc` **35 条既有错误不变**，与本次改动相关 **0 条**
  - 字号门禁通过
- **登记待办**：断点 6 值 → 3 档（需视觉确认）· 3 项 KPI 行 auto-fit 例外 · 其余同模式多取值（卡片网格 6 种 `minmax`、项目树行内网格 `28px minmax(120px,1fr) 72px 140px 100px`）· App.vue `:deep(.doc-page)` 覆盖导致 `.doc-page` 自身滚动声明失效（已登记偏差，未改）
