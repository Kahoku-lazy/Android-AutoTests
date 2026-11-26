## 1. 数值渐变

- [x] 1.1 `frontend/src/shared/components/KpiCard.vue`：`.kpi-card--kpi .kpi-card__value` 与 `.kpi-card--entry .kpi-card__value` 两处渐变改为 `color-mix(accent 80%, paper)` → `color-mix(accent 30%, paper)`，并注明需求口径。验证：`temps/dashboard_kpi_preview.py` 渲染前后对照（`temps/fold-check/shot-dashboard-kpi.png`）。

## 2. 字号

- [x] 2.1 上述 5 个文件里 14 处 `--app-size-xs`（12px）改为 `--app-size-sm`（14px）：描述、字段名、时间、标签、小字。验证：`npm run lint:styles` 批 1（字号刻度）通过。
- [x] 2.2 4 处卡片 / 区块标题从 14px 提到 16px：`.kpi-card--kpi .kpi-card__label`、`.kpi-card__title`、`.subhead`、`.trends-tasks-card__title`。验证：`npx vitest run tests/dashboard tests/shared` → 19 files / 120 tests passed。
- [x] 2.3 大标题（`.chapter-title` 20px）与数值（`--app-size-2xl` 28px）保持不动。验证：diff 中未出现这两处。

## 3. 门禁

- [x] 3.1 `npx vue-tsc --noEmit` 退出码 0；`npm run lint:styles` 批 2 通过；批 4 仍是既有 `AppSidebar.style.css:209` 圆角欠账（与本次无关）。
- [x] 3.2 `python run.py check` 全绿：仍被仓库既有 12 项失败挡住（与本次无关）。
