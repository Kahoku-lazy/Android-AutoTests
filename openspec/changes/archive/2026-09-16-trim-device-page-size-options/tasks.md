## 1. 收敛行数选项

- [x] 1.1 `frontend/src/modules/device-pool/constants.ts` 的 `PAGE_SIZE_OPTIONS` 由 `[5, 10]` 改为 `[5]`，并让注释与 `DEFAULT_PAGE_SIZE` 保持一致
- [x] 1.2 核实未动：`report-generator/constants.ts`、`shared/composables/usePagination.ts`、`index.vue`、`DevicePoolView.style.css` 在本变更中 diff 为空

## 2. 同步 spec

- [x] 2.1 delta 修正 `frontend-doodle-button` 的切换类 Requirement 与 Scenario（「显示行数」移出可切换列表 + 补单选项 Scenario）

## 3. 验证

- [x] 3.1 源级断言：解析 `constants.ts`，`PAGE_SIZE_OPTIONS` 深度等于 `[5]`、`DEFAULT_PAGE_SIZE` 为 `5`；全仓无其它模块消费 device-pool 的该常量
- [x] 3.2 Chromium 断言：按新选项集渲染时「显示行数」组只有 1 个按钮、文本为 `5`、底色为选中态柠黄；同时确认改前反证（旧选项集渲染出 2 个按钮）
- [x] 3.3 `cd frontend && npm run lint:styles` 退出码 0
- [x] 3.4 `cd frontend && npx vite build --mode development` 退出码 0
- [x] 3.5 `npx openspec validate trim-device-page-size-options --strict` 通过

## 4. 归档关单

- [x] 4.1 `npx openspec archive trim-device-page-size-options -y` 成功
- [x] 4.2 `npx openspec validate --all` 无新增失败项
