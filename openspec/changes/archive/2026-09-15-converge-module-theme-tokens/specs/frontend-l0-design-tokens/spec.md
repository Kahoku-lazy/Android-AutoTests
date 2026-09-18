## ADDED Requirements

### Requirement: Module styles consume registered design tokens

模块样式（`modules/**/*.vue` 的 `<style>` 与 `modules/**/*.css`）中的**语义色与状态色** MUST 取 `shared/styles/tokens.css` 已登记的令牌（`--c-*` / `--app-status-*` / `--ink` / `--paper` / `--app-bg-*` / `--app-text-*`），MUST NOT 直写字面量。**文本字号** MUST 取 `--app-size-*` 刻度且 MUST NOT 低于 12px（图形/展示级字号例外见 `frontend/AGENTS.md` 硬性规范 §1.14）。Element Plus 默认调色板（如 `#409eff`）MUST NOT 被当作模块色。**画布绘制色**（ECharts 系列色 / canvas 绘制色，同既有 ECharts 例外）与**数据编码型分类色板**（分类标签色）MAY 保留字面色相；其中分类色板每个色相 MUST 在该文件的具名局部自定义属性中声明一次，SHALL NOT 在规则里重复散落同一字面量。

#### Scenario: Semantic and state colors come from tokens

- **WHEN** 静态检索模块样式中危险 / 成功 / 通过 / 失败 / hover 态等语义色的字面量
- **THEN** 这些位置引用 `--app-status-*` 等令牌，不再出现字面量（canvas 绘制色与图表系列色除外，见需求正文例外）
- **AND** 本轮收敛：`ai-assistant/KnowledgeBase.vue` 的 hover 危险字面量、`case-manager` 两个文件的白底与危险字面量、`report-generator` 两个文件的通过 / 失败字面量

#### Scenario: Element Plus default palette is not used as a module color

- **WHEN** 检索模块样式中的 Element Plus 默认色（`#409eff` / `#67c23a` / `#f56c6c` / `#e6a23c`）
- **THEN** 命中为 0，改用该模块的 `--c-*` 模块色或 `--app-status-*` 状态色
- **AND** 本轮收敛 `device-inspector/components/PageElementsPanel.vue` 的 dump / OCR 徽标底色

#### Scenario: Text size respects the 12px floor

- **WHEN** 静态检索模块样式中 `font-size` 的 px 字面量
- **THEN** 不存在低于 12px 的文本字号，其余字面量仅限图形 / 展示级例外
- **AND** `dashboard/DashboardView.style.css` 的 `.subhead__tag` 由 `10px` 改为 `var(--app-size-xs)`

#### Scenario: Literal values registered as tokens are replaced by the token

- **WHEN** 某处字面量色值与 `tokens.css` 已登记令牌的值等价
- **THEN** 该处引用令牌而非字面量
- **AND** 本轮收敛 `report-generator` 的 `#a03030` → `--app-status-danger-text`、`device-inspector` 的 `#a78bfa` → `--c-element`

#### Scenario: Categorical palettes are declared once

- **WHEN** 检查数据编码型分类色板的使用方式（`case-manager` 的 7 色测试类型标签）
- **THEN** 每个色相只在具名局部自定义属性中声明一次，消费规则里不再出现裸字面量
- **AND** 色相与分类语义保持不变（不压缩为状态色）
