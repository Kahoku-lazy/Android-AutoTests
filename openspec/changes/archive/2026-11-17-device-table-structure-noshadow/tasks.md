# 任务：设备表结构借用 + 表纸去影

## 1. 列配置与表头

- [x] 1.1 `shared/types/device.ts` 的 `ColumnConfig` 增加可选 `icon` 字段，`npx vue-tsc --noEmit` 通过
- [x] 1.2 `device-pool/constants.ts` 的 `COLUMNS[]` 为七列各填 `icon`，`title` 保持纯文字
- [x] 1.3 `index.vue` 补 `#header-<prop>` 插槽（由 `COLUMNS` 驱动，七个表头），渲染「图标 + 列名」，页面表现与 `temps/device-table-glass-proto.html` 的定稿档一致

## 2. 首列身份单元

- [x] 2.1 新增 `components/DeviceIdentityCell.vue`：图标圆 + 状态点 + 型号 / `serial · address` 双行，props 为 `device` / `selected`
- [x] 2.2 `index.vue` 的 `#cell-device` 改为调用该组件，删除内联的 `.dev-id` / `.dev-model` / `.dev-meta` 模板与其页面样式
- [x] 2.3 选中态：行点击选中由 `AppTable` 的 `row-class-name` 产出共享类名 `is-selected`（行底色来自共享皮肤），首列图标圆另加 0 模糊外环

## 3. 操作列收敛

- [x] 3.1 `DeviceActionsCell.vue` 改为「主操作胶囊 + `⋯` 菜单」；Wi-Fi 行保留锁定/公开切换，无任何操作的 USB 行渲染 `—`
- [x] 3.2 菜单项：强制释放（执行占用时隐藏）、删除（`BUSY` 时禁用）；删除仍经 `DisconnectDialog` 二次确认
- [x] 3.3 三个 emit（`lock` / `release` / `disconnect`）与父级 handler 不变，点击后行为与改动前一致

## 4. 表纸去影与样式

- [x] 4.1 `DevicePoolView.style.css` 在已有的 `.device-workbench :deep(.sketch-sheet)` 规则里加 `box-shadow: none`，保留 `border-style: solid`
- [x] 4.2 补首列身份单元（scoped）、表头图标、主操作胶囊与菜单的样式；颜色只取已登记令牌，动效取 `--app-duration-*` / `--app-ease`
- [x] 4.3 新增的 `transition` 涉及 `transform`，已补 `@media (prefers-reduced-motion: reduce)` 降级

## 5. 门禁与回归

- [x] 5.1 `npm run lint:styles`：批 1 / 批 2 / 批 4 通过，本变更文件零告警；全仓退出码仍为 1，来源是 `modules/task-list/**` 既有 21 条 `--ai-*` 悬空引用（HEAD 已存在，与本变更无关）
- [x] 5.2 `cd frontend && npm run lint:lines` 通过（未新增虚线）
- [x] 5.3 `cd frontend && npx vue-tsc --noEmit` 通过；`npm run lint` 0 error（52 条既有 warning）
- [x] 5.4 前端在跑，`/devices` 表格视图目视验收通过：七列表头带图标、身份单元、主操作 + 菜单、表纸计算 `box-shadow: none`；截图存档 `temps/shot-devices-table.png` / `shot-devices-menu.png` / `shot-devices-selected.png`
- [x] 5.5 共享皮肤回归：同页注入 `.wb-shell .sketch-sheet` 探针，计算 `box-shadow` 仍为 `4px 4px 0 rgb(124,111,131)`（`--c-report` 硬影），去影未波及共享声明
- [x] 5.6 `node tests/run.mjs module device-pool`：9 个测试文件 / 45 条用例全部通过

## 6. 文档登记

- [x] 6.1 `doodle-craft` 的 `references/components/data-display.md` 登记「无影变体（.device-workbench）」并写入 §2.1
- [x] 6.2 方案原型 `temps/device-table-glass-proto.html` 的定稿档与实现一致（边框取共享 1px，2px 墨降级为 P2 备选）
