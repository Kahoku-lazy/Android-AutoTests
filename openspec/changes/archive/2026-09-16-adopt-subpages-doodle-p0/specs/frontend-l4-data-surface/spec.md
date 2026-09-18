## ADDED Requirements

### Requirement: Flat lists do not wrap AppTable in Element Plus card

设备管理与报告列表的扁列表 MUST 以 `AppTable` 表纸呈现数据；SHALL NOT 再用 `el-card` 作为表格外套。需要分组容器时 MUST 使用 `.doc-section` 或 `AppCard`，且表纸皮肤遵循 `frontend-doodle-sketch-table`。

#### Scenario: Device table drops Element Plus card chrome

- **WHEN** 用户在 `/devices` 查看表格视图
- **THEN** DOM 中该表不位于 `el-card` 内
- **AND** 仍由共享 `AppTable` 渲染行与列
