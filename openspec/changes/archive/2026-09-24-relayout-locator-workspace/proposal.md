## Why

元素定位项目工作台（`/elements/projects/:code`）把 15 个节点摊成 15 条 1152px 通栏墨框：主区 1192px 里横向 96% 的面积被描边本身占据，名字与行尾「进入」相隔 ≈950–1050px，目录与页面只差 12px 缩进而形状完全相同；而整棵树只有 576px 高、可用 716px——一屏装得下、根本不需要滚动，问题不是挤而是空。同时「项目根」落点常驻第一行（只在拖拽时有用），看一个页面要两次整页跳转（13 个页面 = 26 次，每次跳转都重置树的滚动与勾选）。本次把工作台整理成左树右元素表的分栏台，并让树的层级与落点时机回归语义。

## What Changes

- **工作台改为分栏台**：目录树收进固定宽度左栏，右栏并置「当前选中页面」的元素表；宽屏下在树里点页面 MUST NOT 再整页跳走。
- **目录树紧凑呈现**：行默认不画描边，悬停 / 选中才给底色与描边；层级改用更大缩进加虚线引导线表达；目录尾随子项数（空目录显示「空」而不是「0」）；页面行的进入指示紧贴名称。
- **项目根落点按需出现**：只在拖拽进行中或批量选择模式下出现，平时不占一行；落点判定与端点 MUST NOT 变化。
- **页头概况**：页头副标题由操作说明改为内容概况（N 个目录 · M 个页面）。
- **窄屏退化**：视口 <1280px 时不并置，点页面沿用既有 `/files/:fileId` 整页详情，深链与面包屑不变。

## 关联文档

PRD-04 · ARCH-04

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `element-locator-projects`: 新增项目工作台的分栏版式、目录树紧凑呈现、项目根落点出现时机与窄屏退化四项要求
- `element-locator-page-workbench`: 新增「元素表在工作台右栏复用」要求（同一张七列表纸与硬边按键皮肤，不删列）

## Impact

- 前端模块：`frontend/src/modules/element-locator/`
  - `ProjectWorkspace.vue`（分栏版式与选中态）、`components/LocatorTree.vue` + `components/LocatorTree.style.css`（紧凑行、层级引导线、落点时机）
  - 新增 `components/elementDetailSkin.css`（硬边按键皮肤与表纸线型，由工作台右栏与文件详情页共用）
  - `LocatorFileView.vue`（改引共享皮肤文件，行为不变）
- 测试：`frontend/tests/element-locator/p0/`
- 零后端改动：端点、信封、写库路径、拖拽双通道与批量的判定口径全部不变
- 不在本单：用例管理工作台的同步改版（该能力在 `openspec/specs/` 下没有主 spec，需先补 spec 再改）
