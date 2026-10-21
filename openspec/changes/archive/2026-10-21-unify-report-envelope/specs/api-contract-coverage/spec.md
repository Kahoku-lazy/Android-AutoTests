## Purpose

保证 OpenAPI 基线覆盖全部对外业务端点：任何新增或变更的业务路径都必须出现在 `openspec/openapi.yaml` 中，避免"接口存在但没有契约"的缺口长期潜伏。

## ADDED Requirements

### Requirement: 业务路径必须全部进入 OpenAPI 基线

门禁 MUST 从 Django URLconf 枚举全部 `/api/` 业务路径，并与 `openspec/openapi.yaml` 逐条比对。比对 MUST 先做归一化：去掉 DRF `format` 后缀变体、去掉 Router 根、忽略路径参数名差异（`{pk}` 与 `{id}` 视为同一路径）。业务路径缺失于基线时 MUST 以非零退出码失败，并逐条列出缺失路径与更新命令。

#### Scenario: 新增端点未进基线

- **WHEN** 某 App 新增一条业务路径但未重新生成 `openspec/openapi.yaml`
- **THEN** `openapi-coverage` 门禁失败
- **AND** 输出中列出该缺失路径与"重新生成基线"的命令

#### Scenario: 参数名不同不误报

- **WHEN** URLconf 用 `{pk}`、OpenAPI 用 `{id}` 描述同一路径
- **THEN** 该路径 MUST 被判定为已覆盖，不产生告警

#### Scenario: 全部覆盖时通过

- **WHEN** URLconf 的每条业务路径都能在基线中找到
- **THEN** `openapi-coverage` 门禁通过，退出码为 0
