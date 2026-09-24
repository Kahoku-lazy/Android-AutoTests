## Why

两个工作台的左栏（目录树）宽度写死在 T0 分栏档位（280px）：目录层级深、名称长时读不下，右栏表格宽时又想让左栏让位。侧栏早已支持鼠标拖动改宽度（`useSidebarResize`，180–360 + 折叠），工作台左栏却没有。需求方要求左侧目录栏支持鼠标左右拖动。

## What Changes

- 两个工作台的左右两栏之间新增**可拖动的分隔手柄**：按住左键左右拖动即改变左栏宽度，拖动中光标为 `col-resize`、正文不可选；松手生效并**记住**（同模块下次进入仍是该宽度）。
- 宽度**夹在上下限之间**：下限 220px，上限同时受「容器宽度 − 右栏最小可用宽度（360px）」与 560px 约束，保证右栏不会被挤没。
- 手柄**可键盘操作**：Tab 可聚焦，← / → 调 16px（Shift 加速到 48px），Home / End 到两端；并带 `role="separator"` / `aria-orientation` / `aria-valuenow|min|max`。
- **双击手柄复位**到默认档位（T0 `--layout-pane-left`，280px）。
- 窄屏（<1280px，两栏未并置）时**不渲染手柄**。

## 关联文档

PRD-04 · PRD-05

## Capabilities

### New Capabilities

- `frontend-split-pane`: 分栏台的左右拖动分隔手柄契约（鼠标拖动、宽度夹取、键盘可达、双击复位、持久化、窄屏不渲染）

### Modified Capabilities

（无）

## Impact

- 新增 `frontend/src/shared/components/SplitHandle.vue`（跨模块共享件）
- 两个工作台接入：`element-locator/ProjectWorkspace.vue`、`case-manager/ProjectWorkspace.vue`（分栏栅格加手柄列 + 宽度状态 + 持久化）
- 零后端改动；不改树与右栏预览的内部行为
- 不在本单：折叠左栏、按模块记住不同宽度之外的其它偏好
