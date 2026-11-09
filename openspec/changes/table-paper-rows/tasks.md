## 1. 表纸皮肤

- [x] 1.1 `workbench-theme.css`：`.ac-table` 表头去底色、改 1px ink 14% 底线、600 字重、次要色、字距 0.08em（`wb-shell` 与 `workflow-workbench` 双作用域）。验证：`lint:styles` 批 2 通过。**验证结果**：批 2 通过。
- [x] 1.2 数据行：1px `ink 8%` 行分隔线、`padding: var(--app-space-md) 0`、悬停 `ink 3%` 浅底。验证：build 通过。**验证结果**：build 21.3s。
- [x] 1.3 不引入列线与模块色线；白色仍不作为可见边框色。验证：`lint:styles` 通过（无新增裸色）。**验证结果**：批 2 通过。

## 2. 规格同步

- [x] 2.1 `frontend-l4-data-surface` delta：`Tables draw no visible grid lines` 改为「禁止列线；行线 ink 8%、表头线 ink 14%；表头 12 / 600 / uppercase / 次要色」。验证：`openspec validate table-paper-rows --strict`。**验证结果**：见 3.1。

## 3. 门禁

- [x] 3.1 `npx vue-tsc --noEmit`、`npm run build:check`、`npm run lint:styles`、`npm run lint:lines`、`openspec validate --strict`。验证：全绿。**验证结果**：build 21.3s；批 2 通过；虚线 0 处；validate 通过。
- [ ] 3.2 目视：任务清单 / BUG 单 / 用例管理等表格的表头与行分隔。验证：用户确认。
