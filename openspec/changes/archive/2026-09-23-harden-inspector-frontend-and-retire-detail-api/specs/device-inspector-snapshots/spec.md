## ADDED Requirements

### Requirement: 快照详情端点退役，回看一律经分层端点

系统 MUST NOT 再提供快照详情端点 `GET /api/inspector/snapshots/{id}/`：该路径 MUST NOT 出现在路由表、公开 API 白名单与接口文档中。快照回看 MUST 只消费分层端点 `GET /api/inspector/snapshots/{id}/layers/`。退役 MUST 同步到接口用例——以该端点为对象的用例一并删除，使 `tests/api/case/*.yaml` 中的每条 `/api/` 路径仍能在后端路由表中解析。快照列表、分层、删除、清空与保存到元素定位端点 MUST 不受影响。

#### Scenario: 已退役路径返回 404

- **WHEN** 请求 `GET /api/inspector/snapshots/1/`
- **THEN** 返回 404，MUST NOT 返回快照 JSON

#### Scenario: 回看只消费分层端点

- **WHEN** 用户从快照抽屉回看一份历史快照
- **THEN** 前端只调用 `GET /api/inspector/snapshots/{id}/layers/`，MUST NOT 调用快照详情端点

#### Scenario: 接口用例与路由表一致

- **WHEN** 扫描 `tests/api/case/inspector.yaml` 的 `path:` 字段并逐条在后端路由表中解析
- **THEN** 不存在指向快照详情端点的用例，且每条路径都能解析命中

#### Scenario: 其余快照端点不受影响

- **WHEN** 调用快照列表 / 分层 / 删除 / 清空 / 保存到元素定位端点
- **THEN** 行为与退役前一致
