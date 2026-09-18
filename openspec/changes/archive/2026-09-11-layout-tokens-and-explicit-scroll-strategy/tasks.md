## 1. 缺口 ④ · 滚动策略显式化（行为等价）

- [x] 1.1 新增 `.doc-page--fixed`（视口固定 + 内层滚动），把 `.doc-page.wb-shell` 的滚动与变体规则迁入；`.wb-shell` 回归纯主题作用域
- [x] 1.2 **8 个页面根**加 `doc-page--fixed`：device-inspector · device-pool · dashboard · report-generator/index · ai-assistant{index, AgentDetail, TaskDetailPage, SkillViewerPage}
- [x] 1.3 验证：`.doc-page--fixed` 命中 15 处（8 页面 + 7 CSS 规则）；`.doc-page.wb-shell` **选择器残留 0**（仅剩已同步的注释文字）
- [x] 1.4 等价性：被匹配元素集合不变（同页面同时保留 `wb-shell`），故**视觉零变化**

## 2. 缺口 ③ · 骨架类作用域化（行为等价）

- [x] 2.1 `ai-assistant/index.style.css` 的 `.doc-body` → `.ai-workbench .doc-body`（附注释说明"限定作用域，避免重定义全局骨架类"）
- [x] 2.2 等价性：该文件为 `<style src scoped>`，scoped 命中元素不变；仅消除"全局骨架类被重定义"的歧义
- [x] 2.3 Vite 检查确认下发 CSS 含 `.ai-workbench .doc-body`

## 3. 缺口 ② · 同模式取值收敛（含 3 处视觉微调）

- [x] 3.1 新增令牌：`--layout-pane-left:280px` · `--layout-ratio-chart:1.5fr 1fr` · `--layout-kpi-cols:repeat(4, minmax(0,1fr))`
- [x] 3.2 左固定栏统一：SkillViewer 280px（等值）· ToolboxPanel 240→**280px** · ChatView 300→**280px**
- [x] 3.3 图表行统一：report-generator/index 1.5fr 1fr（等值）· DashboardView 1.4fr→**1.5fr**
- [x] 3.4 KPI 行统一：report{index, ReportDetail, TaskReport} · KnowledgeBase · TaskDetailPage 五处改 `var(--layout-kpi-cols)`
- [x] 3.5 令牌形态选择：`--layout-kpi-cols` 用**整值**（`repeat(4, minmax(0,1fr))`）而非 `repeat(var(--n),…)`，避免在 `repeat()` 内做变量替换的兼容疑虑
- [x] 3.6 登记例外：用例分解页 3 项 KPI 行保留 `auto-fit minmax(180px,1fr)`

## 4. 缺口 ① · 断点体系（登记规范）

- [x] 4.1 tokens.css 新增「皮肤维度六 · 布局」分区：3 档断点规范（sm 768 / md 1024 / lg 1200）+ 现状 6 值映射
- [x] 4.2 明确技术限制：**media query 内不能用 `var()`** → 断点无法令牌化；本批**只登记不改值**（改值会改变折叠时机，需视觉确认）

## 5. 门禁验证

- [x] 5.1 postcss 全量 `frontend/src` → **95 块 / 0 语法错误**
  - 过程修正：替换 `--layout-kpi-cols` 时我漏写分号（`grid-template-columns:var(--layout-kpi-cols)` 直接接下一行 `gap:`），被 postcss 检查抓到 → 补分号后复检 0 错误
- [x] 5.2 Vite dev server 5 个改动模块全部 **200**，标识符（`doc-page--fixed` / `--layout-*` / `.ai-workbench .doc-body`）均到位
- [x] 5.3 `vue-tsc --noEmit` → 35 条既有错误不变，相关 0 条
- [x] 5.4 `node tests/check-style-gates.mjs` → 通过
- [x] 5.5 同步因本次改动而失效的 2 处注释
