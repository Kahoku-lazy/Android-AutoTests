# dashboard-ai-usage Specification

## Purpose
TBD - created by archiving change add-dashboard-ai-usage. Update Purpose after archive.
## Requirements
### Requirement: 后端持久化 AI 消息 token 用量

系统 SHALL 在 AI 对话流式回复持久化时，记录该条 assistant 消息的输入 token 与输出 token，并记录模型名。

#### Scenario: 对话回复记录 token

- **WHEN** 一次 AI 流式回复完成并落库
- **THEN** 该 assistant 消息的输入 token 与输出 token 字段为该轮回复的累计值，模型名字段非空

#### Scenario: 历史消息无用量

- **WHEN** 修复前已存在的历史消息被读取
- **THEN** 其 token 字段保持 0，不影响统计接口按 0 参与汇总

### Requirement: 后端持久化 AI 消息缓存命中

系统 SHALL 记录该条 assistant 消息的缓存命中 token 数与缓存写入 token 数（模型 API 返回时）。

#### Scenario: 缓存命中落库

- **WHEN** 模型 API 返回缓存命中用量
- **THEN** 该 assistant 消息的缓存命中 token 字段为该轮累计值

### Requirement: 仪表盘提供 AI 用量统计接口

系统 SHALL 在仪表盘统计接口中提供 AI 用量汇总，含对话总数、输入/输出 token、缓存命中 token 与命中率、平均每对话 token，且均分「今日 / 累计」两组口径。

#### Scenario: 统计接口返回 AI 用量

- **WHEN** 用户请求仪表盘统计接口
- **THEN** 响应含 `ai_usage` 字段，其 `conversation_count` / `input_tokens` / `output_tokens` / `cache_hit_tokens` / `cache_hit_rate` / `avg_tokens_per_conversation` 各含 `today` 与 `total`

#### Scenario: 缓存命中率除零

- **WHEN** 输入 token 总数为 0
- **THEN** 缓存命中率为 0，不报错

### Requirement: 仪表盘展示 AI 用量区块

系统 SHALL 在仪表盘「AI 用量」区块展示任务数量、累计 Token、缓存命中率、平均每任务 Token、DeepSeek 费用卡片，每张卡片同时显示今日与累计数值。该区块内的 KPI 卡 MUST NOT 渲染独立「进入」按钮；有跳转路径时用户仍可通过激活整卡进入智能体页。

#### Scenario: 区块卡片展示

- **WHEN** 用户打开仪表盘且 AI 用量数据加载完成
- **THEN** 「AI 用量」区块展示上述卡片，每卡显示今日与累计两个数值

#### Scenario: AI KPI cards have no enter button
- **WHEN** 用户查看「AI 用量」区块已加载的 KPI 卡
- **THEN** 卡片内不存在「进入」按钮（`.kpi-card__enter`）
- **AND** 卡片仍可激活并导航到既有智能体路径

