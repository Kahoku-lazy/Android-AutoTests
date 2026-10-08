## MODIFIED Requirements

### Requirement: provider 配置单一真相源
系统 SHALL 保证「provider → base_url」映射只有一份真相源，且 provider 合法性只由该集合判定。平台支持的 provider 集合 SHALL 恰为 DeepSeek 与阿里百炼（DashScope）两项。装配阶段收到集合外的 provider SHALL 报错并列出合法集合；引擎侧创建模型连接时对无法处理的 provider SHALL 同样报错，MUST NOT 静默降级为任何兼容实现。装配阶段解析出的 base_url SHALL 生效于模型连接，MUST NOT 被静默丢弃。

#### Scenario: 未知 provider 在装配阶段被拒
- **WHEN** 智能体配置中某角色的 provider 不在合法集合内
- **THEN** 装配阶段报错，错误文案包含该 provider 名与合法集合

#### Scenario: 自定义 base_url 必须生效
- **WHEN** provider 在合法集合内且配置了自定义 base_url
- **THEN** 该 base_url 生效于模型连接；若该 provider 链路不支持自定义地址，则显式报错，不得解析后丢弃

#### Scenario: 兜底分支不再吸收未知 provider
- **WHEN** 引擎收到合法集合之外的 provider（含已移除的 `openai` / `anthropic` / `gemini` / `custom`）
- **THEN** 抛出 `ConfigurationError`，MUST NOT 以任何兼容实现（含 OpenAI 兼容分支）发起模型请求

#### Scenario: 两侧 provider 集合一致
- **WHEN** 运行一致性测试
- **THEN** 引擎侧可处理的 provider 集合与 Django 侧合法 provider 集合完全相等，且恰为 `{deepseek, dashscope}`
