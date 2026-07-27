# PRD-03 — 用例管理 (Case Manager)

> 关联需求大纲：[`需求大纲.md`](./需求大纲.md) §5.3
> 版本：v6.0 · 日期：2026-07-27

---

## 1. 功能定位

用例管理是测试资产管理中枢。用户在此创建、组织、编排 4 类测试用例（UI 自动化 / Web 自动化 / 存储流程 / API 测试），通过步骤编排器编写设备操作序列。页面由左侧目录树 + 右侧内容区（4 个类型 Tab）构成。

---

## 2. 设计目录

```
frontend/src/modules/case-manager/
├── index.vue                         248 行 · 页面编排者（4 Tab + 目录树容器）
├── index.css                         636 行 · 全局样式（⚠ 独立文件，非 scoped）
├── api.js                             61 行 · 数据层 facade（⚠ 仅 2/10 组件使用）
├── routes.js                          34 行 · 路由定义
├── step-utils.js                     153 行 · 步骤工具函数（28 种类型 + 摘要渲染）
├── composables/
│   ├── useCaseManager.js              27 行 · 工具函数（⚠ 未使用）
│   ├── useBatchSelect.js              99 行 · 批选模式（⚠ DirectoryTree 未使用）
│   ├── useStepDragDrop.js             49 行 · 步骤拖拽排序
│   └── useStepFields.js               48 行 · 步骤字段定义 + 元素选取器标记
├── api/
│   ├── directories.js                 36 行 · 目录 CRUD + 批量移动
│   ├── uiAutomation.js                89 行 · UI 用例 CRUD + 锁 + 跨模块设备/元素
│   ├── storage.js                     29 行 · 存储用例 CRUD
│   ├── apiTesting.js                  29 行 · API 测试用例 CRUD
│   └── webAutomation.js               29 行 · Web 用例 CRUD
├── CaseEditor.vue                    759 行 · UI 自动化用例编辑器
└── components/
    ├── DirectoryTree.vue             960 行 · 目录树（右键菜单/拖拽/批选）
    ├── CaseCard.vue                  263 行 · 用例卡片（卡片视图）
    ├── StepEditor.vue                917 行 · 步骤编排器（类型选择/字段/拖拽/运行）
    ├── StepViewer.vue                187 行 · 步骤只读查看器
    ├── WatcherPanel.vue              167 行 · 弹窗监控配置面板
    ├── ui/UiCaseList.vue             287 行 · UI 用例列表（卡片/表格双视图）
    ├── web/WebCaseList.vue           221 行 · Web 用例列表
    ├── web/WebCaseEditor.vue         160 行 · Web 用例编辑器（表格式）
    ├── api/ApiCaseList.vue           242 行 · API 用例列表
    └── storage/StorageCaseList.vue   232 行 · 存储用例列表
```

**架构特征**：L2 评级。数据层结构完善（5 子 API 模块），但逻辑层薄弱——4 个 composable 中 2 个未使用、1 个半废弃（facade）。4 个 CaseList 组件约 70% 逻辑重复。裸 client 调用已于 v6.0 全部收敛到 api/uiAutomation.js。

---

## 3. 核心功能

### 3.1 左侧目录树

`DirectoryTree.vue` + `index.vue.treeCache` — 按 4 种类型独立缓存目录树。每类型一棵树，切换 Tab 时复用缓存。

#### 3.1.1 目录操作

el-tree 树形结构，最大 2 级深度。右键菜单：新建子目录 / 新建用例 / 重命名 / 删除。长按 500ms 激活拖拽模式。同级目录名不可重复，删除含用例的目录需二次确认。批选模式：勾选 → 批量移动到目标目录。

#### 3.1.2 用例节点

每个用例节点显示优先级标签（P0=红 / P1=黄 / P2=灰）。禁用用例显示删除线 + 灰色。当前激活节点高亮。

### 3.2 右侧用例列表（4 个类型 Tab）

4 个 `*CaseList.vue` 组件共享相同结构：工具栏（面包屑 + 计数 + 视图切换）→ 卡片视图 / 表格视图。

**视图模式**：
- 卡片视图：CSS grid 自适应列（minmax 320px），每张卡片显示优先级/标题/创建人/修改时间/步骤数/锁定状态
- 表格视图：AppTable 渲染，列因类型而异（UI/Web/API/Storage 各有专属列）

**通用操作**：新建用例 → 跳转编辑器。点击卡片详情 → 右侧面板展开步骤预览。编辑锁状态实时显示（🔒/🔓）。30 秒自动刷新。

**UI 类型特有**：CaseCard 子组件渲染，支持 YAML 导出。详情面板使用 StepViewer 展示步骤。

### 3.3 用例编辑器

`CaseEditor.vue` (UI) + `WebCaseEditor.vue` (Web) — 全屏编辑器。

#### 3.3.1 UI 自动化编辑器

顶部 PageHeader + 元数据表单（标题/优先级/目录选择器）+ 步骤编排器（StepEditor）+ 弹窗监控面板（WatcherPanel）。

**StepEditor** — 17 种步骤类型按 6 类分组：点击/手势/等待/验证/应用/控制。每步骤根据类型动态显示字段（XPath/超时/方向/距离/期望文本等）。元素选取器内嵌搜索面板（从已保存元素中按页面+别名搜索）。HTML5 拖拽排序。单步试运行（需连接调试设备）。EventBus 接收 `add-step-to-case`（从元素定位页发送的 XPath）。

**WatcherPanel** — 弹窗/Toast 监控配置。每监控项包含元素 XPath + 点击动作。支持新增/删除。

#### 3.3.2 Web 自动化编辑器

`WebCaseEditor.vue` — 表格式编辑器。动态列（7 个默认列 + 用户自定义列），可编辑行。

### 3.4 协作编辑

**编辑锁**：打开编辑器自动获取锁 → 他人打开时只读模式（黄色横幅「用例正被 XX 编辑中」）。锁超时 30 分钟自动释放。创建者可强制踢出。

**持久锁**：创建者可将用例锁定（🔒），任何人不可编辑（除创建者外）。仅创建者可解除。

**可见性控制**：public（默认全员可见）/ hidden（仅创建者）/ restricted（指定用户）。

**权限管理**：edit（全员可编辑）/ readonly（仅创建者可编辑）/ restricted（指定用户可编辑）。

### 3.5 YAML 导入导出

UI 类型支持多选用例导出为 YAML 文件（含 ID/标题/步骤 JSON/优先级/包名）。从 YAML 文件批量导入（最多 500 条/次，ID 冲突可选跳过或覆盖）。

---

## 4. 数据流

```
index.vue (treeCache + activeDirectoryId + activeTab)
  │
  ├── DirectoryTree (props: treeData, activeId, caseType)
  │     emit: select → handleDirSelect → 更新 activeDirectoryId
  │     emit: refresh → loadTree → 更新 treeCache[tab]
  │
  └── CaseList × 4 (props: activeDirectoryId, treeData)
        emit: refresh-tree → handleTreeRefresh → loadTree
        │
        └── 内部状态 (definitions, loading, viewMode, selectedCase)
             └── loadDefs() → 类型 API → 更新 definitions
             └── 30s setInterval 自动刷新
             └── CaseCard/StepViewer 子组件（UI 类型专属）

CaseEditor (独立路由, 不共享状态)
  ├── loadDevices() → api/uiAutomation.js
  ├── loadDirOptions() → api/directories.js
  ├── StepEditor → useStepDragDrop + useStepFields
  │     → bus.on('add-step-to-case') ← 来自 element-locator
  └── WatcherPanel → 加载元素库

跨模块：
  用例管理 ←──bus.on('add-step-to-case')── 元素定位
  工作流 ←──import { listDefinitions }── 用例管理 api.js (⚠ 耦合)
```

---

## 5. 验收汇总

| 功能编号 | 功能名称 | 验收项 | 通过 | 未验证 |
|:--:|------|:--:|:--:|:--:|
| F-01-01 | 目录树展示 | 5 | | 5 |
| F-01-02 | 目录操作 | 7 | | 7 |
| F-02-01 | UI 用例 CRUD | 6 | | 6 |
| F-02-02 | Web 用例管理 | 4 | | 4 |
| F-02-03 | API 用例管理 | 4 | | 4 |
| F-02-04 | Storage 用例管理 | 4 | | 4 |
| F-03-01 | 步骤编排器 | 6 | | 6 |
| F-03-02 | 元素选取器 | 5 | | 5 |
| F-04-01 | YAML 导出 | 4 | | 4 |
| F-04-02 | YAML 导入 | 5 | | 5 |
| F-05-01 | 编辑锁 + 强制编辑 | 8 | | 8 |
| F-05-02 | 持久锁 + 可见性 + 权限 | 12 | | 12 |
| F-06-01 | 卡片/列表/编辑页数据同步 | 5 | | 5 |
| **合计** | | **75** | **0** | **75** |

---

## 附录A：测试优先级

| 优先级 | 覆盖范围 | 验收时机 |
|:--:|------|------|
| P0 | F-01-01~F-03-01（目录+编辑+编排） | 每次 MR 前 |
| P1 | F-03-02~F-04、F-05-01~F-05-02（元素选取+YAML+协作锁） | 发版前 |
| P2 | F-06（数据同步）、Web/API/Storage 列表 | 大版本前 |

## 附录B：实施状态

| 功能 | 状态 |
|------|:--:|
| 目录树 + 拖拽移动 + 批选 | ✅ |
| 4 类用例 CRUD + 启用/禁用 | ✅ |
| 17 种步骤编排 + 元素选取器 | ✅ |
| YAML 导入导出 | ✅ |
| 编辑锁/持久锁/强制编辑 | ✅ |
| 创建人/修改人追踪 | ✅ |
| 可见性控制 + 权限管理 | ✅ |
| 卡片编辑状态 + 锁定按钮 | ✅ |
| 裸 client 收敛到 api/uiAutomation.js | ✅ v6.0 |
| Web 用例编辑器 | ✅ |
| 4 个 CaseList 合并为通用组件 | 📋 |
| api.js facade 删除（统一走子 API 模块） | 📋 |
| useBatchSelect 死代码清理 | 📋 |
| DirectoryTree 960 行拆分 | 📋 |
| StepEditor 917 行拆分 | 📋 |
| index.css 636 行迁移为 scoped | 📋 |
| Storage/API 用例编辑器开发 | 📋 |

## 附录C：已知问题与改进项

| 编号 | 问题 | 严重度 | 记录日期 |
|:--:|------|:--:|:--:|
| IMP-01 | DirectoryTree.vue 960 行超标（1.9x），应拆出 context-menu/dialog 子组件 | 🔴 | 2026-07-27 |
| IMP-02 | StepEditor.vue 917 行超标（1.8x），步骤运行逻辑可拆到 composable | 🔴 | 2026-07-27 |
| IMP-03 | 4 个 CaseList 组件 ~70% 逻辑重复（~680 行），应提取通用 CaseList.vue | 🟠 | 2026-07-27 |
| IMP-04 | api.js facade 仅 2/10 组件使用，半废弃状态；应删除或强制统一 | 🟠 | 2026-07-27 |
| IMP-05 | useBatchSelect.js 和 useCaseManager.js 为死代码，未被任何组件导入 | 🟡 | 2026-07-27 |
| IMP-06 | index.css 636 行为独立文件（非 scoped），是唯一有此模式的模块 | 🟡 | 2026-07-27 |
| IMP-07 | step-utils.js STEP_TYPES/FIELD_LABELS 与 shared/constants/steps.js 重复定义 | 🟡 | 2026-07-27 |
| IMP-08 | 116 处硬编码 hex 颜色分散在 12 个 .vue scoped CSS 中 | 🟡 | 2026-07-27 |
| IMP-09 | Storage/API 类型的编辑器路由存在（/cases/storage/new 等）但组件不存在 | 🟡 | 2026-07-27 |
