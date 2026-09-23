---
name: frontend-change-plan
description: |
  前端变更方案规划与输出 — 在写代码之前，按真实代码事实规划「改哪些页面 / 复用哪个共享件 / 走哪套版式」，产出一份自包含的 HTML 方案 + 可点原型供人审阅。
  产出物是文档与原型，不写平台代码；审阅通过后再交棒 OpenSpec 落单。
  Keywords: 前端方案, 变更方案, 改版方案, 方案规划, 原型, prototype, HTML 方案, 方案文档, 版式变体, 子页面导航, 界面改版, 审阅, 先出方案
  Trigger: 用户说「写个前端变更方案」「先出个方案我审阅」「出个原型给我看」「这个模块界面怎么改」「按这个模版做方案」「先规划再动手」时。
---

# 前端变更方案规划与输出

## 交付物

一份 **自包含单文件 HTML**：左侧章节导航 + 右侧「方案章节 / 可点原型」，落在 `temps/<topic>-proto.html`。

两条边界：

- 方案阶段 **零平台代码改动** —— 不碰 `frontend/`。产出的 HTML 是给人审阅的提案，不是产品代码。
- 「方案通过」不等于「可以开工」。开工必须走 OpenSpec（`openspec-propose`）。本技能只管到人点头为止。

为什么要分开：本仓库是规范驱动开发（行为规范要求禁止直接写代码）。而一个能被审阅的方案，必须先有可视化的版式与可点原型，否则审阅者只能对着文字想象后果。

## 先读的三份东西

| 文件 | 为什么 |
| --- | --- |
| 工作区规范 | 行为规范、目录约定、临时文件去向、Vue 硬规范 |
| `doodle-craft` skill | 视觉语言、8 模块色、令牌唯一真相源、自检项 |
| `references/authoring-guide.md`（本技能） | 原型编写手册：章节契约 / CSS 片段速查 / JS 交互模式 / 已知坑 |

## 工作流

### 步骤 1 · 事实核查（不做这步不许往下写）

行为规范要求「不推测逻辑，不假设问题」。方案里的每一页、每条路由、每个颜色都要当场从代码读出：

| 要读的事实 | 从哪读 |
| --- | --- |
| 真实路由与页面深度 | `frontend/src/router.ts` + `frontend/src/modules/*/routes.ts` |
| 页面根与版式 | 各模块 `index.vue` 根元素 class（如 `.doc-page .doc-page--fixed .wb-shell .device-workbench`） |
| 已有共享件 | `frontend/src/shared/components/`（清单见步骤 3） |
| 现有视觉语言是否已覆盖 | `frontend/src/shared/styles/`：`tokens.css`、`workbench-theme.css`、`motion.css` |
| 配色事实 | `frontend/src/shared/styles/tokens.css`（唯一真相源） |

**红线：先查「是不是已经做过了」。** 动手前必须扫 `openspec/changes/archive/` 与 `openspec/specs/*/spec.md` —— 你要改的东西很可能已实现并归档。把「已实现」写进方案，不要重复开单。

> 真实教训：`temps/doodle-appcard-panel-prototype.html` 曾被当成待办拿回来，但它对应的 `2026-09-14-add-doodle-appcard-panel` 早已归档、任务 6/6 完成、主 spec 在册，代码还走得更远（全仓只剩 1 处 `<el-card>`，就在 `AppCard.vue` 内部）。**先查归档，能省掉一整轮无用功。**

### 步骤 2 · 范围与深度盘点

先定义**深度**：从侧栏入口点进去要经过几层页面（L1 单页 / L2 列表→详情 / L3 三级 / 侧栏子项 + 深链）。

再产出「模块 × 深度 × 真实路由链 × 版式变体 × 改什么」一张表，**覆盖全站**而不只是被点名的模块 —— 审阅者需要看到改动边界。用模板的 `table.map`。

### 步骤 3 · 复用优先选型

**复制，不发明**（`doodle-craft` 核心原则）。先找最接近的既有件，再判断是否需要新组件；若要新增，方案里必须说明为什么前者不够。

| 角色 | 用什么 | 注意 |
| --- | --- | --- |
| 可复用数据块（图表 / 表格 / 指标 / 认证 / 条目卡） | `AppCard` | 钉板壳；只在 `.wb-shell` / `.workflow-workbench` 作用域内生效，域外会退回 Element Plus 默认外观 |
| 表纸（扁平列表） | `AppTable` + `accent` | **「SketchTable」是它的视觉名，不是第二个组件**（`AppTable.vue:22`） |
| 入口 / 资源格 | `SketchCard` | 点进去的卡片；不要拿它装图表，也不要把项目列表塞进 AppCard |
| 指标数字 | `KpiCard` | |
| 顶层分区标题 | `.doc-section` | 分区**不用** AppCard（`frontend-l3-content-block`） |
| 分段 / 筛选 | `FilterTabs`、`AppTabs` | 二态配色口径见 `frontend-doodle-button` |
| 子页返回 / 面包屑 | `WorkbenchCrumbs` + `.back-chip` | 见 `frontend-doodle-subpage-nav` |
| 三态（加载 / 错 / 空） | `patterns/{SkeletonCard,ErrorState,EmptyState}` | 加载期不得渲染空态 |
| 按钮 | `DoodleBtn` | 皮肤真相源在模块 scoped CSS；令牌在 `tokens.css` |

版式变体四选（模板 `#page-plan` 已示范）：**A 钉板**（KPI / 入口卡网格）· **B 表格纸**（一张纸的扁列表）· **C 分栏台**（左树或面板 + 右内容）· **H Hub 入口**（撕纸卡网格进下一层）。

### 步骤 4 · 产出 HTML 方案 + 原型

整份复制模板（保留 `<style>` 与交互 `<script>` 骨架），替换章节内容：

```powershell
Copy-Item .agents/skills/frontend-change-plan/assets/plan-prototype-template.html temps/<topic>-proto.html
```

章节契约（顺序语义：先讲改什么 → 再讲导航 → 然后可点原型 → 最后一览与去重）：

1. **总方案** — 信息架构表 + 版式变体 + Do/Don't + 落地顺序 P0/P1/P2
2. **子页导航** — 涉及 L2+ 深度时必有：三种导航模版 + 面包屑规范片段
3. **可点原型** — 每个改版主题一节
4. **其它模块** — 一览 + 迷你原型
5. **与已有方案的关系** — 明确本方案不重复哪几份既有原型 / spec

CSS 片段速查、JS 交互的五种写法，以及若干**已知坑**（`.wb` 默认紫阴影会静默吃错色、`.mini` 微倾依赖兄弟序号、`.pin` 缺 `pointer-events`、reduced-motion 覆盖不全……）见 `references/authoring-guide.md`。

**颜色要诚实标注**：模板 `:root` 里 8 个 `--c-*` 模块色与产品一致，而 `--ink` / `--yellow` / `--red` / `--teal` 是原型局部的**示意色**，与 `tokens.css` 并不相同。写方案时引用令牌名（`var(--c-device)`），不要把示意色值说成产品色值。

### 步骤 5 · 自检、交付、等审阅

跑完 `references/authoring-guide.md` §7 的 10 项清单（含一条硬检查：`git status` 里不得出现 `frontend/` 的改动）。然后用 `present` 把 HTML 交给用户，并逐条口述：改了哪些页面、复用哪些共享件、分几批、哪些明确不做。

**审阅通过之后**：交棒 `openspec-propose`。把方案里的范围与 P0/P1/P2 批次直接当作 change 的输入；HTML 方案作为设计依据写进 proposal 的 Why，或作为 design.md 的引用来源。

## 边界（不要越界做的事）

- **不写平台代码**，也不「顺手」修 `frontend/` 里发现的问题 —— 那些属于后续 change 的范围，写进方案的「发现但不在本次范围」。
- **不发明新视觉**：原型里每个元素都应能在产品现状或 `doodle-craft` 规格里找到出处。
- **不改业务、路由深度与 API**：方案针对版式与导航，业务链路不动。
- **不把原型色值当规范**：原型的色值是示意，规范在 `tokens.css` 与 spec。

## 与 html-report 的关系（格式优先级）

`html-report` 声称是本项目「所有 HTML 报告 / 方案文档」的唯一权威设计规范（animal-island-ui）。**本技能产出的原型方案 HTML 是明确的例外**，理由：原型的职责是**镜像产品真实的 UI 语言**，让审阅者看到改动后界面长什么样；用一套与产品无关的报告皮肤去画界面原型，评审就失去意义。

据此分工，不要混在一份文件里：

| 产物 | 走哪套 |
| --- | --- |
| 界面原型 + 版式方案（本技能交付物，`temps/*-proto.html`） | 本技能模板（Doodle Craft DNA，与产品同源） |
| 纯文字类报告：分析报告 / 质量报告 / 测试报告 / 架构图 | `html-report`（animal-island-ui） |

一次交付里两者都有时，分成两个文件。

## 参考文件

| 文件 | 内容 |
| --- | --- |
| `assets/plan-prototype-template.html` | 1491 行自包含模版：侧栏章节导航 + 23 个 CSS 片段 + 五种 JS 交互（复制起点） |
| `references/authoring-guide.md` | 章节契约、配色诚实标注、CSS 片段速查表、已知坑 6 条、JS 交互模式、交付自检 10 项 |

视觉与令牌真相源在 `doodle-craft` skill；前端验收在 `vue-frontend-check` skill；落单流程在 `openspec-propose` skill。
