## ADDED Requirements

### Requirement: 共享骨架块不得无作用域重定义

`.doc-section` 及其 BEM 部分（`__header` / `__title` / `__label`）的皮肤 SHALL 由全局样式唯一定义。模块确需差异时 MUST 通过任一登记方式限定作用域：`.<模块根类> .doc-section…`，或 BEM modifier `.doc-section--<变体>`（该 modifier 与 `.doc-section` 同时挂在同一元素上）。覆写 MUST NOT 重复声明全局已提供的同名属性（背景 / 描边 / 圆角 / 阴影 / 内边距 / 标题字号与字重）。系统 SHALL NOT 以**裸** `.doc-section` / `.doc-section__*` 选择器覆写该骨架块，SHALL NOT 用行内 `style` 覆写其内边距。

#### Scenario: No bare section override remains

- **WHEN** 在 `frontend/src/modules` 的 `<style>` 块与 `.css` 文件中检索行首即 `.doc-section`（**不含** `--` 修饰符）或 `.doc-section__` 的选择器
- **THEN** 命中数为 `0`
- **AND** 保留的变体只以 `.<模块根类> .doc-section…` 或 `.doc-section--<变体>` 两种形式出现

#### Scenario: Section skin is single-sourced

- **WHEN** 比较 `/reports` 与 `/ai-assistant/evaluator` 的 `.doc-section` 计算样式
- **THEN** 背景、描边宽度与颜色、圆角、阴影、内边距同源（同为墨色实线描边，而非 `1px` 近白线）
- **AND** 标题字号同为全局 `--app-size-md`

#### Scenario: No inline padding override on sections

- **WHEN** 检索模板中对 `.doc-section` 的 `style="padding…"` 覆写
- **THEN** 命中数为 `0`
- **AND** 需要贴边布局的分区改用 `.<模块根类> .<分区类>` 的类选择器表达

#### Scenario: Module-specific decoration keeps its scope

- **WHEN** 检查 `/reports` 分区标题的手绘波浪下划线
- **THEN** 该装饰以 `.report-workbench .doc-section__title::after` 形式声明
- **AND** 不影响其他模块的分区标题