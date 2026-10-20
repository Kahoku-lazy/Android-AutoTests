## ADDED Requirements

### Requirement: 描边宽度与线型以令牌登记

手绘风格的描边宽度 SHALL 以 T0 规格原子 `--size-stroke-sketch`（2.5px）登记在 `shared/styles/tokens.css`；消费该宽度的样式 MUST 以 `var()` 引用该原子，SHALL NOT 直写 `2.5px` 描边字面量。

描边**线型**（`dashed` / `solid`）SHALL 由消费边界以具名令牌自行声明（如登录页的 `--login-line`），MUST NOT 借用其它边界的组件令牌（`--comp-*`）或模块令牌来决定自身线型。理由是线型是"这个边界要不要留手绘虚线"的决定，由别的边界代为持有会让该决定在别处被改写时静默失效。

#### Scenario: 描边宽度取自已登记的原子

- **WHEN** 静态检索 `frontend/src` 中 `2.5px` 描边宽度字面量，并检查登录页的三处描边（`.hero-cta`、`.login-border` 组合、表单提交按钮）
- **THEN** 这些位置引用 `var(--size-stroke-sketch)`
- **AND** `tokens.css` 中该原子恰好声明一次

#### Scenario: 线型不跨边界借用

- **WHEN** 检索登录页样式对共享组件令牌 `--comp-sidebar-dash` 的引用
- **THEN** 命中数为 `0`
- **AND** 登录页线型由声明在 `.login-page` 作用域内的令牌提供

#### Scenario: 门禁保持通过

- **WHEN** 运行 `npm run lint:styles`
- **THEN** 字号下限、token 唯一性与引用完整性、几何尺度四类检查均不新增命中
- **AND** 新增原子名命中 `--size-*` 规格命名，不含模块前缀
