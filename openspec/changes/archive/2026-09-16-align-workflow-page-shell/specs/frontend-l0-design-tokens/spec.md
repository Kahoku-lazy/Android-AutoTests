## ADDED Requirements

### Requirement: 共享皮肤不依赖模块作用域令牌

共享样式（`shared/styles/**` 及 `shared/components/**` 内的样式）SHALL NOT 消费模块作用域令牌（即声明在 `.ai-workbench` / `.case-workbench` / `.workflow-workbench` 等模块页面根类内的令牌）。共享皮肤在多个模块的页根上同时生效，消费模块令牌会使其在未声明该令牌的页根上**静默失效**，造成同一共享组件跨模块外观不一致。共享皮肤所需的外观值 MUST 取自 T0 主 token 或声明在 `:root` 上的共享组件令牌（`--comp-*`）。模块令牌文件内 SHALL NOT 重复声明同一令牌。

#### Scenario: Workbench shell does not consume module tokens

- **WHEN** 检查 `shared/styles/workbench-theme.css` 对 `.wb-shell` / `.workflow-workbench` 的声明
- **THEN** 其 `font-family` / `color` 取自 `--app-font` / `--ink` 等共享或主 token
- **AND** 不再出现只声明在单个模块页根内的 `--ac-font` / `--ac-ink` 一类令牌

#### Scenario: Shared card pin shadow resolves in every module

- **WHEN** 在 dashboard、report-generator 或 ai-assistant 的任一页面上渲染 `AppCard` 的图钉（`.ac-card__pin`）
- **THEN** 该图钉的计算 `box-shadow` 非 `none`，且色源取自 `:root` 上的共享组件令牌
- **AND** 不再出现"同一共享组件在 workflow 有硬阴影、在其他模块无阴影"的差异

#### Scenario: Module token is declared once

- **WHEN** 检查 `modules/workflow/tokens.css` 的 `--ac-accent`
- **THEN** 该令牌只声明一次，取值与模块色登记一致（工作流天蓝 `--c-workflow`）
- **AND** 不再存在后置声明静默改写其值的情况

#### Scenario: Zero-consumer tokens left by the fix are removed

- **WHEN** 检索 `--ac-font` / `--ac-ink` / `--ac-pin-shadow`
- **THEN** 三者的声明与消费命中数均为 `0`