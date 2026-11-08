## Why

「知识库助手」与「页面流」两个入口仍在开发中，但侧栏没有任何提示，用户点进去看到半成品会误判为功能故障。需要在入口本身就把状态说清楚。

## What Changes

- 侧栏「知识库助手」「页面流」两项在右侧追加红色「开发中」标签；
- 标签用语义色（danger 底 + danger 字），选中态保持红色不被白底覆盖；
- 折叠态不显示标签（空间不足），仅在展开时出现。

## 关联文档

- 复用侧栏已有的 `.sidebar-menu__badge` 机制，不新增第二套标签样式。

## Capabilities

### New Capabilities

- 无

### Modified Capabilities

- `frontend-sidebar-nav`: 新增「开发中入口标签」要求。

## Impact

- 前端：`shared/components/sidebarNavConfig.ts`（新增 `isDev` 字段与类型）、`AppSidebar.style.css`（红色标签样式）。
- 后端 / 接口：无改动。
