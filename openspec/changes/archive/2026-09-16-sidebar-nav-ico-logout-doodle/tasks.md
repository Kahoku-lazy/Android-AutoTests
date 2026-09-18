## 1. 令牌

- [x] 1.1 在 `frontend/src/shared/styles/tokens.css` 增加 `--app-marker-red: #ff6b6b`，并在 `frontend/DESIGN_SYSTEM.md` 色板注明仅用于 doodle 危险 CTA；`rg` 确认无第二处硬编码该色

## 2. 侧栏样式

- [x] 2.1 将 `.nav-ico` 底色改为 `var(--mod-color)`，去掉 active 白底覆盖；浏览器侧栏可见各模块色块且 active 不回白
- [x] 2.2 `.logout-btn` 与 `.sidebar__icon-logout` 使用 `--app-marker-red` 实心底、墨边、浅色文字、扁平阴影；`AppSidebar.vue` 去掉退出按钮 `link`/`danger`；展开/折叠两态均为红底

## 3. 验收

- [x] 3.1 浏览器走一遍展开导航、active、折叠退出；`cd frontend && npx vite build --mode development` 通过
