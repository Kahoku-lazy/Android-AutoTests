## ADDED Requirements

### Requirement: 字号刻度登记 48px 品牌展示档
`shared/styles/tokens.css` 的字号刻度 SHALL 在既有 6 档之外登记一档 48px 品牌展示级文本字号：T0 原子 `--font-size-3xl: 48px`，并 SHALL 提供等价别名 `--app-size-3xl`。该档 MUST 仅用于首屏品牌展示级文本（当前唯一消费点为登录页 Hero 标题），SHALL NOT 取代现有 6 档 UI 文本刻度。

#### Scenario: 48px 档以规格原子登记并提供别名
- **WHEN** 检索 `tokens.css` 的排版原子声明
- **THEN** 存在 `--font-size-3xl: 48px`，且别名区存在 `--app-size-3xl: var(--font-size-3xl)`
- **AND** 消费方以 `var()` 引用该档，样式文件中不存在 `font-size: 48px` 这类字面量

#### Scenario: 展示档不扩散到常规 UI 文本
- **WHEN** 检索样式文件中 `--app-size-3xl` 的使用位置
- **THEN** 命中仅出现在登录页 Hero 标题载体
