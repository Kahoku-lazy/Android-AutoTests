## Why

侧栏 `.nav-ico` 目前是白底墨框，与 `temps/hand-drawn-doodle-sidebar.html` 中「每项一块马克笔色」不一致，模块辨识度弱。账号区「退出」是白底 link 按钮，危险操作不够醒目，也未对齐参考稿的红色实心底。

## What Changes

- 导航项 `.nav-ico` 使用已注入的 `--mod-color`（8 模块色）作为色块底，墨色粗边与 Lucide 描边保持不变。
- 展开态 `.logout-btn` 改为红色马克笔实心按钮（墨边 + 扁平偏移阴影），对齐参考稿 `.btn-primary` / `--red` 语义。
- 折叠态 `.sidebar__icon-logout` 同步红色，避免展开/折叠两套语义。

## 关联文档

- UI 规范：`frontend/DESIGN_SYSTEM.md`（Doodle Craft 令牌与硬性约束）
- 风格参考：`temps/hand-drawn-doodle-sidebar.html`
- 无独立 PRD / ARCH：纯 L1 侧栏视觉迭代，不改导航结构与鉴权流程。

## Capabilities

### New Capabilities

- `frontend/sidebar-doodle`: 侧栏导航图标色块与退出按钮的 doodle 视觉行为

### Modified Capabilities

- （无）`openspec/specs/` 下尚无对应能力

## Impact

- 前端：`frontend/src/shared/components/AppSidebar.style.css`（主改）；必要时微调 `AppSidebar.vue` 仅当 EP `link` 按钮无法压过红色实心样式
- 令牌：若现有 `--app-status-danger` / `--c-runner` 不足以表达参考稿朱红，则在 `tokens.css` + `DESIGN_SYSTEM.md` 增加侧栏危险红并引用变量
- API / 鉴权 / `sidebarNavConfig` 路由与 `--mod-color` 映射：不改
- 测试：侧栏视觉回归（浏览器展开/折叠/active/hover）
