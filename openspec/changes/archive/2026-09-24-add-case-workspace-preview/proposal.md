## Why

用例管理项目工作台与元素定位工作台是同一套版式（列表 → 项目台 → 文件叶子），但上一轮只给元素定位加了「左树 + 右预览」。用例这边点开一个用例文件仍要整页跳走，核对多个文件里的用例没有概览位。需求方要求给用例工作台补同样的右栏预览，且预览**只显示五列：用例 ID / 测试类型 / 业务类型 / 标题 / 时间**。

## What Changes

- 用例管理项目工作台改为**左目录树 + 右用例预览**的分栏版式；宽屏（≥1280px）点文件不再整页跳走，窄屏退化为既有两页流程。
- 右栏预览**只读**，固定五列：**用例 ID · 测试类型 · 业务类型 · 标题 · 时间**；其余列（模块 / 前置 / 步骤 / 预期结果 / 操作）与全部编辑能力只在文件详情页。
- 右栏分页呈现该文件全部用例（每页 10 行 + 「第 X / Y 页 · 共 N 条」+ 上一页 / 下一页，边界禁用），并只保留**一个**「进入页面编辑」入口（固定标题行）。
- 左栏固定宽度取模块令牌；页头副标题给出内容概况（N 个目录 · M 个文件）。

## 关联文档

PRD-05 · ARCH-05

## Capabilities

### New Capabilities

- `case-manager-workspace-preview`: 用例管理项目工作台的左树右预览版式，以及右栏「只读 · 五列 · 可分页 · 单一编辑入口」的预览契约

### Modified Capabilities

（无）

## Impact

- 前端模块：`frontend/src/modules/case-manager/`
  - `ProjectWorkspace.vue`（分栏版式与选中态）
  - 新增 `components/CasePagePreview.vue`（只读预览表）
  - `tokens.css`（左栏宽度令牌 `--case-tree-pane-w`）
- 顺带对齐（G7 门禁）：两个工作台的左栏宽度令牌改为引用 T0 统一分栏档位 `var(--layout-pane-left)`（280px），不再写 320px 字面量；`element-locator/tokens.css` 同步改一行（左栏由 320px 变 280px，观感差异可忽略）
- 复用既有 `getFileSheet` 端点与 `usePagination`，零后端改动
- 不改 `ProjectTree.vue` 的树皮肤与拖拽行为（本次只加右侧预览）
- 不在本单：`case-manager-projects` 主 spec 的补齐（该能力在 `openspec/specs/` 下仍缺主 spec，属既有漂移）；并把工作台断点从 1280px 迁到 T0 登记的 `lg = 1200px` 档位（tokens.css 注明该迁移需视觉确认，另立一单）
