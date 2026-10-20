## REMOVED Requirements

### Requirement: Three resource lists consume SketchCard

**Reason**: 元素定位模块整体退役，资源列表从三处变为两处（用例项目、页面流原型），原要求以「三处」为口径不再成立。
**Migration**: 由本单新增的「Two resource lists consume SketchCard」承接仍存在的两处列表，组件与皮肤口径不变。

## ADDED Requirements

### Requirement: Two resource lists consume SketchCard

用例项目列表与页面流原型列表 MUST 使用共享 `SketchCard`。SHALL NOT 继续维护私有 `project-card__accent` / `proto-card__accent` 顶条实现。

#### Scenario: Case project list uses SketchCard

- **WHEN** 用户打开用例管理且存在至少一个项目
- **THEN** 每张卡为 `SketchCard` 撕纸壳
- **AND** 点击卡片进入该项目工作台
- **AND** 删除控件不冒泡为进入

#### Scenario: Workflow prototype list uses SketchCard

- **WHEN** 用户打开页面流且存在至少一个原型
- **THEN** 每张卡为 `SketchCard` 撕纸壳
- **AND** 点击卡片进入该原型工作台
- **AND** 删除控件不冒泡为进入
