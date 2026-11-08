## 1. 配置

- [x] 1.1 `sidebarNavConfig.ts`：新增 `NavItem` / `NavCategory` 类型（`isDev?` / `badge?` / `badgeClass?` / `children?`），给 `/knowledge-assistant` 与 `/workflow` 加 `isDev: true`。验证：`vue-tsc` 通过。**验证结果**：tsc 0。
- [x] 1.2 关闭态行为由模板已有 `v-if="(item.isDev || item.badge) && !collapsed"` 保证，不改模板。验证：折叠态无徽标。**验证结果**：模板未改，条件已含 `!collapsed`。

## 2. 样式

- [x] 2.1 `AppSidebar.style.css`：`.sidebar-menu__badge--dev` 改红色语义（`--app-status-danger-bg` / `--app-status-danger-text`），字号 12px、内距 `1px 6px`；补 `.sidebar-menu__item.active .sidebar-menu__badge--dev` 防止被选中态白底覆盖。验证：`lint:styles` 批 2 通过。**验证结果**：批 2 通过。

## 3. 门禁

- [x] 3.1 `npx vue-tsc --noEmit`、`npm run build:check`、`npx vitest run tests/shared`、`npm run lint:lines`。验证：全绿。**验证结果**：tsc 0；build 46.7s；11 文件 49 passed；虚线 0 处。
- [ ] 3.2 目视：展开/折叠/选中三态。验证：用户确认。
