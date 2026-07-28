# PRD-08 — 工作流工作台 (Workflow Workbench)

> 关联需求大纲：[`需求大纲.md`](./需求大纲.md) §5.7
> 版本：v4.0 · 日期：2026-07-27

---

## 1. 功能定位

工作流工作台是平台的可视化编排中枢。用户在此通过 Blockly 积木块或 VueFlow 节点图编排自动化流程。模块提供文件系统风格的资源管理、跨编辑器拖拽式工作流构建，以及与用例管理模块的互操作。页面由左侧目录树 + Blockly/VueFlow 双编辑器 + 右侧文件浏览器构成。

---

## 2. 设计目录

```
frontend/src/modules/workflow/
├── index.vue                         768 行 · 页面编排者（目录树 + 编辑器 + 文件浏览器）
├── api.js                            107 行 · 数据层（23 端点）
├── routes.js                           8 行 · 路由定义
├── constants.js                       86 行 · L4 达标（字符串常量集中管理）
├── stores/
│   ├── workflowStore.ts              787 行 · ComfyUI 风格节点图状态
│   ├── testCaseStore.ts              550 行 · Blockly 块树 + 模拟执行
│   └── libraryStore.ts               627 行 · 文件系统风格资源库 CRUD（⚠ 18 处 ElMessage）
├── composables/
│   ├── useVueFlowAdapter.ts          219 行 · VueFlow 节点/边转换 + 连接验证
│   ├── blocklyBlocks.ts              162 行 · Blockly 块类型注册
│   ├── blocklySerializer.ts          191 行 · Blockly ↔ Store 树序列化
│   ├── caseBridge.ts                 121 行 · 步骤格式桥接（与 case-manager 互操作）
│   └── useImportExport.ts            135 行 · JSON 导入导出 + 剪贴板
├── types/
│   ├── testCase.ts                   203 行 · 步骤类型定义 + 颜色常量
│   ├── workflow.ts                   181 行 · 节点/边/端口类型 + 元素池
│   └── pageCatalog.ts                257 行 · 页面/元素目录加载器（⚠ 裸 api-client）
├── registry/
│   └── nodeRegistry.ts                76 行 · ComfyUI 风格节点类映射
└── components/
    ├── WorkflowDirTree.vue           660 行 · 左侧目录树（拖拽 + 展开折叠）
    ├── WorkflowFileBrowser.vue       523 行 · 右侧文件浏览器（卡片网格）
    ├── ImportCasesDialog.vue         310 行 · 从用例管理导入（⚠ 跨模块 import）
    ├── blockly/
    │   ├── TestCaseBlockly.vue       697 行 · Blockly 编辑器宿主 + 工具栏
    │   └── ScratchPalette.vue        254 行 · Blockly 调色板侧栏
    └── vueflow/
        ├── PageFlowVueFlow.vue       797 行 · VueFlow 画布宿主 + 工具栏
        ├── PageFlowNode.vue          496 行 · 自定义 VueFlow 节点
        └── NodeContextMenu.vue       341 行 · 右键上下文菜单 (Teleported)

合计：24 文件 / 8,556 行
```

**架构特征**：L3 评级（项目仅有的两个 L3 模块之一，与 ai-assistant 并列）。TypeScript 类型系统完善（types/ 3 文件 641 行），Pinia 三层 Store 结构合理，constants.js 达标。但存在 3 处违规：libraryStore 直接调用 ElMessage（18 处，最严重）、ImportCasesDialog 跨模块 import case-manager/api.js、pageCatalog 动态裸 import api-client。共享组件采用率为 0/14——模块完全自建 UI。8/24 文件超标（33%，所有模块中比例最高）。

---

## 3. 核心功能

### 3.1 资源库与目录树

`libraryStore.ts` + `WorkflowDirTree.vue` + `WorkflowFileBrowser.vue` — 文件系统风格的资源管理。支持文件夹/测试用例/页面流三种资源类型。左侧树支持拖拽移动、展开折叠（localStorage 持久化）。右侧卡片网格展示文件，hover 显示操作按钮。服务端 CRUD 备份（createFolder/createPageFlow/createTestCase/renameNode/deleteNode/moveNode）。

`bootstrapIfEmpty` 首次运行自动初始化 Demo 资源。

### 3.2 Blockly 测试用例编辑器

`TestCaseBlockly.vue` + `testCaseStore.ts` + `blocklyBlocks.ts` + `blocklySerializer.ts` — 17 种步骤类型注册为积木块，按 6 类分组显示在 ScratchPalette 侧栏。Blockly workspace ↔ Store `rootBlocks` 树双向序列化。支持模拟执行（前端随机化 pass/fail）。导出为 JSON 文件。

### 3.3 VueFlow 页面流编辑器

`PageFlowVueFlow.vue` + `workflowStore.ts` + `useVueFlowAdapter.ts` — ComfyUI 风格节点图编辑器。节点从注册表 (`nodeRegistry.ts`) 按类名创建，每个节点有输入/输出端口。端口颜色按类型区分（element=蓝, boolean=绿, text=橙, intent=紫, action=红）。连线验证（类型兼容检查）。右键菜单（NodeContextMenu）支持重命名/删除。画布支持缩放、平移、小地图。

### 3.4 用例导入桥接

`ImportCasesDialog.vue` + `caseBridge.ts` — 从用例管理模块导入现有用例，转换为工作流 Blockly 步骤。**当前实现存在跨模块违规**：直接 import `listDefinitions` from `@/modules/case-manager/api.js`。修复方案：通过 workflow 自己的 api.js 调用（已有同签名函数 `listDefinitions`）。

---

## 4. 数据流

```
Pinia Stores (3)
  ├── workflowStore     节点图状态 (nodes/links/ports) → VueFlow 渲染
  ├── testCaseStore     Blockly 块树 → Blockly workspace → blocklySerializer
  └── libraryStore      资源库 CRUD → api.js → Django

Composables
  ├── useVueFlowAdapter  Store ↔ VueFlow 格式转换
  ├── blocklyBlocks      块类型注册 → Blockly 引擎
  ├── blocklySerializer  双向序列化
  ├── caseBridge         步骤格式桥接
  └── useImportExport    JSON 文件导入导出 + 剪贴板

index.vue
  ├── WorkflowDirTree    → libraryStore
  ├── TestCaseBlockly    → testCaseStore + blocklySerializer
  ├── PageFlowVueFlow    → workflowStore + useVueFlowAdapter
  └── WorkflowFileBrowser → libraryStore

跨模块:
  ImportCasesDialog → ⚠ case-manager/api.js（违规，应走 workflow/api.js）
```

---

## 5. 验收汇总

| 功能编号 | 功能名称 | 验收项 | 通过 | 未验证 |
|:--:|------|:--:|:--:|:--:|
| F-01-01 | 目录管理（CRUD + 拖拽 + 展开折叠） | 5 | | 5 |
| F-01-02 | 文件浏览器（卡片网格 + 操作） | 3 | | 3 |
| F-02-01 | Blockly 编辑器（17 种块 + 序列化） | 5 | | 5 |
| F-02-02 | 同步到用例库 | 3 | | 3 |
| F-02-03 | 从用例库导入 | 3 | | 3 |
| F-03-01 | VueFlow 页面流编辑器 | 5 | | 5 |
| F-04-01 | 运行时/调试 | 7 | | 7 |
| **合计** | | **31** | **0** | **31** |

---

## 附录A：测试优先级

| 优先级 | 覆盖范围 | 验收时机 |
|:--:|------|------|
| P0 | F-01-01~F-02-02（目录 + Blockly + 同步） | 每次 MR 前 |
| P1 | F-02-03（导入）+ F-03-01（VueFlow） | 发版前 |
| P2 | F-04（运行时调试） | 大版本前 |

## 附录B：实施状态

> 验收日期：2026-07-27（文档优化阶段复查）

| 功能 | 状态 |
|------|:--:|
| 目录树 + 拖拽 + 展开折叠（libraryStore） | ✅（已验证 2026-07-27） |
| 文件浏览器（WorkflowFileBrowser） | ✅（已验证 2026-07-27） |
| Blockly 编辑器 + 17 种积木块 | ✅（已验证 2026-07-27） |
| 同步到用例库（caseBridge） | ✅（已验证 2026-07-27） |
| 从用例库导入（ImportCasesDialog） | ✅（⚠ 含跨模块违规，已验证 2026-07-27） |
| VueFlow 页面流编辑器 + 自定义节点 | ✅（已验证 2026-07-27） |
| 首次运行 Demo 自举（bootstrapIfEmpty） | ✅（已验证 2026-07-27） |
| JSON 导入导出 | ✅（已验证 2026-07-27） |
| 跨模块 import 修复（case-manager → workflow/api.js） | 📋 |
| libraryStore 18 处 ElMessage 上移 | 📋 |
| pageCatalog.ts 裸 api-client → api.js | 📋 |
| WorkflowDirTree 660 行 → 拆分 | 📋 |
| PageFlowVueFlow 797 行 → 拆分 | 📋 |
| 运行时/调试 | 📋 |

## 附录C：已知问题与改进项

| 编号 | 问题 | 严重度 | 记录日期 |
|:--:|------|:--:|:--:|
| IMP-01 | libraryStore.ts 627 行 + 18 处 ElMessage 调用（BL 层引用 UI 层，最严重违规） | 🔴 | 2026-07-27 |
| IMP-02 | ImportCasesDialog.vue:7 跨模块 import case-manager/api.js（唯一跨模块违规） | 🔴 | 2026-07-27 |
| IMP-03 | PageFlowVueFlow.vue 797 行超标（+297），画布+工具栏+元素目录+API 面板全内联 | 🔴 | 2026-07-27 |
| IMP-04 | 8/24 文件超标 500 行（33%，所有模块比例最高） | 🟠 | 2026-07-27 |
| IMP-05 | 共享组件采用率 0/14，完全自建 UI（WorkflowDirTree 替代 GroupTreePanel 等） | 🟠 | 2026-07-27 |
| IMP-06 | 97 处硬编码 hex 颜色（53 vue + 44 ts）→ 2026-07-27 复查：ai-assistant 模块 ~140 处已替换为 `var(--ai-*)` 令牌（Phase 2）；workflow 模块 97 处待处理 | 🟡 | 2026-07-27 |
| IMP-07 | data/pageCatalog.ts:239 动态裸 import api-client，bypass api.js | 🟡 | 2026-07-27 |
