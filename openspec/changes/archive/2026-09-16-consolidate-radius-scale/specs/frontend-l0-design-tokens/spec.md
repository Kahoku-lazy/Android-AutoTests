## ADDED Requirements

### Requirement: 可见盒子的圆角取自不对称规格令牌

前端样式中**可见盒子**的圆角 MUST 取自 `tokens.css` 已登记的不对称规格令牌（`--app-radius-sm` / `--app-radius-md` / `--app-radius-lg` / `--app-radius-pill` / `--app-radius-table`，或其原子 `--radius-*`）。系统 SHALL NOT 在可见盒子上书写对称字面量（如 `999px` / `8px` / `12px`），也 SHALL NOT 书写与已登记令牌**等价**的多值展开形式（如 `4px 8px 4px 8px`）。登记例外：真实圆形的 `50%`、已登记 2px 纸角（`--comp-note-radius` / `--comp-sheet-radius` 分量）、`1px` / `3px` / `5px` 一类图形量、`0` 重置、方向性几何（如 `0 3px 3px 0`），以及登录页已登记的独立视觉。

#### Scenario: No equivalent multi-value expansion remains

- **WHEN** 静态检索 `frontend/src` 的 `border-radius` 字面量
- **THEN** 不再出现 `4px 8px 4px 8px` / `6px 10px 6px 10px` / `3px 6px 3px 6px` / `2px 6px 2px 4px`
- **AND** 这些位置引用对应的已登记令牌

#### Scenario: Pill shapes use the registered pill token

- **WHEN** 检索 `border-radius` 的 `999px`
- **THEN** 命中数为 `0`
- **AND** 原胶囊位置引用 `var(--app-radius-pill)`

#### Scenario: Visible boxes are asymmetric

- **WHEN** 逐项检查改动后的可见盒子计算圆角
- **THEN** 其四角不完全相等（不对称几何），或属于登记例外（`50%` / 2px 纸角 / 图形量 / 登录页）
- **AND** `--app-radius-pill` 的引用数由 0 变为正数