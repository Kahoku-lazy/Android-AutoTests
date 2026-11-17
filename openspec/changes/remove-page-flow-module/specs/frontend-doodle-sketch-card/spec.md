## REMOVED Requirements

### Requirement: Two resource lists consume SketchCard

**Reason**: 页面流原型列表随模块整体删除，「两处资源列表」的消费方只剩用例项目列表，原要求的双消费方口径失效。

**Migration**: 用例项目列表继续消费共享 `SketchCard`，由下方 ADDED 要求承接；共享组件本身与 cycle 配色不变。

## ADDED Requirements

### Requirement: Case project list consumes SketchCard

用例项目列表 MUST 使用共享 `SketchCard`。SHALL NOT 继续维护私有 `project-card__accent` 顶条实现。

#### Scenario: Case project list uses SketchCard

- **WHEN** 用户打开用例管理且存在至少一个项目
- **THEN** 每张卡为 `SketchCard` 撕纸壳
- **AND** 点击卡片进入该项目工作台
- **AND** 删除控件不冒泡为进入
