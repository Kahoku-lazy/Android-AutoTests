## Purpose

让 AI 一次拿到**全部**页面流文档，并知道每篇文档在目录树中的位置（完整路径与层级深度），从而在选测试点时不会因默认截断而漏文档、也不会因缺少层级而误判文档归属。

## ADDED Requirements

### Requirement: 页面流文档列表为全量并含目录层级

`list_page_flows` SHALL 返回平台全部页面流文档，MUST NOT 按固定条数截断。每条文档 MUST 含其在目录树中的层级信息：`directory_path`（祖先目录名以 `/` 连接而成的完整路径）与 `directory_depth`（根目录下的文档为 1）。未归入任何目录的文档 MUST 仍被列出，并以 `directory_id` 为空值、`directory_path` 为空字符串、`directory_depth` 为 0 明确标示，MUST NOT 静默丢弃。返回体 MUST 含文档总数。

#### Scenario: 不截断地列出全部文档

- **WHEN** 平台存在 25 篇页面流文档，调用 `list_page_flows`
- **THEN** 返回的 `documents` 含 25 条，`total` 为 25
- **AND** MUST NOT 只返回前 20 条

#### Scenario: 多级目录给出完整路径与深度

- **WHEN** 某文档位于「默认目录 / 详情页 / 深一层」三级目录下
- **THEN** 该条的 `directory_path` 为 `默认目录/详情页/深一层`
- **AND** `directory_depth` 为 3

#### Scenario: 未归类文档仍被列出

- **WHEN** 某页面流文档未归入任何目录
- **THEN** 该文档出现在 `documents` 中
- **AND** `directory_id` 为空值、`directory_path` 为空字符串、`directory_depth` 为 0

#### Scenario: 可按关键词收窄

- **WHEN** 调用 `list_page_flows` 并传入非空 `query`
- **THEN** 只返回标题或文档 ID 命中该关键词的文档
- **AND** 不传 `query` 时为全量（默认语义不变）
