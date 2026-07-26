# SPEC — 用例管理模块重构

> 基于 SPEC-模块重构规范.md，针对 case-manager 模块的逐阶段执行计划。
> 版本：v1.0 · 日期：2026-07-25

---

## 当前状态快照

```
frontend/src/modules/case-manager/
├── index.vue                         248 行 · 主列表页（编排者）
├── index.css                         638 行 · scoped CSS
├── api.js                             61 行 · API 聚合出口（26 函数重导出）
├── routes.js                          34 行 · 路由定义
├── step-utils.js                       —  · 步骤工具函数（与 StepEditor 代码重复）
├── constants.js                       ❌ 缺失
├── stores/                            ❌ 空目录
├── composables/
│   ├── useStepDragDrop.js             49 行 · 步骤拖拽排序
│   ├── useStepFields.js              48 行 · 步骤字段工具
│   ├── useCaseManager.js             27 行 · 用户名/类型解析
│   └── useBatchSelect.js             99 行 · 批量选择（⚠️ 未接入，DirectoryTree 内联重复）
├── components/
│   ├── CaseEditor.vue                761 行 · 用例编辑页（超标 261 行）
│   ├── StepEditor.vue                957 行 · 步骤编辑器（超标 457 行）
│   ├── DirectoryTree.vue             960 行 · 目录树（超标 460 行）
│   ├── CaseCard.vue                  263 行 · 用例卡片
│   ├── StepViewer.vue                187 行 · 步骤查看器
│   ├── WatcherPanel.vue              167 行 · 变量观察面板
│   └── ui/web/storage/api 子目录    各含 CaseList + CaseEditor
│
└── api/ 子目录
    ├── directories.js                 36 行
    ├── uiAutomation.js                81 行
    ├── storage.js                     29 行
    ├── apiTesting.js                  29 行
    └── webAutomation.js               29 行
```

**架构评级**：L3（有 composables，缺 constants.js）。模块总行数 ~4876，是 9 模块中**体量最大**的。

---

## 关键问题

| 问题 | 严重度 | 说明 |
|------|:--:|------|
| **3 个 God 组件超标** | 🔴 | DirectoryTree 960 + StepEditor 957 + CaseEditor 761 — 全部远超 500 |
| **步骤代码重复** | 🟠 | `stepSummary()` 在 step-utils.js 和 StepEditor.vue 各有一份（各 ~150 行） |
| **useBatchSelect 未接入** | 🟡 | composable 已创建但 DirectoryTree 仍用内联逻辑 |
| **零 KPI 卡片** | 🟡 | 主列表页无统计概览 |
| **11 处裸调 API** | 🟡 | CaseEditor(5) + StepEditor(4) + WatcherPanel(2) |
| **API 聚合层冗余** | 🟢 | api.js 是纯重导出，api/uiAutomation.js 已有包装函数但组件绕过它直接 import client |
| **字体** | ✅ | 无 Caveat/Quicksand 残留 |
| **stores/ 空目录** | 🟢 | 可接受 |

---

## 阶段 1：基础设施统一 — 已完成 ✅

背景点阵 + 全宽已在全局生效。字体已统一。

---

## 阶段 2：代码重复消除 — stepSummary 统一

### 问题

`step-utils.js` 和 `StepEditor.vue` 各有一份 `stepSummary()`（~150 行 switch），StepEditor 版本是 step-utils 的子集。

### 操作

1. 将 `StepEditor.vue` 的 `stepSummary` 替换为 `import { stepSummary } from '../step-utils.js'`
2. `step-utils.js` 的 `stepSummary` 接受可选的 `resolveElementName` 参数（处理实时元素库查找场景）
3. `STEP_TYPES` 统一来源：step-utils.js 从 `@/shared/constants/steps.js` 引入，不再自己定义

---

## 阶段 3：接入 useBatchSelect composable

### 问题

`composables/useBatchSelect.js` 已创建但 DirectoryTree.vue 仍用内联批量选择逻辑（~130 行）。

### 操作

DirectoryTree.vue 从 composable 引入，删除内联 selectMode/checkedIds/selectAll/moveDialog 相关代码。

---

## 阶段 4：KPI 统计概览 — 新增

### 问题

主列表页（index.vue）没有任何 KPI 卡片。用户不知道有多少用例、多少已启用。

### 新功能

在 WorkbenchHeader 下方增加统计概览 section：

```
统计概览 Overview
┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
│  总计 11  │ │  已启用 9  │ │  UI 6    │ │  Web 3   │
└──────────┘ └──────────┘ └──────────┘ └──────────┘
```

**组件**：`shared/components/KpiCard.vue`，颜色使用 `var(--c-case)` `#4ECDC4` 青绿。

---

## 阶段 5：裸调 API 消除 — 11→0

| 文件 | 当前 | 修复 |
|------|------|------|
| CaseEditor.vue (5 处) | `client.get("/devices")` / `client.get("/cases/definitions/${id}")` 等 | 改为从 `api.js` 引入 `listDevices`/`getDefinition`/`saveDefinition` |
| StepEditor.vue (4 处) | `client.get("/elements/pages")` / `client.post("/runner/run-step")` | 改为从 `api.js` 引入 |
| WatcherPanel.vue (2 处) | 同上 | 同上 |

`api/uiAutomation.js` 已经定义了这些包装函数，只是没被调用。

---

## 阶段 6：模块颜色收束

| 当前 | 应该 | 位置 |
|------|------|------|
| 操作按钮色不统一 | `var(--c-case)` `#4ECDC4` | CaseEditor / DirectoryTree |
| resizer hover 色不统一 | `var(--c-case)` | index.vue |

---

## 阶段 7：constants.js 补全

从各文件内联常量提取：

| 当前位置 | 内容 | 应放 constants.js |
|------|------|------|
| index.vue | `tabs` 数组（4 case-type labels） | `CASE_TYPE_TABS` |
| CaseEditor.vue | `EXEC_PREFIXES`、form 默认值 | `EXEC_PREFIXES`、`DEFAULT_FORM` |
| DirectoryTree.vue | `ROUTE_CREATE`/`ROUTE_EDIT_PREFIX`/`DELETE_API` 映射 | 三组常量 |

---

## 阶段 8：PRD 更新

参照 PRD-00 格式更新 PRD-03-用例管理.md。

---

## 执行顺序

```
1. 代码重复消除 (stepSummary)      →  1h   ─ 150 行重复归零
2. useBatchSelect 接入              →  1h   ─ DirectoryTree -130 行
3. KPI 统计概览新增                 →  1h   ─ 4 张 KpiCard
4. 裸调 API 消除 (11→0)            →  1.5h ─ 3 文件改引用
5. 模块颜色收束                    →  0.5h
6. constants.js 补全               →  0.5h
7. God 组件拆分 (3 文件)           →  8h   ─ 见阶段 9
8. PRD 更新                        →  1h
                                   ─────
                                    14.5h
```

## 阶段 9：God 组件拆分（专项，另立项）

| 文件 | 行数 | 拆分方案 |
|------|:--:|------|
| DirectoryTree | 960 | 接入 useBatchSelect + 提取 useContextMenu（已分析，见前序复杂度分析） |
| StepEditor | 957 | 提取 useElementLibrary + useStepExecution + ContainerStepChildren.vue（已分析） |
| CaseEditor | 761 | 提取 useEditLock + useFormDirty + 基本信息区子组件 |

---

## 验证

```bash
npx vite build --mode development
grep -rn "client\.\(get\|post\)" modules/case-manager/ --include="*.vue" | grep -v api.js
ls modules/case-manager/constants.js
```
