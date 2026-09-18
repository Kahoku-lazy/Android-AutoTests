## ADDED Requirements

### Requirement: 主 token 是颜色与规格的唯一登记处
共享层主 token SHALL 以按颜色命名的原子登记全部字面量色值，并 SHALL 是字面量色值的唯一声明位置；其他任何位置（模块层、组件层、Element Plus 覆盖）MUST 通过 `var()` 引用。

#### Scenario: 新增色值先登记原子
- **WHEN** 任一模块或组件需要一个主 token 中尚不存在的色值
- **THEN** 该色值 MUST 先作为颜色原子登记于主 token，消费处 MUST 以 `var()` 引用该原子

#### Scenario: 同值不重复声明
- **WHEN** 对主 token 运行静态校验
- **THEN** 同一色值的字面量声明 MUST 恰好出现一次，其余引用 MUST 为 `var()`

### Requirement: 主 token 命名只描述颜色与规格
主 token 的颜色、排版、基础量三档声明名 MUST 仅由颜色或规格构成，SHALL NOT 含使用场景名或模块名；模块用途 MUST 在模块层以 `var()` 组合表达。

#### Scenario: 新增原子命名合法性
- **WHEN** 对主 token 运行静态校验
- **THEN** 任何新增原子名 MUST 遵循颜色（`--color-<色相>-<明度>`）或规格（`--font*` / `--space-*` / `--radius-*` / `--shadow-*` / `--duration-*` / `--ease` / `--size-*`）命名，且 MUST NOT 含模块前缀（`--ai-` / `--case-` / `--rg-` / `--di-` / `--wf-` / `--views-`）

#### Scenario: 场景语义留在模块层
- **WHEN** 某模块需要「标签底色」这类场景语义
- **THEN** 该语义 MUST 声明在模块层并取值于主 token 原子，SHALL NOT 在主 token 中新增场景名声明

### Requirement: 通用组件配色独立成档
共享层 SHALL 为跨模块复用的通用组件提供配色档，声明名 MUST 采用 `--comp-<组件>-<场景>` 形式，且 SHALL NOT 含模块名。

#### Scenario: 通用组件令牌落档
- **WHEN** `shared/components/**` 中的组件需要模块无关的场景配色
- **THEN** 该配色 MUST 以 `--comp-<组件>-<场景>` 声明，其值 MUST 引用颜色原子

### Requirement: Element Plus 覆盖引用主 token 原子
主题对 Element Plus 变量的覆盖 MUST 引用主 token 原子，SHALL NOT 直接书写字面量色值。

#### Scenario: EP 覆盖不再直写字面量
- **WHEN** 静态校验扫描主题文件的 `--el-*` 声明
- **THEN** 其值 MUST 全部为 `var()` 引用，字面量命中 MUST 为 0
