## ADDED Requirements

### Requirement: 任务列表查询预算与轮询不叠加

`GET /api/tasks/` MUST 只查任务自身列，MUST NOT 通过 `select_related` 读取智能体的大字段；线路名 MUST 由数据库侧从 `route_configs` 中提取。单次列表请求 SQL MUST NOT 超过 5 条，附件 MUST 批量取。前端运行态轮询 MUST 在上一轮未返回时跳过本轮，间隔 MUST NOT 小于 10 秒。

#### Scenario: 列表不再随任务数放大

- **WHEN** 请求 `GET /api/tasks/`，返回 N 条任务
- **THEN** SQL 条数与 N 无关（不超过 5 条）
- **AND** 不出现「每条任务一次附件查询」的 N+1

#### Scenario: 慢请求不叠加

- **WHEN** 上一次任务列表请求尚未返回，轮询到点
- **THEN** 本轮被跳过
- **AND** 上一次返回后按正常节奏继续

#### Scenario: 响应字段不变

- **WHEN** 对比改动前后的任务列表响应
- **THEN** `tasks[]` 的字段与取值口径一致（含 `assistant_name`、`attachment_names`、`deepseek_cost`）
