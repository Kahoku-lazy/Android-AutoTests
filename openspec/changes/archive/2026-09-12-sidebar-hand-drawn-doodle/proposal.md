## Why

主内容区已按 `temps/hand-drawn-doodle-sidebar.html` 收敛为暖白纸面 + 涂鸦，但 L1 侧栏仍是粗实线边框与旧 active 书签条，和原型「虚线分隔 / 黄底微倾 / 偏移色块阴影 / 方框图标」不一致。现在改侧栏视觉对齐模板，同时保留现有中文文案与 Lucide SVG。

## What Changes

- 将 `AppSidebar` 视觉改为 hand-drawn doodle 侧栏风格：暖纸底、右侧虚线、品牌黄方块 mark、导航 hover/active 微旋转与偏移阴影
- 保留全部导航文案、路由、折叠/拖宽/账号菜单/退出逻辑
- 保留 Lucide SVG 图标形态；外层加模板式描边方盒，描边/填充色走主题令牌
- active 偏移阴影色优先用模块色 `--c-*`（无则回退 `--c-case` 青绿，对齐模板 teal）
- **不**改主区涂鸦层、**不**改顶栏结构（顶栏虚线对齐若需另开变更）

## 关联文档

- UI 参考原型：`temps/hand-drawn-doodle-sidebar.html`（`.sidebar` / `.brand` / `.nav-item`）
- 前端分层：`frontend/AGENTS.md`（L1 侧栏只读归属）
- 主题技能：`.agents/skills/doodle-craft/`（令牌不硬编码）
- 无独立 PRD/ARCH 编号；属 L1 视觉对齐，不改业务接口

## Capabilities

### New Capabilities

- `frontend-sidebar-hand-drawn`: L1 侧栏 hand-drawn doodle 视觉行为与约束（文案/路由/SVG 保留）

### Modified Capabilities

- （无；`openspec/specs/` 下暂无既有侧栏视觉能力）

## Impact

- 前端：`frontend/src/shared/components/AppSidebar.vue`、`AppSidebar.style.css`（必要时微调模板结构以容纳 brand-mark）
- 可能微调 `sidebarNavConfig.ts` 仅当需要展示层 class，不改 path/label/icon 语义
- 令牌：优先复用 `--ink` / `--paper` / `--app-highlight` / `--c-*`；若缺「虚线描边宽度」可在 tokens 补极少量侧栏专用变量
- 不影响 API、鉴权、模块路由；登录页无侧栏不受影响
- 目视验收：展开/折叠、各模块 active、账号菜单
