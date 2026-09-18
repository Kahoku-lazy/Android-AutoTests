## ADDED Requirements

### Requirement: 模块令牌按模块落文件
每个拥有模块级场景令牌的模块 SHALL 在本模块目录下提供 `tokens.css`，其内容 SHALL 覆盖该模块全部模块级场景令牌；共享层 SHALL NOT 承载模块级场景令牌。

#### Scenario: 模块级令牌的落点
- **WHEN** 某模块需要跨组件复用的场景令牌（如标签底色、抽屉描边）
- **THEN** 该令牌 MUST 声明在 `modules/<模块>/tokens.css`，且 MUST NOT 继续留在 `shared/styles/**`

#### Scenario: 迁移后共享层无模块令牌
- **WHEN** 静态校验扫描 `shared/styles/tokens.css`
- **THEN** 其中 MUST NOT 存在 `--ai-*` / `--case-*` 等模块家族声明

### Requirement: 模块令牌值引用主 token
模块令牌的值 MUST 引用 T0 主 token 原子；模块令牌文件内 SHALL NOT 出现字面量色值。

#### Scenario: 模块令牌无字面量
- **WHEN** 静态校验扫描 `modules/*/tokens.css`
- **THEN** 任何 `--name: <字面量色值>` 的命中 MUST 为 0，值 MUST 形如 `var(--color-*)`

#### Scenario: 组件级载体同样引用原子
- **WHEN** 某组件在自身根类声明只被它消费的场景令牌
- **THEN** 其值 MUST 引用 T0 主 token 原子，SHALL NOT 写字面量色值

### Requirement: 模块令牌作用域保持在模块页面根类
模块令牌 SHALL 声明在该模块页面根类的作用域内，以模块页面根类为选择器；SHALL NOT 提升为 `:root` 全局声明。

#### Scenario: 作用域不因文件迁移而改变
- **WHEN** 模块令牌从共享文件迁至模块文件
- **THEN** 其选择器 MUST 保持为原模块页面根类（如 `.ai-workbench`），MUST NOT 改为 `:root`

#### Scenario: Teleport 目标的例外
- **WHEN** 某模块的浮层显式 Teleport 到 `body`
- **THEN** 该浮层所需令牌 MUST 声明在被传送元素自身根类上，并在声明处注释原因