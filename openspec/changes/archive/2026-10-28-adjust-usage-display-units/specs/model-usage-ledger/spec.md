## MODIFIED Requirements

### Requirement: 仪表盘模型用量

仪表盘 SHALL 展示「模型用量」区：

- 分类卡片的 token 值 MUST 只使用 `M`（百万）或 `K`（千）单位，保留 2 位小数；不得显示原始 token 数或 `token` 后缀。
- 分类卡片副标题 MUST 只显示厂商名：`DeepSeek` / `DASHSCOPE`；不得再显示 token 数。
- 最近明细表的 token 列与顶部累计 chip MUST 使用同一套 `M`/`K` 单位。
- 最近明细表显示时间、厂商、分类、模型、来源、token、费用。
- 数据来自 `usage_ledger.today` / `.total` / `.recent`。

#### Scenario: 卡片副标题

- **WHEN** 今日存在 DeepSeek LLM 调用
- **THEN** LLM 卡片副标题只显示 `DeepSeek`
- **AND** 其他分类按各自厂商显示

#### Scenario: 统一 token 单位

- **WHEN** 某分类今日 token 为 4,897
- **THEN** 卡片显示 `4.90K`
- **AND** 明细表显示 `4.90K`
- **AND** 不显示 `4,897 token`
