# BUG 单表格：列头图标 + 首列身份单元 + 表纸去影

## Why

BUG 单列表和设备列表现在是同一类「扁列表」，但长相完全不同：BUG 表头是纯文字、首列只有一串编号、开着 `border` 画了列线、表纸还压着一层 `--c-runner` 位移硬影。设备表刚做完「列头图标 + 首列身份单元 + 无影表纸」，两张表放在同一产品里应当读成同一套语言。

## What Changes

- 六个列头各加一个图标（emoji），列名保持纯文字。
- 首列改为身份单元：图标圆 + `BUG-0057`（主）+ 创建时间（副）；**独立「创建时间」列随之移除**，列数 7 → 6（信息上移，不在两列重复）。
- 关掉 `AppTable` 的 `border`（不再画列线），行分隔与表头分栏仍由既有皮肤承担。
- BUG 表纸去掉 `--c-runner` 位移硬影，描边与圆角保持共享令牌不变。
- 分类 Tab、状态下拉、关键字搜索、显示行数、分页位置、操作键（`DoodleBtn`）全部不动。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- `bug-ticket-management`：新增「BUG 列表列头与首列身份单元」的行为要求（列头图标、身份单元、无列线、列数变化）。
- `frontend-doodle-sketch-table`：无影变体从「仅设备页」扩展为「已登记无影页清单（设备管理页、BUG 单管理页）」；新增 BUG 页的无影要求。

## Impact

- 前端 `bug-manager` 模块：`constants.ts`（列定义）、`index.vue`（表头插槽 + 首列组件 + 去 `border`）、新增 `components/BugIdentityCell.vue`、`index.style.css`（去影 + 身份单元样式）。
- 不改后端、接口、筛选条件、分页与详情抽屉；共享 `AppTable` / `DoodleBtn` / `tokens.css` 不动。
