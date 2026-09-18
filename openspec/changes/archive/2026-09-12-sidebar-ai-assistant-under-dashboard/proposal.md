## Why

侧栏底部独立分组「AI助手」把高频入口压到折叠区外，且分组标题与展开项「AI 助手」重复。需要把该入口上移到仪表盘正下方，并去掉冗余分组标题。

## What Changes

- 将「AI 助手」可展开项（含子页）从独立分组移到「仪表盘」下方
- 删除分组标题「AI助手」（不再渲染 `sidebar__group-label`）
- 不改路由 path、子项、图标、账号区与折叠/拖宽行为

## 关联文档

无独立 PRD。侧栏入口落位约定见 `frontend/AGENTS.md`（`sidebarNavConfig.ts` 为导航唯一真相源）。视觉仍遵循已归档的 L1 doodle 侧栏口径。

## Capabilities

### New Capabilities

- `frontend-sidebar-nav`: 侧栏导航分组顺序与可见分组标题

### Modified Capabilities

- （无）现有 `frontend-sidebar-hand-drawn` 只约束侧栏视觉 chrome，不约束入口顺序

## Impact

- `frontend/src/shared/components/sidebarNavConfig.ts`：`NAV_CATEGORIES` 结构调整
- `frontend/AGENTS.md`：分组数量描述同步
- 路由与 `MOD_COLORS` 不变；无后端影响
