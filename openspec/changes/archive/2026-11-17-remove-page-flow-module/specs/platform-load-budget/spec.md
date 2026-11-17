## MODIFIED Requirements

### Requirement: 列表计数一次聚合

项目列表 MUST 用一次 `annotate(Count)` 产出每个条目的用例数，MUST NOT 对每一行单独执行 `COUNT`。页面流原型列表已随模块退役，本要求 MUST NOT 再以原型列表为约束对象。

#### Scenario: 项目列表查询数恒定

- **WHEN** 请求项目列表，返回 P 个项目
- **THEN** 查询条数与 P 无关
- **AND** 每个项目的 `case_count` 与逐个计数一致

#### Scenario: 原型列表查询数恒定

<!-- 场景名沿自变更前：原型列表已随页面流模块退役删除，本场景改为守住「零残留实现」 -->

- **WHEN** 检索原型列表端点与 `doc_count` 聚合实现
- **THEN** 命中数为 `0`（已随页面流模块删除）
- **AND** 项目列表的一次聚合不受影响
