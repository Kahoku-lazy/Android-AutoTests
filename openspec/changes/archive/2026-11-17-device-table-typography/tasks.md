# 任务：设备表字号对齐 BUG 表

## 1. 字号三档

- [x] 1.1 `DevicePoolView.style.css`：表头加 `font-size: var(--app-size-md)` 与 `.cell` 的 `white-space: nowrap`
- [x] 1.2 连接 / 可见性胶囊（`.conn-chip` / `.vis-chip`）提到 `--app-size-sm`
- [x] 1.3 `DeviceIdentityCell.vue`：型号 `--app-size-md` → `--app-size-sm`；序列号行（`.dev-id__meta` 与其中 `code`）`--app-size-xs` → `--app-size-sm`
- [x] 1.4 `DeviceActionsCell.vue`：`.act-pill` 与 `.act-more` 从 `--app-size-xs` 提到 `--app-size-sm`
- [x] 1.5 活跃列：`.time-rel` 保持 14px、`.time-abs` 保持 12px（无回归）
- [x] 1.6 控制区同档：统一按键皮肤块加 `font-size: var(--app-size-sm)`（覆盖 `el-button size="small"`、筛选下拉与搜索框），`.dev-mock-toggle__label` 12 → 14；实测分页文案 / 下拉 / 搜索 / 翻页键 / 局域网 / 刷新 / 开发调试全部 14px

## 2. 验证

- [x] 2.1 浏览器量测 `/devices`：表头七个 `th` 全为 **16px** 且 `oneLine: true`；型号 / 序列号 / 两者 code / 连接胶囊 / 可见性胶囊 / 分辨率 / 相对时间 / 操作胶囊 / 「⋯」全为 **14px**；`.time-abs` 为 **12px**
- [x] 2.2 `npx prettier --check "src/modules/device-pool/**/*.{vue,ts,css}"` 通过；`npm run lint:styles` 对 device-pool 零告警；`npx vue-tsc --noEmit` 对本模块 0 错（全仓剩余报错均在 `tests/dashboard/**` 与 `tests/workflow/**`，属他人未完成的 page-flow 退役改动，与本次无关）
- [x] 2.3 `node tests/run.mjs module device-pool`：9 文件 / 48 用例全绿

## 4. 全局单一来源（2026-11 决策 A）

- [x] 4.1 `style.css` 的 `.el-table th` 字号 `--app-size-xs` → `--app-size-md`，并给 `.el-table th .cell` 加 `nowrap`
- [x] 4.2 共享皮肤 `workbench-theme.css` 的 `.wb-shell .ac-table th.el-table__cell` 字号同步改 16px（这才是 AppTable 页的真实来源）
- [x] 4.3 删除设备页与 BUG 页的表头字号 / nowrap 覆写，改为依赖全局与共享皮肤
- [x] 4.4 跨页实测：`/devices` 7 列、`/bugs` 6 列、`/tasks` 9 列表头均为 **16px** 且 `wrapped: 0`（无折行）
- [x] 4.5 `frontend-l4-data-surface` 的「表头排版唯一来源」要求同步改为 16px，并补「不存在模块私有表头字号覆盖」的断言
- [x] 4.6 平台规则写进主题 skill：`doodle-craft/references/components/data-display.md` §1.1「表格字号三档」+ `SKILL.md` 组件目录入口

## 5. 已知副作用（供决策）

- [x] 3.1 序列号与地址在 14px 下会于窄列折成两行（USB 设备两者同值时看起来像重复两行）。若要单行：把这两处降回 12px，或加宽「设备」列（`COLUMNS.device.minWidth` 220 → 260）。
