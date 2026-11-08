## ADDED Requirements

### Requirement: 开发中入口标签

侧栏导航项 SHALL 支持「开发中」标记：`NAV_CATEGORIES` 中 `isDev: true` 的条目在标签文字右侧显示红色「开发中」徽标。

- 徽标 MUST 使用语义色：底色 `--app-status-danger-bg`、文字与描边 `--app-status-danger-text`；
- 徽标 MUST NOT 抢占导航项主色，MUST NOT 使用模块色或 ink 描边；
- 条目被选中时徽标 MUST 保持红色语义，MUST NOT 被选中态的白色徽标底色覆盖；
- 折叠态 MUST 隐藏徽标（空间不足），仅在展开态显示。

#### Scenario: 两个开发中入口显示红标

- **WHEN** 用户展开侧栏
- **THEN** 「知识库助手」与「页面流」右侧各有一个红色「开发中」徽标，其余导航项无徽标

#### Scenario: 选中态仍为红色

- **WHEN** 当前路由是 `/knowledge-assistant` 或 `/workflow`
- **THEN** 该导航项黄底选中，但「开发中」徽标仍是红底红字

#### Scenario: 折叠态不显示

- **WHEN** 侧栏处于折叠（仅图标）状态
- **THEN** 徽标不渲染，图标与位置不受影响
