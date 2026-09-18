## ADDED Requirements

### Requirement: Module page root class names are module-prefixed and globally unique

每个模块的页面根 modifier 类名 MUST 带该模块前缀（如 `case-` / `locator-` / `ai-`），且 MUST 在全仓唯一 —— 系统 SHALL NOT 出现两个模块使用同名页根类的情况。孪生组件（同角色的两份实现）的私有类名 MUST 采用同一规格来源（令牌或共享选择器），SHALL NOT 各自维护分叉的字面量规格。

#### Scenario: No page root class is shared across modules

- **WHEN** 静态检索全仓 `modules/**` 中出现的页根 modifier 类名
- **THEN** 每个类名只出现在一个模块内
- **AND** `project-list-page` / `project-workspace` 不再被两个模块同时使用

#### Scenario: Twin components share one spec source

- **WHEN** 对比 `case-manager/components/ProjectTree.vue` 与 `element-locator/components/LocatorTree.vue` 的 `.ex-btn`
- **THEN** 两者的圆角与底色**取自同一令牌**（`--app-radius-sm` / `--paper`），内边距取值一致
- **AND** 不存在一方用字面量、另一方用令牌的分叉（圆角与底色维度）