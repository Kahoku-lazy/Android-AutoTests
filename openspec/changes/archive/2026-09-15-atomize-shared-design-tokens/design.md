## Context

本变更只动主 token（共享层），不动模块层与消费点。实测现状：

| 指标 | 实测 |
|---|---|
| `tokens.css` 声明 | 165 条（`:root` 121 · `.ai-workbench` 42 · `.case-workbench` 2） |
| 全仓颜色字面量声明 | 252 条 |
| **唯一色值**（规范化 hex/rgba 后） | **198** |
| **同值重复组** | **34**（最大：`#fff`×5 · `#999`×5 · `rgba(137,207,240,0.16)`×4） |
| `--el-*` 覆盖 | 35 条，其中多条与 `--c-*` / `--app-status-*` 同值直写 |
| 复合值内嵌颜色（阴影/渐变） | 7 处 |

动机见 `proposal.md` - Why；目标架构（T0/T1/T2 边界与职责、数据链、作用域、门禁）见 `dev_docs/05-开发与测试/设计方案与报告/设计方案-前端设计令牌分层与数据链.md`，本设计只落其中的「变更 A」。

## Goals / Non-Goals

**Goals:**
- 建立 T0 四档：颜色原子 / 排版原子 / 基础量原子 / 通用组件配色
- 全部字面量色值收敛为「一个色值一个原子」，主 token 内同值只出现一次字面量
- `--el-*` 覆盖改为引用 T0 原子
- 落地静态门禁 G1（主 token 同值重复 = 0）与 G5（主 token 不出现模块前缀/场景名）

**Non-Goals:**
- 不合并近邻色（会改变视觉）——本仓 198 个唯一色值中大量为近邻，合并需视觉确认，另开变更
- 不新建模块 token 文件、不改模块层与组件层引用（归变更 B）
- 不改管道介质与 SVG/prop/JS 的引用（归变更 C）
- 不改任何色值、字号、间距、圆角、阴影取值（零视觉变化）

## Decisions

### D1 · T0 四档与命名规则

| 档 | 命名 | 示例 |
|----|------|------|
| 颜色 | `--color-<色相>-<明度>[-s<饱和>][-a<透明度>]`；中性 `--color-white` / `--color-black` / `--color-ink-<明度>` | `--color-yellow-65` · `--color-ink-30` · `--color-black-a04` |
| 排版 | `--font-<族>` · `--font-size-<档>` | `--font-mono` · `--font-size-sm` |
| 基础量 | `--space-*` · `--radius-*` · `--shadow-*` · `--duration-*` · `--ease` · `--size-*` | `--space-md` · `--radius-md` · `--size-sidebar-w` |
| 通用组件配色 | `--comp-<组件>-<场景>` | `--comp-card-pin-shadow` |

色相取 12 档（red/orange/yellow/lime/green/teal/cyan/blue/indigo/violet/purple/magenta）；明度为明度百分比按 5 取整后的两位数（05–95）；饱和度仅在「同色相同明度有多值」时补 `s25/s50/s75/s100`；透明度在 <100% 时补 `a05–a99`。

**备选方案（已否决）**：
- 沿用 Material 式 10 档（50…900）：实测同一档位冲突 154 处 —— 本仓配色不是按刻度设计的，弃用
- 直接沿用现有 token 名作为原子名：违反「以颜色命名、不含场景与模块」，弃用
- 一次性改名并全仓替换 ~3000 处引用：与「零视觉变化 + 可回滚」冲突，拆到变更 B/C

### D2 · 保真登记，不合并近邻色

规范化后 198 个唯一色值，其中 61 个在命名上仍需序号兜底、43 个色相-明度组含多值 —— 这是本仓配色未按刻度设计的证据。本变更只登记，不合并；合并标准（ΔE 阈值、用途是否相同）需视觉确认，列入 Open Questions。

### D3 · 旧名保留为别名（零视觉变化 + 可回滚）

`tokens.css` 内现有场景名/模块名声明改为 `var(--color-…)` 别名，声明名不变 → 消费点（含 JS 字符串、模板内联 style、SVG 属性、prop 传色）**零改动**，视觉零变化。别名归位到 T1/通用组件档由变更 B 承担。

### D4 · `--el-*` 覆盖引用原子

35 条 `--el-*` 的值改为 `var(--color-*)`；Element Plus 变量因此不再是第二真相源。选择理由：EP 覆盖与主题令牌同值是重复的一致性问题高发区（实测 `--el-color-primary` 与 `--c-dashboard` 同值）。

### D5 · 复合值内嵌颜色暂留字面量并登记

7 处阴影/渐变内嵌色（如 `0 2px 8px rgba(30,30,36,0.15)`）本阶段保留字面量，但列入登记清单；后续可改写为 `0 2px 8px var(--color-ink-a15)`。选择理由：CSS 允许 `var()` 内嵌于 shadow/渐变，但改写面涉及组件层，归变更 B/C。

### D6 · 门禁落点

落在既有 `frontend/tests/check-style-gates.mjs`（已有字号刻度门禁先例），新增三条自动检查：

1. **G1**：主 token 内同一色值的字面量声明恰好 1 次（否则报出重复组）
2. **G5**：主 token 的原子声明名不得匹配 `/^--(ai|case|rg|di|wf|views)-/`。`--el-*` 是 Element Plus 框架变量名，必须保留原名、只把值改为 `var()`；`--app-*` 中遗留的场景名别名在本变更内保留，其归位与删除由变更 B 负责，门禁对此只输出**存量清单**（计数只降不增）
3. **引用存在性**：任何 `var(--color-*)` 的引用必须能在主 token 中找到声明（防 EP 覆盖改为 `var()` 后静默回退）

### D7 · 作用域不变

T0 全部声明在 `:root`（含通用组件档）；模块层作用域问题不在本变更范围（变更 B 沿用「模块页面根类 + Teleport 目标声明在元素自身根类」口径，依据 EP 2.7 `el-dialog` 默认不 Teleport）。

## 数据链与作用域

```text
T0 主 token（本变更唯一改动面，:root）
   --color-* / --font* / --space-* / --radius-* / --shadow-* / --comp-*
        │  var() 引用（单向）
        ▼
T0 别名层（本变更临时保留：--app-status-* / --c-* / --el-* = var(原子)）
        │  消费点零改动
        ▼
T1 模块 token（变更 B）→ T2 组件样式（变更 B/C）
```

完整作用域表见方案文档 §4；本变更不新增作用域。

## 模块防火墙自检

| 红线 | 本变更 |
|------|--------|
| 跨 App import（仅 Model 只读 / api.py） | 不涉及：改动面全在 `frontend/src/**` 样式声明与 `frontend/tests`，无 Python 侧改动 |
| 禁止跨 App import service/runner/consumer/state_machine | 不涉及 |
| 写库收敛到各 App api.py | 不涉及：无 ORM 访问 |
| 前端不直连数据库、仪表盘不做写操作 | 不涉及：无数据访问，仅 CSS 变量声明 |
| 新增跨模块依赖 | 无新增依赖（不新增 npm 包，不改 vue/vite 配置） |

## Risks / Trade-offs

- [198 个唯一色值远超健康令牌量（约 30–60），属配色未刻度化] → 保真登记 + 附录列出近邻组；合并另开变更（需视觉确认）
- [旧名别名会长期存在，可能被误认为真相源] → 每条别名声明处统一注释 `/* alias → var(--color-…) */`，并在 spec 中明确 T0 原子为唯一真相源；变更 B 负责删除别名
- [T0 出现 `-2`/`-3` 序号兜底名] → 仅 61 个，附录可逐条复核；根治方式同近邻色合并
- [零视觉变化缺少构建级验证] → `vite build` 被沙箱拦（spawn EPERM）；改以「值等价静态校验（原子值 = 别名值原字面量）+ `vue-tsc --noEmit`（基线 34 条 tests 错误 / 应用代码 0）+ 人工 diff」三重核验，构建验证留待环境可用
- [EP 覆盖改为 var() 后若原子缺失会静默回退] → 门禁增加「`var(--color-*)` 引用必须存在于 T0」的检查

## Migration Plan

1. 生成原子表（脚本产出，见附录）—— 已完成于 `temps/atom-mapping-colors.md`
2. 在 `tokens.css` 新增 T0 四档原子（纯新增，不动旧名）→ 此步结束时视觉与引用均无变化
3. 旧名值改为 `var(原子)`（同值去重在此步完成）
4. `--el-*` 值改为 `var(原子)`
5. 落地 G1/G5 门禁并跑验证；`vue-tsc --noEmit` 与基线对比
6. **回滚**：改动集中在 `tokens.css` + `check-style-gates.mjs`，`git revert` 单次提交即可；无消费点改动，回滚无连锁风险

## Open Questions

- 近邻色合并的判据（ΔE 阈值？同用途？）与批次 —— 不影响本变更的原子命名与门禁，可在变更 B 期间评估
- 通用组件档与「外壳/骨架」档是否合并（方案文档 §8-4）—— 不影响原子命名，可延后
- 复合值内嵌颜色是否改写为 `var()` —— 涉及组件层，归变更 B/C

## 附录 A · 颜色原子映射表（198 个唯一色值，脚本生成）

| 现值（字面量） | 目标原子名 | HSL(h/s/l) | 现行声明（token@文件:行） |
|---|---|---|---|
| `rgba(0, 0, 0, 0.03)` | `--color-black-a03` | 0° / 0% / 0% | --skeleton-shimmer-faint@SkeletonCard.vue:30 |
| `rgba(0,0,0,0.04)` | `--color-black-a04` | 0° / 0% / 0% | --rg-shadow-soft@ReportDetail.vue:437 · --rg-shadow-soft@index.vue:371 |
| `rgba(0, 0, 0, 0.05)` | `--color-black-a05` | 0° / 0% / 0% | --wf-btn-press-shadow@index.vue:486 · --wf-btn-press-shadow@WorkflowFileBrowser.vue:276 · --wf-btn-press-shadow@PageFlowVueFlow.vue:595 |
| `rgba(0, 0, 0, 0.06)` | `--color-black-a06` | 0° / 0% / 0% | --skeleton-shimmer-base@SkeletonCard.vue:31 |
| `rgba(0, 0, 0, 0.08)` | `--color-black-a08` | 0° / 0% / 0% | --screenshot-pin-shadow-color@ScreenshotView.css:7 |
| `rgba(0, 0, 0, 0.12)` | `--color-black-a12` | 0° / 0% / 0% | --screenshot-img-shadow-color@ScreenshotView.css:8 · --kpi-pin-shadow@KpiCard.vue:155 |
| `rgba(0, 0, 0, 0.15)` | `--color-black-a15` | 0° / 0% / 0% | --ac-pin-shadow@workbench-theme.css:33 |
| `rgba(0, 0, 0, 0.25)` | `--color-black-a25` | 0° / 0% / 0% | --pep-enlarge-shadow-color@PageElementsPanel.vue:229 · --sap-enlarge-shadow-color@StructureAnalysisPanel.vue:238 |
| `rgba(0, 0, 0, 0.38)` | `--color-black-a38` | 0° / 0% / 0% | --app-overlay@tokens.css:81 |
| `#1a3a6a` | `--color-blue-25` | 216° / 61% / 26% | --app-pending-text@tokens.css:57 |
| `#1a4a73` | `--color-blue-30` | 208° / 63% / 28% | --case-sheet-head-fg@CaseFileSheet.vue:426 |
| `#4a5a8a` | `--color-blue-40-s25` | 225° / 30% / 42% | --ai-status-conn-text@tokens.css:284 |
| `#2a6f96` | `--color-blue-40-s50` | 202° / 56% / 38% | --tag-web-fg@CaseFileSheet.vue:526 |
| `#2f6ea3` | `--color-blue-40-s50-2` | 207° / 55% / 41% | --ac-accent-deep@workbench-theme.css:19 · --wf-nodemenu-hint@NodeContextMenu.vue:236 |
| `#4a6ad4` | `--color-blue-55` | 226° / 62% / 56% | --wf-node-in-count-fg@PageFlowNode.vue:246 |
| `#3b82f6` | `--color-blue-60-s100` | 217° / 91% / 60% | --td-flow-blue@TaskDetailPage.vue:307 |
| `#7889c4` | `--color-blue-60-s50` | 227° / 39% / 62% | --ai-status-conn-border@tokens.css:285 |
| `#6c80d4` | `--color-blue-65-s50` | 228° / 55% / 63% | --ai-status-blue-border@tokens.css:273 |
| `#6f9fd8` | `--color-blue-65-s50-2` | 213° / 57% / 64% | --wf-picker-accent@PageFlowVueFlow.vue:781 |
| `#5fa8e8` | `--color-blue-65-s75` | 208° / 75% / 64% | --ss-type-input@StepScreenshotPanel.vue:131 |
| `#60a5fa` | `--color-blue-70` | 213° / 94% / 68% | --wb-icon-gradient-end@WorkbenchHeader.vue:65 |
| `#89CFF0` | `--color-blue-75-s75` | 199° / 77% / 74% | --c-workflow@tokens.css:34 · --el-color-info@tokens.css:191 |
| `rgba(137, 207, 240, 0.12)` | `--color-blue-75-s75-a12` | 199° / 77% / 74% | --ai-dot-grid@index.style.css:58 |
| `rgba(137, 207, 240, 0.16)` | `--color-blue-75-s75-a16` | 199° / 77% / 74% | --ac-accent-soft@workbench-theme.css:20 · --wf-ctx-hover-bg@WorkflowDirTree.vue:668 · --wf-edge-hover-bg@EdgeContextMenu.vue:124 · 等 4 处 |
| `rgba(136, 157, 240, 0.2)` | `--color-blue-75-s75-a20` | 228° / 78% / 74% | --wf-node-in-count-bg@PageFlowNode.vue:247 |
| `rgba(137, 207, 240, 0.28)` | `--color-blue-75-s75-a28` | 199° / 77% / 74% | --wf-node-selected-ring@PageFlowNode.vue:243 |
| `rgba(137, 207, 240, 0.4)` | `--color-blue-75-s75-a40` | 199° / 77% / 74% | --wf-status-pill-border@index.vue:487 |
| `#a2d2ff` | `--color-blue-80-s100` | 209° / 100% / 82% | --wf-picker-focus@PageFlowVueFlow.vue:784 |
| `rgba(162, 210, 255, 0.12)` | `--color-blue-80-s100-a12` | 209° / 100% / 82% | --wf-picker-item-hover-bg@PageFlowVueFlow.vue:786 |
| `rgba(162, 210, 255, 0.14)` | `--color-blue-80-s100-a14` | 209° / 100% / 82% | --wf-picker-tint-soft@PageFlowVueFlow.vue:783 |
| `rgba(162, 210, 255, 0.16)` | `--color-blue-80-s100-a16` | 209° / 100% / 82% | --wf-picker-count-bg@PageFlowVueFlow.vue:782 |
| `rgba(162, 210, 255, 0.18)` | `--color-blue-80-s100-a18` | 209° / 100% / 82% | --case-border-subtle@tokens.css:298 · --chat-count-tint@ChatView.css:5 · --wf-picker-add-bg@PageFlowVueFlow.vue:789 |
| `rgba(162, 210, 255, 0.22)` | `--color-blue-80-s100-a22` | 209° / 100% / 82% | --wf-picker-item-border@PageFlowVueFlow.vue:785 |
| `rgba(162, 210, 255, 0.24)` | `--color-blue-80-s100-a24` | 209° / 100% / 82% | --case-border@tokens.css:299 · --wf-picker-head-border@PageFlowVueFlow.vue:780 |
| `rgba(162, 210, 255, 0.3)` | `--color-blue-80-s100-a30` | 209° / 100% / 82% | --wf-node-handle-ring@PageFlowNode.vue:248 |
| `rgba(162, 210, 255, 0.72)` | `--color-blue-80-s100-a72` | 209° / 100% / 82% | --wb-select-ring-color@motion.css:43 |
| `#9ec9f0` | `--color-blue-80-s75` | 209° / 73% / 78% | --case-sheet-head-border@CaseFileSheet.vue:427 |
| `#b8e4f8` | `--color-blue-85` | 199° / 82% / 85% | --wf-header-icon-end@PrototypeList.vue:152 |
| `#D4E8FF` | `--color-blue-90-s100` | 212° / 100% / 92% | --app-pending@tokens.css:56 |
| `#d6ebff` | `--color-blue-90-s100-2` | 209° / 100% / 92% | --case-sheet-head-bg@CaseFileSheet.vue:425 |
| `#eef8ff` | `--color-blue-95-s100` | 205° / 100% / 97% | --note-status-run-bg@DoodleNote.vue:110 |
| `#f0f4ff` | `--color-blue-95-s100-2` | 224° / 100% / 97% | --ai-status-blue-bg@tokens.css:271 |
| `rgba(238, 247, 255, 0.45)` | `--color-blue-95-s100-a45` | 208° / 100% / 97% | --chat-body-grad-to@ChatView.css:7 |
| `#e8ecf1` | `--color-blue-95-s25` | 213° / 24% / 93% | --app-border-light@tokens.css:76 |
| `#eef0f7` | `--color-blue-95-s25-2` | 227° / 36% / 95% | --ai-status-conn-bg@tokens.css:283 |
| `#E8F4FD` | `--color-blue-95-s75` | 206° / 84% / 95% | --app-page-active-bg@tokens.css:91 |
| `#e8f6fc` | `--color-blue-95-s75-2` | 198° / 77% / 95% | --tag-web-bg@CaseFileSheet.vue:526 |
| `#0d8a80` | `--color-cyan-30-s75` | 175° / 83% / 30% | --nav-save-teal-deep@AgentFormFooter.vue:21 |
| `#158a80` | `--color-cyan-30-s75-2` | 175° / 74% / 31% | --ai-teal-text@tokens.css:258 |
| `#1a7a74` | `--color-cyan-30-s75-3` | 176° / 65% / 29% | --tag-app-fg@CaseFileSheet.vue:525 |
| `#15a89c` | `--color-cyan-35` | 175° / 78% / 37% | --ai-teal-hover@tokens.css:259 |
| `#17b3a6` | `--color-cyan-40` | 175° / 77% / 40% | --mascot-stroke@AnimatedMascot.vue:112 |
| `#19c8b9` | `--color-cyan-45-s75` | 175° / 78% / 44% | --ai-teal@tokens.css:256 · --mascot-teal@AnimatedMascot.vue:110 |
| `rgba(25, 200, 185, 0.35)` | `--color-cyan-45-s75-a35` | 175° / 78% / 44% | --nav-save-glow@AgentFormFooter.vue:22 |
| `#4ECDC4` / `#4ecdc4` | `--color-cyan-55` | 176° / 56% / 55% | --c-case@tokens.css:30 · --paper-mark-teal@PaperDoodles.vue:110 |
| `#1a5c2a` | `--color-green-25` | 135° / 56% / 23% | --app-pass-text@tokens.css:53 |
| `#2a7a2a` | `--color-green-30` | 120° / 49% / 32% | --ai-status-green-text@tokens.css:281 |
| `#2d7a2d` | `--color-green-35-s50` | 120° / 46% / 33% | --app-status-success-text@tokens.css:39 |
| `#2f7a3d` | `--color-green-35-s50-2` | 131° / 44% / 33% | --tag-appliance-fg@CaseFileSheet.vue:529 |
| `#6fba2c` | `--color-green-45-s50` | 92° / 62% / 45% | --ss-type-assert@StepScreenshotPanel.vue:132 |
| `rgba(111,186,44,0.1)` | `--color-green-45-s50-a10` | 92° / 62% / 45% | --rg-status-pass-bg@TaskReport.vue:339 |
| `#4caf50` | `--color-green-50` | 122° / 39% / 49% | --ai-status-green-border@tokens.css:282 |
| `rgba(122, 184, 141, 0.45)` | `--color-green-60-s25-a45` | 138° / 30% / 60% | --chat-empty-dash@ChatView.css:4 |
| `#6BCB77` | `--color-green-60-s50` | 128° / 48% / 61% | --c-device@tokens.css:28 · --app-status-success@tokens.css:37 · --el-color-success@tokens.css:188 |
| `#C8F5D0` | `--color-green-85` | 131° / 69% / 87% | --app-status-success-bg@tokens.css:38 · --app-pass@tokens.css:52 |
| `#e6f5e6` | `--color-green-95-s50` | 120° / 43% / 93% | --ai-status-green-bg@tokens.css:280 |
| `#e9f8ec` | `--color-green-95-s50-2` | 132° / 52% / 94% | --tag-appliance-bg@CaseFileSheet.vue:529 |
| `rgba(74, 78, 105, 0.12)` | `--color-indigo-35-s25-a12` | 232° / 17% / 35% | --wf-picker-shadow@PageFlowVueFlow.vue:779 |
| `rgba(74, 78, 105, 0.26)` | `--color-indigo-35-s25-a26` | 232° / 17% / 35% | --wf-picker-mask@PageFlowVueFlow.vue:775 |
| `#5b4aa8` | `--color-indigo-45` | 251° / 39% / 47% | --tag-api-fg@CaseFileSheet.vue:527 |
| `#4256b8` | `--color-indigo-50` | 230° / 47% / 49% | --ai-status-blue-text@tokens.css:272 |
| `#c4b5fd` | `--color-indigo-85` | 252° / 95% / 85% | --locator-header-icon-end@ProjectWorkspace.vue:106 · --locator-header-icon-end@ProjectList.vue:73 · --locator-header-icon-end@LocatorFileView.vue:145 |
| `#1e1e24` | `--color-ink-15` | 240° / 9% / 13% | --ink@tokens.css:22 |
| `rgba(30, 30, 36, 0.15)` | `--color-ink-15-a15` | 240° / 9% / 13% | --case-menu-shadow@ProjectTree.vue:691 · --case-menu-shadow@CaseFileSheet.vue:571 · --kpi-icon-shadow@KpiCard.vue:157 |
| `rgba(30, 30, 36, 0.25)` | `--color-ink-15-a25` | 240° / 9% / 13% | --note-tape-border@DoodleNote.vue:112 · --kpi-tape-border@KpiCard.vue:156 |
| `#5a5547` | `--color-ink-30` | 44° / 12% / 32% | --app-nav-text@tokens.css:73 |
| `#5f5d59` | `--color-ink-35` | 40° / 3% / 36% | --app-stat-text@tokens.css:106 |
| `#6b7280` | `--color-ink-45` | 220° / 9% / 46% | --td-neutral-ink@TaskDetailPage.vue:306 |
| `#7C6F83` | `--color-ink-45-2` | 279° / 8% / 47% | --c-report@tokens.css:32 |
| `#888` | `--color-ink-55` | 0° / 0% / 53% | --dbtn-disabled-ink@DoodleBtn.vue:52 |
| `#8e8e8e` | `--color-ink-55-2` | 0° / 0% / 56% | --ss-type-other@StepScreenshotPanel.vue:135 |
| `#999` | `--color-ink-60` | 0° / 0% / 60% | --ac-wood-light@workbench-theme.css:11 · --ac-ink-muted@workbench-theme.css:14 · --app-text-secondary@tokens.css:70 · 等 5 处 |
| `#9e9e9e` | `--color-ink-60-2` | 0° / 0% / 62% | --ss-type-nav@StepScreenshotPanel.vue:133 |
| `#bbb` | `--color-ink-75` | 0° / 0% / 73% | --ac-wood-soft@workbench-theme.css:12 · --ac-ink-faint@workbench-theme.css:15 · --app-text-muted@tokens.css:71 |
| `#ccc` | `--color-ink-80` | 0° / 0% / 80% | --app-btn-disabled-color@tokens.css:90 |
| `#d4d8dc` | `--color-ink-85` | 210° / 10% / 85% | --app-offline@tokens.css:59 · --tb-unarmed-border@ToolboxPanel.style.css:6 |
| `#f5f5f5` | `--color-ink-95` | 0° / 0% / 96% | --ai-bg-neutral@tokens.css:267 |
| `rgba(235, 237, 238, 0.58)` | `--color-ink-95-a58` | 200° / 8% / 93% | --wf-picker-used-bg@PageFlowVueFlow.vue:787 |
| `#4a3a28` | `--color-orange-20` | 32° / 30% / 22% | --ai-ink-soft@tokens.css:262 · --mascot-ink@AnimatedMascot.vue:115 |
| `#a36600` | `--color-orange-30-s100` | 38° / 100% / 32% | --ai-status-orange-text@tokens.css:278 |
| `#5c4b38` | `--color-orange-30-s25` | 32° / 24% / 29% | --ai-ink-subtle@tokens.css:264 |
| `rgba(121, 79, 39, 0.05)` | `--color-orange-30-s50-a05` | 29° / 51% / 31% | --kb-filter-bg@KnowledgeBase.vue:256 |
| `rgba(121, 79, 39, 0.06)` | `--color-orange-30-s50-a06` | 29° / 51% / 31% | --kb-md-code-bg@KnowledgePreviewDrawer.vue:61 |
| `#7a4f2e` | `--color-orange-35` | 26° / 45% / 33% | --paper-mark-brown@PaperDoodles.vue:107 |
| `#7a6b5a` | `--color-orange-40-s25` | 32° / 15% / 42% | --wf-picker-xpath@PageFlowVueFlow.vue:788 |
| `#b9770e` | `--color-orange-40-s75` | 37° / 86% / 39% | --wf-api-btn-fg@PageFlowVueFlow.vue:596 |
| `#ba7517` | `--color-orange-40-s75-2` | 35° / 78% / 41% | --ai-hint-orange@tokens.css:268 |
| `#8a7b66` | `--color-orange-45` | 35° / 15% / 47% | --eval-quiet-ink@EvaluatorTab.vue:551 · --kb-tree-dir-ink@KbTreeView.vue:112 |
| `rgba(245, 166, 35, 0.08)` | `--color-orange-55-s100-a08` | 37° / 91% / 55% | --wf-node-api-bg@PageFlowNode.vue:245 |
| `rgba(245, 166, 35, 0.12)` | `--color-orange-55-s100-a12` | 37° / 91% / 55% | --wf-api-btn-hover-bg@PageFlowVueFlow.vue:598 |
| `rgba(245, 166, 35, 0.16)` | `--color-orange-55-s100-a16` | 37° / 91% / 55% | --wf-node-api-glow@PageFlowNode.vue:244 |
| `rgba(245, 166, 35, 0.5)` | `--color-orange-55-s100-a50` | 37° / 91% / 55% | --wf-api-btn-border@PageFlowVueFlow.vue:597 |
| `#988b7a` | `--color-orange-55-s25` | 34° / 13% / 54% | --ai-status-warm-text@tokens.css:287 |
| `#a09080` | `--color-orange-55-s25-2` | 30° / 14% / 56% | --app-pushpin-dark@tokens.css:94 |
| `#e0a13a` | `--color-orange-55-s75` | 37° / 73% / 55% | --ai-status-orange-border@tokens.css:279 |
| `#d8a870` | `--color-orange-65-s50` | 32° / 57% / 64% | --el-button-border-color@motion.css:10 |
| `#f0a050` | `--color-orange-65-s75` | 30° / 84% / 63% | --ss-type-wait@StepScreenshotPanel.vue:134 |
| `#F0C090` | `--color-orange-75` | 30° / 76% / 75% | --el-button-bg-color@motion.css:9 |
| `#f5cda0` | `--color-orange-80` | 32° / 81% / 79% | --el-button-hover-bg-color@motion.css:12 |
| `#e8e0d5` | `--color-orange-85` | 35° / 29% / 87% | --app-pushpin-light@tokens.css:93 |
| `#fff5e6` | `--color-orange-95-s100` | 36° / 100% / 95% | --ai-status-orange-bg@tokens.css:277 |
| `#f0ede8` | `--color-orange-95-s25` | 38° / 21% / 93% | --app-border-lighter@tokens.css:77 |
| `#9a3aad` | `--color-purple-45` | 290° / 50% / 45% | --tag-biz-app-fg@CaseFileSheet.vue:531 |
| `#9448b3` | `--color-purple-50` | 283° / 43% / 49% | --ai-status-purple-text@tokens.css:275 |
| `#C050D0` | `--color-purple-55` | 293° / 58% / 56% | --el-color-primary-dark-2@tokens.css:253 |
| `#c97adb` | `--color-purple-65` | 289° / 57% / 67% | --ai-status-purple-border@tokens.css:276 |
| `#E879F9` | `--color-purple-75` | 292° / 91% / 73% | --c-ai@tokens.css:33 · --el-color-primary@tokens.css:247 |
| `#F0A0FA` | `--color-purple-80` | 293° / 90% / 80% | --el-color-primary-light-3@tokens.css:248 |
| `#F5C0FB` | `--color-purple-85` | 294° / 88% / 87% | --el-color-primary-light-5@tokens.css:249 |
| `#FAD8FC` | `--color-purple-90` | 297° / 86% / 92% | --el-color-primary-light-7@tokens.css:250 |
| `#fce8ff` | `--color-purple-95-s100` | 292° / 100% / 95% | --tag-biz-app-bg@CaseFileSheet.vue:531 |
| `#fef0ff` | `--color-purple-95-s100-2` | 296° / 100% / 97% | --ai-status-purple-bg@tokens.css:274 |
| `#FCE8FD` | `--color-purple-95-s75` | 297° / 84% / 95% | --el-color-primary-light-8@tokens.css:251 |
| `#FEF4FE` | `--color-purple-95-s75-2` | 300° / 83% / 98% | --el-color-primary-light-9@tokens.css:252 |
| `#7a1c1c` | `--color-red-30` | 0° / 63% / 29% | --app-fail-text@tokens.css:55 |
| `#a03030` | `--color-red-40` | 0° / 54% / 41% | --app-status-danger-text@tokens.css:42 |
| `#b35a48` | `--color-red-50-s50` | 10° / 43% / 49% | --tag-lighting-fg@CaseFileSheet.vue:530 |
| `#c43f3f` | `--color-red-50-s50-2` | 0° / 53% / 51% | --ai-status-danger-text@tokens.css:291 |
| `#e85f5f` | `--color-red-65-s75` | 0° / 75% / 64% | --app-error@tokens.css:60 · --ai-status-danger@tokens.css:289 |
| `rgba(232,95,95,0.12)` | `--color-red-65-s75-a12` | 0° / 75% / 64% | --rg-status-fail-bg@TaskReport.vue:339 |
| `#f87171` | `--color-red-70-s100` | 0° / 91% / 71% | --app-live@tokens.css:58 |
| `#fc736d` | `--color-red-70-s100-2` | 3° / 96% / 71% | --mascot-antenna-tip@AnimatedMascot.vue:113 |
| `#ff6b6b` | `--color-red-70-s100-3` | 0° / 100% / 71% | --app-marker-red@tokens.css:49 · --paper-mark-red@PaperDoodles.vue:109 |
| `rgba(248, 113, 113, 0)` | `--color-red-70-s100-a00` | 0° / 91% / 71% | --kpi-live-pulse-fade@KpiCard.vue:161 |
| `rgba(248, 113, 113, 0.4)` | `--color-red-70-s100-a40` | 0° / 91% / 71% | --kpi-live-pulse@KpiCard.vue:160 |
| `#e8998a` | `--color-red-75` | 10° / 67% / 73% | --ac-red@workbench-theme.css:27 |
| `#e8b0b0` | `--color-red-80` | 0° / 55% / 80% | --rg-issue-badge-border@CaseBreakdown.vue:508 |
| `#FFB5A7` | `--color-red-85-s100` | 10° / 100% / 83% | --c-runner@tokens.css:31 · --app-status-danger@tokens.css:40 · --el-color-danger@tokens.css:190 |
| `#f0c0c0` | `--color-red-85-s50` | 0° / 62% / 85% | --rg-issue-head-border@CaseBreakdown.vue:501 |
| `#FFD0C8` | `--color-red-90` | 9° / 100% / 89% | --app-btn-hover-danger@tokens.css:89 |
| `#fde0e0` | `--color-red-95-s100` | 0° / 88% / 94% | --ai-status-danger-hover@tokens.css:292 |
| `#fef0f0` | `--color-red-95-s100-2` | 0° / 88% / 97% | --ai-status-danger-bg@tokens.css:290 |
| `#FFE0DB` | `--color-red-95-s100-3` | 8° / 100% / 93% | --app-status-danger-bg@tokens.css:41 · --app-fail@tokens.css:54 |
| `#ffe8e8` | `--color-red-95-s100-4` | 0° / 100% / 95% | --note-status-fail-bg@DoodleNote.vue:109 |
| `#fff0ec` | `--color-red-95-s100-5` | 13° / 100% / 96% | --tag-lighting-bg@CaseFileSheet.vue:530 |
| `#fff0f0` | `--color-red-95-s100-6` | 0° / 100% / 97% | --app-error-bg@tokens.css:61 |
| `#1a7a5c` | `--color-teal-30` | 161° / 65% / 29% | --stats-card-trend-text@StatsCard.vue:140 |
| `#3dd4c6` | `--color-teal-55` | 174° / 64% / 54% | --mascot-teal-light@AnimatedMascot.vue:111 |
| `#6ee7d8` | `--color-teal-65` | 173° / 72% / 67% | --case-icon-accent@ProjectWorkspace.vue:116 · --case-icon-accent@ProjectList.vue:151 · --case-icon-accent@CaseFileSheet.vue:405 |
| `#e2ece9` | `--color-teal-90` | 162° / 21% / 91% | --wb-loader-dot-3@motion.css:28 |
| `#e6f9f6` | `--color-teal-95-s50` | 171° / 61% / 94% | --ai-teal-bg@tokens.css:257 |
| `#e6faf8` | `--color-teal-95-s75` | 174° / 67% / 94% | --tag-app-bg@CaseFileSheet.vue:525 |
| `#e8fbf8` | `--color-teal-95-s75-2` | 171° / 70% / 95% | --note-status-ok-bg@DoodleNote.vue:108 |
| `#5a3fa0` | `--color-violet-45` | 257° / 43% / 44% | --app-status-purple-text@tokens.css:45 |
| `#A78BFA` | `--color-violet-75-s100` | 255° / 92% / 76% | --c-element@tokens.css:29 · --app-status-purple-border@tokens.css:46 |
| `#c084fc` | `--color-violet-75-s100-2` | 270° / 95% / 75% | --td-icon-grad-end@TaskDetailPage.vue:308 · --sv-icon-grad-end@SkillViewerPage.style.css:5 |
| `rgba(167, 139, 250, 0.18)` | `--color-violet-75-s100-a18` | 255° / 92% / 76% | --sap-row-selected-bg@StructureAnalysisPanel.vue:237 |
| `#D4C8F0` | `--color-violet-85-s50` | 258° / 57% / 86% | --app-btn-hover-purple@tokens.css:88 |
| `#C9B6F2` | `--color-violet-85-s75` | 259° / 70% / 83% | --app-status-purple@tokens.css:43 |
| `#E8DDF8` | `--color-violet-90` | 264° / 66% / 92% | --app-status-purple-bg@tokens.css:44 |
| `#F0E8FF` | `--color-violet-95-s100` | 261° / 100% / 95% | --app-icon-purple-bg@tokens.css:84 |
| `#f1ebff` | `--color-violet-95-s100-2` | 258° / 100% / 96% | --tag-api-bg@CaseFileSheet.vue:527 |
| `#fff` / `#ffffff` | `--color-white` | 0° / 0% / 100% | --ac-paper@workbench-theme.css:9 · --app-bg-card@tokens.css:64 · --app-bg-input@tokens.css:65 · 等 8 处 |
| `rgba(255, 255, 255, 0.35)` | `--color-white-a35` | 0° / 0% / 100% | --chat-body-grad-from@ChatView.css:6 |
| `rgba(255, 255, 255, 0.55)` | `--color-white-a55` | 0° / 0% / 100% | --dot-board-inner-glow@index.style.css:59 |
| `rgba(255, 255, 255, 0.68)` | `--color-white-a68` | 0° / 0% / 100% | --wf-picker-border@PageFlowVueFlow.vue:778 |
| `rgba(255, 255, 255, 0.85)` | `--color-white-a85` | 0° / 0% / 100% | --kpi-shape-border@KpiCard.vue:158 |
| `#8a6a00` | `--color-yellow-25-s100` | 46° / 100% / 27% | --tag-func-fg@CaseFileSheet.vue:528 |
| `#5a4e20` | `--color-yellow-25-s50` | 48° / 48% / 24% | --app-footer-yellow-text@tokens.css:92 |
| `#7a5a10` | `--color-yellow-25-s75` | 42° / 77% / 27% | --app-warning-text@tokens.css:86 |
| `#b08800` | `--color-yellow-35` | 46° / 100% / 35% | --app-queue-text@tokens.css:87 |
| `#D4A830` | `--color-yellow-50` | 44° / 66% / 51% | --el-color-primary-dark-2@tokens.css:186 |
| `#a0936e` | `--color-yellow-55` | 44° / 21% / 53% | --ai-ink-muted@tokens.css:263 |
| `#ffd93d` | `--color-yellow-60` | 48° / 100% / 62% | --paper-mark-yellow@PaperDoodles.vue:108 |
| `#F7C948` | `--color-yellow-65` | 44° / 92% / 63% | --c-dashboard@tokens.css:27 · --el-color-primary@tokens.css:180 · --el-color-warning@tokens.css:189 |
| `#F9D870` | `--color-yellow-70-s100` | 46° / 92% / 71% | --el-color-primary-light-3@tokens.css:181 |
| `#FFE066` | `--color-yellow-70-s100-2` | 48° / 100% / 70% | --app-highlight@tokens.css:78 |
| `#c0b8a8` | `--color-yellow-70-s25` | 40° / 16% / 71% | --app-pushpin-mid@tokens.css:95 |
| `#cfc9bb` | `--color-yellow-75-s25` | 42° / 17% / 77% | --case-sheet-grid@CaseFileSheet.vue:424 |
| `#d0c8b8` | `--color-yellow-75-s25-2` | 40° / 20% / 77% | --ai-status-warm-border@tokens.css:288 |
| `#FBE898` | `--color-yellow-80-s100` | 48° / 93% / 79% | --el-color-primary-light-5@tokens.css:182 |
| `#d8d2c4` | `--color-yellow-80-s25` | 42° / 20% / 81% | --dot@tokens.css:24 |
| `#FDF0C0` | `--color-yellow-85-s100` | 47° / 94% / 87% | --el-color-primary-light-7@tokens.css:183 |
| `#e8e2d6` | `--color-yellow-85-s25` | 40° / 28% / 87% | --ai-warm-border@tokens.css:261 |
| `#FEF6D8` | `--color-yellow-90-s100` | 47° / 95% / 92% | --el-color-primary-light-8@tokens.css:184 |
| `#e8e4d8` | `--color-yellow-90-s25` | 45° / 26% / 88% | --ac-border-soft@workbench-theme.css:17 · --el-border-color-light@tokens.css:208 |
| `#ecece6` | `--color-yellow-90-s25-2` | 60° / 14% / 91% | --dbtn-disabled-bg@DoodleBtn.vue:51 |
| `#f0ebe0` | `--color-yellow-90-s25-3` | 41° / 35% / 91% | --ai-bg-subtle@tokens.css:266 |
| `#fff8db` | `--color-yellow-95-s100` | 48° / 100% / 93% | --tag-func-bg@CaseFileSheet.vue:528 |
| `#FFF9E0` | `--color-yellow-95-s100-2` | 48° / 100% / 94% | --app-status-warning-bg@tokens.css:47 |
| `#FFFBE8` | `--color-yellow-95-s100-3` | 50° / 100% / 95% | --el-color-primary-light-9@tokens.css:185 |
| `#fffef5` | `--color-yellow-95-s100-4` | 54° / 100% / 98% | --paper@tokens.css:23 |
| `#fffef8` | `--color-yellow-95-s100-5` | 51° / 100% / 99% | --ai-sticky-bg@tokens.css:265 |
| `#f5f3ed` | `--color-yellow-95-s25` | 45° / 29% / 95% | --ai-status-warm-bg@tokens.css:286 |
| `#f8f6f2` | `--color-yellow-95-s25-2` | 40° / 30% / 96% | --app-bg-subtle@tokens.css:66 · --el-fill-color-light@tokens.css:197 |
| `#f8f8f0` | `--color-yellow-95-s25-3` | 60° / 36% / 96% | --mascot-screen@AnimatedMascot.vue:114 |
| `#faf9f4` | `--color-yellow-95-s25-4` | 50° / 37% / 97% | --ai-warm-bg@tokens.css:260 |
| `#fefdfb` | `--color-yellow-95-s50` | 40° / 60% / 99% | --rg-hover-bg@ReportDetail.vue:437 · --rg-hover-bg@index.vue:371 |

## 附录 B · 同值重复清单（34 组，去重目标）

| 现值（规范化） | 重复处数 | 涉及声明 |
|---|---|---|
| `rgba(255,255,255,1)` | 8 | --ac-paper@workbench-theme.css:9 · --app-bg-card@tokens.css:64 · --app-bg-input@tokens.css:65 · --app-text-inverse@tokens.css:72 · --el-bg-color-overlay@tokens.css:194 · --el-fill-color-blank@tokens.css:196 · --el-button-text-color@motion.css:11 · --el-button-hover-text-color@motion.css:13 |
| `rgba(153,153,153,1)` | 5 | --ac-wood-light@workbench-theme.css:11 · --ac-ink-muted@workbench-theme.css:14 · --app-text-secondary@tokens.css:70 · --app-timeline-dot@tokens.css:85 · --el-text-color-secondary@tokens.css:201 |
| `rgba(137,207,240,0.16)` | 4 | --ac-accent-soft@workbench-theme.css:20 · --wf-ctx-hover-bg@WorkflowDirTree.vue:668 · --wf-edge-hover-bg@EdgeContextMenu.vue:124 · --wf-nodemenu-hover-bg@NodeContextMenu.vue:235 |
| `rgba(110,231,216,1)` | 3 | --case-icon-accent@ProjectWorkspace.vue:116 · --case-icon-accent@ProjectList.vue:151 · --case-icon-accent@CaseFileSheet.vue:405 |
| `rgba(196,181,253,1)` | 3 | --locator-header-icon-end@ProjectWorkspace.vue:106 · --locator-header-icon-end@ProjectList.vue:73 · --locator-header-icon-end@LocatorFileView.vue:145 |
| `rgba(187,187,187,1)` | 3 | --ac-wood-soft@workbench-theme.css:12 · --ac-ink-faint@workbench-theme.css:15 · --app-text-muted@tokens.css:71 |
| `rgba(247,201,72,1)` | 3 | --c-dashboard@tokens.css:27 · --el-color-primary@tokens.css:180 · --el-color-warning@tokens.css:189 |
| `rgba(107,203,119,1)` | 3 | --c-device@tokens.css:28 · --app-status-success@tokens.css:37 · --el-color-success@tokens.css:188 |
| `rgba(255,181,167,1)` | 3 | --c-runner@tokens.css:31 · --app-status-danger@tokens.css:40 · --el-color-danger@tokens.css:190 |
| `rgba(162,210,255,0.18)` | 3 | --case-border-subtle@tokens.css:298 · --chat-count-tint@ChatView.css:5 · --wf-picker-add-bg@PageFlowVueFlow.vue:789 |
| `rgba(0,0,0,0.05)` | 3 | --wf-btn-press-shadow@index.vue:486 · --wf-btn-press-shadow@WorkflowFileBrowser.vue:276 · --wf-btn-press-shadow@PageFlowVueFlow.vue:595 |
| `rgba(30,30,36,0.15)` | 3 | --case-menu-shadow@ProjectTree.vue:691 · --case-menu-shadow@CaseFileSheet.vue:571 · --kpi-icon-shadow@KpiCard.vue:157 |
| `rgba(254,253,251,1)` | 2 | --rg-hover-bg@ReportDetail.vue:437 · --rg-hover-bg@index.vue:371 |
| `rgba(0,0,0,0.04)` | 2 | --rg-shadow-soft@ReportDetail.vue:437 · --rg-shadow-soft@index.vue:371 |
| `rgba(0,0,0,0.25)` | 2 | --pep-enlarge-shadow-color@PageElementsPanel.vue:229 · --sap-enlarge-shadow-color@StructureAnalysisPanel.vue:238 |
| `rgba(0,0,0,0.12)` | 2 | --screenshot-img-shadow-color@ScreenshotView.css:8 · --kpi-pin-shadow@KpiCard.vue:155 |
| `rgba(232,228,216,1)` | 2 | --ac-border-soft@workbench-theme.css:17 · --el-border-color-light@tokens.css:208 |
| `rgba(47,110,163,1)` | 2 | --ac-accent-deep@workbench-theme.css:19 · --wf-nodemenu-hint@NodeContextMenu.vue:236 |
| `rgba(167,139,250,1)` | 2 | --c-element@tokens.css:29 · --app-status-purple-border@tokens.css:46 |
| `rgba(78,205,196,1)` | 2 | --c-case@tokens.css:30 · --paper-mark-teal@PaperDoodles.vue:110 |
| `rgba(232,121,249,1)` | 2 | --c-ai@tokens.css:33 · --el-color-primary@tokens.css:247 |
| `rgba(137,207,240,1)` | 2 | --c-workflow@tokens.css:34 · --el-color-info@tokens.css:191 |
| `rgba(200,245,208,1)` | 2 | --app-status-success-bg@tokens.css:38 · --app-pass@tokens.css:52 |
| `rgba(255,224,219,1)` | 2 | --app-status-danger-bg@tokens.css:41 · --app-fail@tokens.css:54 |
| `rgba(255,107,107,1)` | 2 | --app-marker-red@tokens.css:49 · --paper-mark-red@PaperDoodles.vue:109 |
| `rgba(212,216,220,1)` | 2 | --app-offline@tokens.css:59 · --tb-unarmed-border@ToolboxPanel.style.css:6 |
| `rgba(232,95,95,1)` | 2 | --app-error@tokens.css:60 · --ai-status-danger@tokens.css:289 |
| `rgba(248,246,242,1)` | 2 | --app-bg-subtle@tokens.css:66 · --el-fill-color-light@tokens.css:197 |
| `rgba(25,200,185,1)` | 2 | --ai-teal@tokens.css:256 · --mascot-teal@AnimatedMascot.vue:110 |
| `rgba(74,58,40,1)` | 2 | --ai-ink-soft@tokens.css:262 · --mascot-ink@AnimatedMascot.vue:115 |
| `rgba(162,210,255,0.24)` | 2 | --case-border@tokens.css:299 · --wf-picker-head-border@PageFlowVueFlow.vue:780 |
| `rgba(138,123,102,1)` | 2 | --eval-quiet-ink@EvaluatorTab.vue:551 · --kb-tree-dir-ink@KbTreeView.vue:112 |
| `rgba(192,132,252,1)` | 2 | --td-icon-grad-end@TaskDetailPage.vue:308 · --sv-icon-grad-end@SkillViewerPage.style.css:5 |
| `rgba(30,30,36,0.25)` | 2 | --note-tape-border@DoodleNote.vue:112 · --kpi-tape-border@KpiCard.vue:156 |

## 附录 C · 复合值内嵌颜色（7 处，本阶段保留字面量）

- `--app-shadow-sm@tokens.css:154`
- `--app-shadow-md@tokens.css:155`
- `--app-shadow-lg@tokens.css:156`
- `--el-box-shadow-light@tokens.css:210`
- `--el-box-shadow@tokens.css:211`
- `--el-box-shadow-dark@tokens.css:212`
- `--avatar-shadow@AgentBasicInfo.vue:62`