## 1. 皮肤基建（页面作用域）

- [x] 1.1 从 `frontend/src/shared/components/AppSidebar.style.css:439-455` 逐字抄录参考几何（`2px solid var(--ink)` / `border-radius: 2px` / `box-shadow: 2px 2px 0 0 var(--ink)` / hover `translate(-1px,-1px)` + `box-shadow: 3px 3px 0 0 var(--ink)`），确认页根 `index.vue:67` 含 `.device-workbench` 作用域锚点
- [x] 1.2 在 `DevicePoolView.style.css` 新增「统一按键皮肤」一节并写入基础几何块，选择器覆盖 `.device-workbench :deep(.el-button)`、`:deep(.filter-tab)`、`:deep(.error-state__btn)`、`:deep(.card-btn)`、`.view-btn`、`.page-size-btn`，hover 用 `:not(:disabled):hover`；以 `npm run lint:styles` 为 0 验证
- [x] 1.3 在同一节登记角色底色：切换类未选中 `var(--c-workflow)`、选中 `var(--c-dashboard)`；`.action-bar-btn--network` = `var(--c-element)`；`.action-bar-btn--primary` = `var(--c-device)`；文字统一 `var(--ink)`

## 2. 页面自身按键收敛

- [x] 2.1 `.view-btn` / `.page-size-btn` 删除自带边框、圆角、背景与 transition，改为交由 1.2/1.3 的皮肤块承担；保留 `min-width`、`padding`、`cursor`、`font-size`
- [x] 2.2 `.view-toggle` 删除 `border` / `border-radius` / `overflow: hidden` 并改用 `gap`，`.view-btn` 删除 `border-right`（否则 2px 实边与硬阴影被容器裁掉）；以 Chromium 断言阴影未被裁剪验证
- [x] 2.3 `.action-bar-btn` 删除 `border` / `border-radius` / `color` / `box-shadow` 覆写（保留 `gap`、`padding`），新增 `.action-bar-btn--network` 承载紫底，删除 `.action-bar-btn:hover` 的背景覆写
- [x] 2.4 `index.vue` 给「局域网」按钮补 `action-bar-btn--network` 类名，确认「刷新」仍为 `action-bar-btn--primary`（绿）

## 3. 子组件冲突声明收敛

- [x] 3.1 `components/DeviceActionsCell.vue`：从 `.action-bar :deep(.el-button)` 删除 `border-radius` / `border-width`，从 `--primary` / `--danger.is-plain` / `--warning.is-plain` / `.is-disabled` 四条规则删除 `border-color` 与 `color`，仅保留语义 `background`
- [x] 3.2 `components/DeviceCard.vue`：`.card-btn` 删除 `border` / `border-radius` / `transition` 与 hover 的 `transform`，删除 `.card-btn--ghost` 规则及模板中的类名绑定，保留 `.card-btn--warn` 的语义底色
- [x] 3.3 复核未改动：`shared/components/FilterTabs.vue`、`shared/components/patterns/ErrorState.vue`、`shared/styles/workbench-theme.css`、`src/style.css` 在本次变更中 diff 为空

## 4. 验证

- [x] 4.1 `cd frontend && npm run lint:styles` 退出码 0
- [x] 4.2 `cd frontend && npx vite build --mode development` 退出码 0
- [x] 4.3 Chromium 断言（含改动前反证）：设备管理页各按键的计算 `border-width` 2px / `border-style` solid / `border-radius` 2px / `box-shadow` 模糊半径 0 且偏移 2px；四组底色与选中态命中；文字色 `--ink` 且四组对比度 ≥ 4.5:1；工具条未因按钮变大而溢出
- [x] 4.4 Chromium 断言：`/inspector`、`/ai-assistant/agents`、`/cases` 的 `FilterTabs` / `ErrorState` / `.wb-btn` 计算样式与改动前一致
- [x] 4.5 `npx openspec validate unify-device-pool-buttons --strict` 通过

## 5. 归档关单

- [x] 5.1 `npx openspec archive unify-device-pool-buttons -y` 成功
- [x] 5.2 `npx openspec validate --all` 无新增失败项
