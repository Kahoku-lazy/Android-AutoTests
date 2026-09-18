## ADDED Requirements

### Requirement: Stacking order comes from registered tokens

前端样式的 `z-index` SHOULD 取自 `tokens.css` 已登记的层叠令牌（`--z-*`）。系统 SHALL NOT 保留**悬空**的层叠令牌引用（引用了未声明的 `--z-*` / 模块 `--*-z-*` 令牌），因为该引用会在 computed-value 阶段失效并回落 `auto`，使层叠静默失效。单例值（未纳入档位的一次性层叠）MAY 保留字面量，但 MUST 在 `tokens.css` 的层叠令牌段登记其用途。

#### Scenario: No dangling stacking token remains

- **WHEN** 静态检索全仓 `.vue` / `.css` 的 `z-index` 声明与其引用的自定义属性
- **THEN** 每个被引用的层叠令牌都能在 `:root` 或对应模块 tokens.css 中找到声明
- **AND** `--case-z-context` 等此前悬空的令牌已声明且解析为预期层叠值

#### Scenario: Registered tiers match their previous literals

- **WHEN** 对比改动前后同值位置的 `z-index` 计算值
- **THEN** 取令牌的声明与其原字面量数值**逐一相同**
- **AND** 未纳入档位的单例值未被改动

#### Scenario: Module stacking tokens resolve inside their module

- **WHEN** 在 `case-manager` 的页面内渲染其上下文菜单
- **THEN** 该菜单的计算 `z-index` 为 `80`（不再为 `auto`）
- **AND** 与 `element-locator` 同类浮层的层级一致