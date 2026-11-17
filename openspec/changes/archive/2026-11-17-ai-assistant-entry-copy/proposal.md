# 平台助手入口：去分组标题、改名、助手区补区块标题条

## Why

侧栏「AI 功能」分组只剩一条入口，标题行是多余的；入口与页头都叫「AI 助手」，与模块里真正列出来的「AI 助手」名片同名，读起来容易混。另外助手区顶部只有一行「共 3 位助手 …… 新建助手」，没有区块标题，而下面工作流区有「工作流 共 1 条」，两个区块一个有一个没有，结构不对称。

## What Changes

- 侧栏「AI 功能」分组不再渲染分组标题（`label` 置空），入口直接跟在仪表盘之后。
- 入口名与页头主标题由「AI 助手」改为「平台助手」：侧栏文案、`WorkbenchHeader` 标题、路由 `meta.title`（浏览器标签页）三处同步。
- 助手区新增区块标题条：`AI 助手 · 共 N 位助手 ······ 新建助手`，与工作流区的 `工作流 · 共 N 条 ······ 新建工作流` **同一位置、同一几何**。
- 两处标题条抽成模块内共享件 `components/SectionBar.vue`（标题 / 计数 / 右侧动作插槽），`index.vue` 与 `SopWorkflowSection.vue` 都用它，避免两份手写样式漂移。

## 关联文档

无关联 PRD 编号：需求方 2026-11-17 按页面截图直接提出的命名与区块结构统一。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- `frontend-sidebar-nav`：入口名改为「平台助手」，且该分组 MUST NOT 渲染标题。
- `ai-assistant/assistant-board-layout`：新增「助手区与工作流区标题条同构」要求，并约定页头主标题为「平台助手」。

## Impact

- `frontend/src/shared/components/sidebarNavConfig.ts`（入口文案、`ai` 分组 label 置空）
- `frontend/src/modules/ai-assistant/index.vue`（页头标题、区块标题条）
- `frontend/src/modules/ai-assistant/routes.ts`（`meta.title`）
- `frontend/src/modules/ai-assistant/components/SopWorkflowSection.vue`（改用共享标题条）
- `frontend/src/modules/ai-assistant/components/SectionBar.vue`（新增）
- `frontend/tests/shared/p0/sidebarNavConfig.spec.ts`（入口名与分组标题期望）
