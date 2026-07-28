# 前端技术债清理 — SPEC

> 版本 v1.0 | 2026-07-27 | 基于全量前端代码扫描
>
> 扫描范围：`frontend/src/modules/` 9 个模块 + `frontend/src/shared/`
> 对照标准：`frontend/CLAUDE.md` + `.claude/rules/frontend.md` + `frontend/DESIGN_SYSTEM.md`

---

## 目录

1. [总览 — 技术债热力图](#1-总览--技术债热力图)
2. [1号线：文件瘦身 — 超标文件拆分](#2-1号线文件瘦身--超标文件拆分)
3. [2号线：硬编码色值 — 令牌驱动改造](#3-2号线硬编码色值--令牌驱动改造)
4. [3号线：无状态/错误态 — 三态规范补齐](#4-3号线缺失状态--三态规范补齐)
5. [4号线：模块结构 — 架构与依赖合规](#5-4号线模块结构--架构与依赖合规)
6. [5号线：设计令牌 — tokens.css 与 DESIGN_SYSTEM 对齐](#6-5号线设计令牌--tokenscss-与-design_system-对齐)
7. [6号线：样式违规 — 圆角/模糊/overflow](#7-6号线样式违规--圆角模糊overflow)
8. [7号线：共享组件 — 推广使用率](#8-7号线共享组件--推广使用率)
9. [执行路线图](#9-执行路线图)

---

## 1. 总览 — 技术债热力图

```
          文件瘦身  硬编码色值  Error/Empty 模块结构  令牌对齐  样式违规  共享组件
dashboard    🟢        🟢        🟢         🟢       🟢        🟢        🟢
device-pool  🟡        🟢        🟢         🟢       🟢        🟢        🟡
element-loc  🔴        🟡        🟡         🟡       🟡        🟡        🟡
case-manager 🔴        🟡        🟡         🟡       🟡        🟡        🟡
test-runner  🔴        🟢        🔴         🟢       🟢        🟡        🟡
report-gen   🟡        🟢        🟢         🟡       🟢        🟢        🟡
ai-assistant 🔴        🔴        🟢         🟡       🔴        🔴        🟢
workflow     🔴        🟡        🔴         🟡       🟡        🟡        🟡
digital-human🟢        🟢        🔴         🔴       🟢        🔴        🟡

🔴 严重  🟡 中等  🟢 合规
```

### 统计摘要

| 指标 | 当前值 | 目标值 | 差距 |
|------|--------|--------|------|
| 超标文件 (>500行) | 11 个 | 0 个 | 11 |
| 超软上限 (>300行) | 22+ 个 | ≤10 个 | 12+ |
| 硬编码色值点 | ~150+ 处 | 0 处 | ~150 |
| 缺失 ErrorState 模块 | 4 个 | 0 个 | 4 |
| 缺失三态的模块 | 7/9 | 0/9 | 7 |
| 结构不全的模块 | 2 个 (digital-human, report-gen) | 0 个 | 2 |
| 未使用共享组件的模块 | 5 个 | 0 个 | 5 |
| border-radius:50% 违规 | ~15 处 | 0(或明确豁免) | ~15 |
| backdrop-filter/blur | 3 处 | 0 | 3 |
| tokens.css 与 DESIGN_SYSTEM 不一致 | 2 处 | 0 处 | 2 |

---

## 2. 1号线：文件瘦身 — 超标文件拆分

### 规则

> `frontend.md`: 硬上限 **500 行**，软上限 **300 行**。出现 ref/reactive > 6 个 / 模板 > 150 行任一即该拆。

### 🔴 严重 — 超过 500 行硬上限 (11 个文件)

| 文件 | 行数 | 超标比例 | 核心问题 | 拆分建议 |
|------|------|:--:|------|------|
| [WebElementManager.vue](frontend/src/modules/element-locator/components/WebElementManager.vue) | **1072** | 2.1x | Web 元素 CRUD 巨型组件 | 拆出 WebElementTable、WebElementForm、WebElementImport 三个子组件 |
| [DirectoryTree.vue](frontend/src/modules/case-manager/components/DirectoryTree.vue) | **960** | 1.9x | 目录树 + 内联操作全在单文件 | 拆出 TreeContextMenu、TreeDragDrop、TreeBatchActions |
| [StepEditor.vue](frontend/src/modules/case-manager/components/StepEditor.vue) | **917** | 1.8x | 步骤编辑器重度耦合 | 按步骤类型拆 StepXXXEditor 组件 + StepEditorContainer |
| [test-runner/index.vue](frontend/src/modules/test-runner/index.vue) | **807** | 1.6x | 主页面塞了太多逻辑 | 拆出 TaskList、TaskCreateDialog、RunProgressPanel |
| [PageFlowVueFlow.vue](frontend/src/modules/workflow/components/vueflow/PageFlowVueFlow.vue) | **797** | 1.6x | VueFlow 画布 + 控制栏全在一个 | 拆出 FlowCanvas、FlowToolbar、FlowMiniMap |
| [PageElementsPanel.vue](frontend/src/modules/element-locator/components/PageElementsPanel.vue) | **790** | 1.6x | 元素面板膨大 | 拆出 ElementTable、ElementBreadcrumb、PageSelector |
| [ApiEndpointManager.vue](frontend/src/modules/element-locator/components/ApiEndpointManager.vue) | **770** | 1.5x | API 端点管理 | 拆出 EndpointTable、EndpointForm、EndpointTestPanel |
| [TaskDetail.vue](frontend/src/modules/test-runner/components/TaskDetail.vue) | **769** | 1.5x | 任务详情 | 拆出 TaskLog、TaskStepTimeline、TaskSummaryCard |
| [workflow/index.vue](frontend/src/modules/workflow/index.vue) | **768** | 1.5x | 工作流主页 | 拆出 WorkflowList、WorkflowToolbar、WorkflowCanvas |
| [CaseEditor.vue](frontend/src/modules/case-manager/CaseEditor.vue) | **759** | 1.5x | 用例编辑器 | 拆出 CaseMetaForm、CaseStepPanel、CasePreviewPanel |

### 🟡 中等 — 300~500 行 (11+ 个文件)

| 文件 | 行数 | 备注 |
|------|------|------|
| TestCaseBlockly.vue | 697 | 接近不可拆分（Blockly 特性），标记观察 |
| WorkflowDirTree.vue | 660 | 可拆 ContextMenu |
| device-pool/index.vue | 625 | 可拆 DeviceGrid + FilterBar |
| ScreenshotView.vue | 589 | 核心截图逻辑，谨慎拆分 |
| ai-assistant/index.vue | 578 | 可拆 AgentGrid + TaskPanel |
| EvaluatorTab.vue | 547 | 可拆 EvalForm + EvalResults |
| ChatView.vue | 547 | SS/SessionList + ChatWindow |
| AgentDetail.vue | 515 | 已按步骤拆分 Agent* 子组件，标记观察 |
| XPathCandidatePanel.vue | 504 | 可拆为 XPathList + CandidateDetail |
| ElementManager.vue | 455 | 比 WebElementManager 小，但仍超软上限 |
| digital-human/index.vue | 450 | 占位页面，暂不处理 |
| ReportDetail.vue | 439 | 可拆 ReportSummary + ReportChart |
| CaseBreakdown.vue | 431 | 可拆 |
| AgentStickyNote.vue | 427 | 可拆 |
| dashboard/index.vue | 401 | 可拆 KpiRow + ActivityPanel |
| MessageBubble.vue | 391 | 接近不可拆分 |

### 验收条件

- [ ] 所有 >500 行文件已拆分到 500 行以内
- [ ] 所有 >300 行文件已拆分或有明确的观察标记
- [ ] `find frontend/src/modules -name "*.vue" | xargs wc -l | sort -rn | head -10` 无 >500 行文件
- [ ] 拆分后功能不变、路由不变、测试通过

---

## 3. 2号线：硬编码色值 — 令牌驱动改造

### 规则

> `frontend.md` 样式约束 #1: 颜色/圆角/阴影/字体从 `tokens.css` 取。
> `DESIGN_SYSTEM.md` §5.11: 禁止组件 scoped 中硬编码色值（必须走 `var(--*)`）
> `DESIGN_SYSTEM.md` §1.9: 颜色使用规则

### 🔴 严重 — ai-assistant 模块（~90% 违规集中在此）

**AgentDetail.vue** — CSS 块中大量硬编码色值：
```
#19c8b9, #e6f9f6, #158a80, #4a3a28, #f0ebe0, #5c4b38, #a0936e
```

**AgentToolsPanel.vue** — 内联样式和 scoped CSS 满篇硬编码：
```
#19c8b9, #e6f9f6, #158a80, #e8e2d6, #faf9f4, #2d7a2d, #C8F5D0, #a03030, #FFE0DB, #a0936e, #f0ede8
```

**ConfirmDialog.vue** — 大量硬编码背景色：
```
#faf9f4, #e8f5e9, #c8e6c9, #ffebee, #ffcdd2, #f5f5f5, #eeeeee, #e6f9f6, #b2dfdb
```

**HintCard.vue** — 5 种提示类型色 + 4 种背景色全部硬编码：
```
#534ab7, #378add, #1d9e75, #ba7517, #d85a30 (类型色)
#fff8e7, #f7cd67, #fff3e0, #e3f2fd, #e8f5e9, #ffebee, #f5f5f5 (背景色)
```

**AgentFormFooter.vue**：
```
#f0ebe0, #15a89c
```

**AgentBasicInfo.vue**：
```
#faf9f4
```

**AgentStickyNote.vue**：
```
#fffef8, #fffbf5
```

**MessageBubble.vue**：
```
#e6f9f6
```

### 🟡 中等 — 其他模块零星违规

| 模块/文件 | 问题 |
|------|------|
| element-locator/DeviceSelector.vue | `#999` 作为 dev-dot 背景（应用 `--app-ink-muted`） |
| device-pool/DeviceActionsCell.vue | `#D4C8F0` hover 色 |

### 改造方案

1. **在 tokens.css 中新增 ai-assistant 专用令牌**（补充到 `[data-theme="light"]` 根作用域 + `.ai-workbench` 作用域）：

```css
/* ai-assistant 模块令牌 — 新增 */
--ai-teal:         #19c8b9;
--ai-teal-bg:      #e6f9f6;
--ai-teal-text:    #158a80;
--ai-teal-hover:   #15a89c;
--ai-warm-bg:      #faf9f4;
--ai-warm-border:  #e8e2d6;
--ai-ink-soft:     #4a3a28;
--ai-ink-muted:    #a0936e;
--ai-sticky-bg:    #fffef8;
--ai-sticky-cream: #fffbf5;
--ai-bg-subtle:    #f0ebe0;
--ai-bg-success:   #e8f5e9;
--ai-bg-error:     #ffebee;
--ai-bg-neutral:   #f5f5f5;
--hint-purple:     #534ab7;
--hint-blue:       #378add;
--hint-green:      #1d9e75;
--hint-orange:     #ba7517;
--hint-red:        #d85a30;
--hint-purple-bg:  #e3f2fd;
--hint-green-bg:   #e8f5e9;
--hint-orange-bg:  #fff3e0;
--hint-red-bg:     #ffebee;
--hint-neutral-bg: #f5f5f5;
```

2. **逐个组件替换硬编码色值为 `var(--ai-*)` / `var(--hint-*)`**

### 验收条件

- [ ] `grep -rnP "color:\s*#[0-9a-fA-F]{3,6}|background:\s*#[0-9a-fA-F]{3,6}" frontend/src/modules/ --include="*.vue" | grep -v "tokens\|style.css"` 输出为 0
- [ ] JSON 语法高亮中的色值（AgentDetail.vue 的 `.replace()` 调用）标记为豁免项（代码渲染用，非样式）
- [ ] 所有新增令牌在 tokens.css 有完整注释

---

## 4. 3号线：缺失状态 — 三态规范补齐

### 规则

> `DESIGN_SYSTEM.md` §3.7: 每个列表/表格必须有 加载/空/错误 三态。
> `DESIGN_SYSTEM.md` §5.4: 禁止全屏 spinner、禁止白屏、禁止空白列表。

### 🔴 严重 — 主页面无加载/错误态

| 模块 index.vue | 当前状态 | 缺什么 |
|------|:--:|------|
| **case-manager/index.vue** | 无 loading/error 检测 | ErrorState + 加载态 |
| **test-runner/index.vue** | 无 loading/error 检测 | ErrorState + 加载态 |
| **workflow/index.vue** | 无 loading/error 检测 | ErrorState + 加载态 |
| **digital-human/index.vue** | 无任何数据获取 | 占位页面，不做要求 |

### 🟡 中等 — 子组件缺少三态

| 组件 | 缺什么 |
|------|------|
| element-locator items | 部分表格无 ErrorState/EmptyState |
| case-manager 子组件 | StepEditor/StepViewer 无加载态骨架屏 |
| test-runner/components | TaskDetail 内子面板无错误态 |

### 改造方案

1. 统一使用 `shared/components/patterns/` 下的共享组件：
   - `ErrorState.vue` — 错误提示条（含重试按钮）
   - `EmptyState.vue` — 空数据提示（图标 + 文字 + 可选操作按钮）
   - `SkeletonCard.vue` — 骨架屏加载态
2. 每个模块 index.vue 必须包裹：
   ```vue
   <ErrorState v-if="error" :message="error" @retry="fetchData" />
   <div v-loading="loading">...</div>
   <EmptyState v-if="!loading && !error && !list.length" ... />
   ```
3. ref/computed 命名统一：`error` / `loading`

### 验收条件

- [ ] 8 个有数据的模块 index.vue 都含 `ErrorState` 组件使用
- [ ] 8 个有数据的模块 index.vue 都有 `v-loading` 或 `SkeletonCard`
- [ ] 所有模块的 API 调用都含 `.catch(err => error.value = ...)` 错误处理
- [ ] 无 `try { ... } catch (_) {}` 静默吞错

---

## 5. 4号线：模块结构 — 架构与依赖合规

### 规则

> `frontend.md` 架构红线 #1-#3：按业务域拆分、模块自治、调用链单向。
> `frontend.md` 三层职责：components 只渲染、composables 状态+逻辑、api.js 纯 HTTP。

### 🔴 严重 — 结构不全

| 模块 | api.js | components/ | composables/ | 备注 |
|------|:--:|:--:|:--:|------|
| **digital-human** | ❌ | ❌ | ❌ | 占位页面，仅一个 index.vue + routes.js |
| **report-generator** | ✅ | ✅ | ❌ | 缺少 composables/，逻辑可能混在组件中 |

### 🟡 中等 — 结构异常

| 问题 | 详情 |
|------|------|
| **case-manager** 有巢状子目录 | `components/api/` `components/storage/` `components/ui/` `components/web/` — 过度分层 |
| **case-manager** 有独立 `.css` 文件 | `index.css: 12897B` — 应该 scoped 在 .vue 中，或放 tokens.css |
| **device-pool** 有独立 `.css` 文件 | `device-pool.css: 9734B` — 同上 |
| **ai-assistant** 有 `ChatView.css` | `ChatView.css: 12178B` — 应该 scoped |
| **report-generator** 有 `index.css` | `index.css: 5226B` — 应该 scoped |
| **ai-assistant** api.js 663 行 | 远超正常范围（其他模块 60-160 行），应拆出 `api-{domain}.js` |
| **workflow** 自建 store/ | 使用 Pinia store，与项目"能用 ref 不用 Pinia"原则冲突。考虑是否降级 |

### 改造方案

| 优先级 | 行动 |
|:--:|------|
| P0 | report-generator 补建 `composables/`，将组件中业务逻辑抽入 |
| P1 | 4 个独立 .css 文件并入对应 .vue 的 `<style scoped>` 或 tokens.css |
| P1 | ai-assistant/api.js 拆分为 `api-agents.js`, `api-tasks.js`, `api-evaluator.js` |
| P2 | case-manager 组件子目录扁平化 |
| P3 | digital-human 补建基本结构或标记为 `deprecated/placeholder` |

### 验收条件

- [ ] 每个模块有 api.js + components/ + composables/（占位模块除外）
- [ ] 模块目录无独立 .css 文件（tokens.css 全局样式除外）
- [ ] ai-assistant/api.js ≤ 300 行
- [ ] 无新增 Pinia store（workflow 特殊场景允许保留）

---

## 6. 5号线：设计令牌 — tokens.css 与 DESIGN_SYSTEM 对齐

### 🔴 严重 — 字号刻度不一致

| 令牌 | tokens.css 现值 | DESIGN_SYSTEM.md 标称 | 冲突 |
|------|:--:|------|------|
| `--app-font-size-sm` | **12px** | `--app-size-sm` = 14px | tokens 的 sm 是 12px 但 DESIGN_SYSTEM 的 sm 是 14px |
| `--app-font-size-base` | 14px | 无对应 | legacy 别名，多余 |
| `--app-font-size-lg` | 16px | `--app-size-md` = 16px | 命名混乱：tokens 的 lg=16px 但 DESIGN_SYSTEM 的 lg=20px |

**根因**：`tokens.css` 保留了旧版 legacy aliases (`--app-font-size-sm/base/lg`)，而 `DESIGN_SYSTEM.md` 定义了新的 6 档刻度 (`--app-size-{xs,sm,md,lg,xl,2xl}`)。两套体系并存，开发者不知道用哪个。

### 修复方案

1. **统一推荐用 `--app-size-*` 体系**：
   - `--app-size-xs: 12px` ← 按钮文字、标签、Badge
   - `--app-size-sm: 14px` ← UI 正文
   - `--app-size-md: 16px` ← 卡片标题、表单标签
   - `--app-size-lg: 20px` ← 段落标题、弹窗标题
   - `--app-size-xl: 24px` ← 页面标题
   - `--app-size-2xl: 32px` ← KPI 数字

2. **废弃旧别名**：`--app-font-size-sm/base/lg` 标注 `@deprecated` 并全局替换

3. **style.css 中 hardcoded font-size** 也需替换：
   - `h1 { font-size: 26px }` → `var(--app-size-xl)`
   - `h2 { font-size: 22px }` → `var(--app-size-lg)` 或新建
   - `h3 { font-size: 17px }` → `var(--app-size-md)`
   - `h4 { font-size: 15px }` → 不在刻度表内，统一为 `var(--app-size-sm)`

### 验收条件

- [ ] `--app-font-size-*` legacy aliases 标注 `@deprecated` 注释
- [ ] style.css 中 h1-h4 使用 `var(--app-size-*)` 变量
- [ ] DESIGN_SYSTEM.md 字号刻度表无冲突
- [ ] `grep -rn "font-size:\s*[0-9]" frontend/src/ --include="*.css" --include="*.vue" | grep -v "var(--" | grep -v "node_modules"` 只输出豁免项

---

## 7. 6号线：样式违规 — 圆角/模糊/overflow

### 🔴 严重

| 违规类型 | 位置 | 数量 | 规则引用 |
|------|------|:--:|------|
| `border-radius: 50%` | 10+ 文件（卡片装饰、状态点、头像） | ~15 | §1.5 禁止对称大圆角 |
| `border-radius: 20px` | PageElementsPanel.vue, ScreenshotView.vue | 2 | §1.5 |
| `border-radius: 12px` | AgentToolsPanel.vue 多处 | 5+ | 不在不对称圆角规范中 |
| `filter: blur()` | digital-human, LoginView.vue | 3 | §5.11 禁止 glass/blur |
| `overflow: hidden` | ai-assistant 模块 15+ 处 | ~30 | §4.4 禁止中间层 overflow:hidden |

### 🟡 中等

| 违规类型 | 位置 | 备注 |
|------|------|------|
| `border-radius: 50%` 用于 avatar/dot | 若干 | 可豁免（纯装饰圆形元素） |
| style.css h1-h4 hardcoded font-size | 4 处 | 已在 §5 线覆盖 |
| `gap: 24px` 在 style.css | 1 处 | 应用 `var(--app-space-lg)` |
| `padding: 24px 28px 60px` 在 style.css | 1 处 | 应用间距刻度变量 |

### 修复策略

**border-radius: 50%** — 分两类处理：
- 不可豁免：卡片装饰、状态标签、panel — 改为 `3px 6px 3px 6px` 等不对称圆角
- 可豁免：头像圈、色点指示器（`width:7px; height:7px; border-radius:50%` — 太小无法不对称）

**overflow: hidden** — 逐一审核，改为：
- 文字截断场景 → `text-overflow: ellipsis` + 不设 overflow:hidden 在父容器
- 裁剪场景 → 确认不影响滚动

**filter: blur()** — digital-human 和 LoginView 的背景动效保留（非玻璃态，是动效背景）

### 验收条件

- [ ] 无可豁免的 `border-radius: 50%` / `20px` / `12px` 已替换
- [ ] 豁免列表在 tokens.css 顶部注释中登记
- [ ] 新增 `overflow: hidden` 均含注释说明原因

---

## 8. 7号线：共享组件 — 推广使用率

### 现状

共享组件已建好，但**使用率低**：

| 共享组件 | 当前使用者 | 应使用者 |
|------|------|------|
| **ErrorState.vue** | dashboard, report-generator | **全部 8 模块** |
| **EmptyState.vue** | ai-assistant, case-manager(DirectoryTree), device-pool, report-gen, test-runner | 全部 8 模块（部分已用） |
| **SkeletonCard.vue** | dashboard/StatsCard | ai-assistant, element-locator, test-runner |
| **FilterTabs.vue** | ❓ 待查 | case-manager, test-runner, report-gen |
| **KpiCard.vue** | ❓ 待查 | dashboard, device-pool, test-runner |
| **AppTabs.vue** | ai-assistant | report-generator |

### 改造方案

1. 全局搜索手写的错误提示条和空状态，全部替换为共享组件
2. 各模块统一 `ErrorState` 使用模式
3. 手写的 filter tabs → `FilterTabs.vue`
4. 手写的 KPI 卡 → `KpiCard.vue`

### 验收条件

- [ ] `grep -rn "v-if.*error" frontend/src/modules/ --include="*.vue"` 结果中每个手写错误条都关联 Issue 替换
- [ ] `grep -rn "暂无数据\|没有数据\|暂无任务" frontend/src/modules/ --include="*.vue"` 均使用 `EmptyState` 组件

---

## 9. 执行路线图

### Phase 1: 小快赢（预计 2-3 天）— 不改架构，纯 CSS/组件替换

```
1.1 tokens.css 对齐 DESIGN_SYSTEM.md
    ├── 废弃旧别名，统一推荐 --app-size-*
    └── 新增 ai-assistant 模块令牌
    ✅ 产出：tokens.css 无冲突 + ai 令牌就位

1.2 4 模块补齐 ErrorState + EmptyState
    ├── case-manager/index.vue
    ├── test-runner/index.vue
    ├── workflow/index.vue
    └── element-locator/index.vue
    ✅ 产出：8 模块全有三态

1.3 3 模块补齐 EmptyState 替换手写空状态
    ✅ 产出：全文无手写 "暂无数据"

1.4 independent .css → scoped
    ├── case-manager/index.css → index.vue
    ├── device-pool/device-pool.css → index.vue
    ├── report-generator/index.css → index.vue
    └── ai-assistant/ChatView.css → ChatView.vue
    ✅ 产出：模块目录无独立 .css
```

### Phase 2: 硬编码色值清理（预计 2-3 天）

```
2.1 ai-assistant/AgentDetail.vue 硬编码色 → var(--ai-*)
2.2 ai-assistant/AgentToolsPanel.vue 硬编码色 → var(--ai-*)
2.3 ai-assistant/ConfirmDialog.vue 硬编码色 → var(--ai-*)
2.4 ai-assistant/HintCard.vue 硬编码色 → var(--hint-*)
2.5 ai-assistant 其余子组件
2.6 其他模块零星硬编码色
    ✅ 产出：grep 硬编码色 0 结果
```

### Phase 3: 文件拆分（预计 4-6 天）— 逐个拆分，拆分一个验证一个

```
3.1 WebElementManager.vue     1072 → <500
3.2 DirectoryTree.vue         960  → <500
3.3 StepEditor.vue            917  → <500
3.4 test-runner/index.vue     807  → <500
3.5 PageFlowVueFlow.vue       797  → <500
3.6 PageElementsPanel.vue     790  → <500
3.7 ApiEndpointManager.vue    770  → <500
3.8 TaskDetail.vue            769  → <500
3.9 workflow/index.vue        768  → <500
3.10 CaseEditor.vue           759  → <500
3.11 其余 300-500 行文件
    ✅ 产出：无 >500 行 Vue 文件
```

### Phase 4: 样式违规修复（预计 1-2 天）

```
4.1 border-radius 审核 + 替换
4.2 overflow:hidden 审核 + 注释
4.3 style.css font-size 硬编码 → var(--app-size-*)
4.4 style.css padding/gap 硬编码 → var(--app-space-*)
    ✅ 产出：grep 样式违规 0 结果
```

### Phase 5: 架构优化（预计 2-3 天）

```
5.1 report-generator 补建 composables/
5.2 ai-assistant/api.js 拆分
5.3 case-manager 组件子目录扁平化
5.4 共享组件推广使用
    ✅ 产出：模块结构一致性达标
```

---

## 每阶段通用验收

```bash
# 编译
cd frontend && npx vite build --mode development 2>&1 | tail -10

# 色值检查
grep -rnP "color:\s*#[0-9a-fA-F]{3,6}|background:\s*#[0-9a-fA-F]{3,6}" \
  frontend/src/modules/ --include="*.vue" | grep -v "tokens\|style.css"

# 文件上限
find frontend/src/modules -name "*.vue" | xargs wc -l | sort -rn | head -10

# 浏览器验证
#   - 侧边栏 9 菜单项完整
#   - 每个模块页面可加载
#   - 页面可纵向滚动
#   - 缩小窗口确认
```

---

## 变更记录

| 版本 | 日期 | 变更摘要 |
|------|------|----------|
| v1.0 | 2026-07-27 | 初版：全量扫描 9 模块，7 条清理线，5 阶段执行路线 |
