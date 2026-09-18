## ADDED Requirements

### Requirement: 装配期配置 fail-fast
Django 侧组装任务时 SHALL 校验配置完整性：`device_control` 线路必须存在，planner / executor / verifier 三角色各自的模型名与可解密密钥必须非空，设备串必须可用。任一项缺失或非法时 SHALL 在装配阶段抛出可读错误并使任务以失败终态结束，MUST NOT 以空模型名 / 空密钥 / 空设备串继续进入工作流。

#### Scenario: 三角色配置缺失
- **WHEN** 智能体配置中缺少 planner / executor / verifier 中任意一个角色
- **THEN** 任务在装配阶段即以明确错误失败，错误文案指明缺失的角色，不进入工作流

#### Scenario: 模型名或密钥为空
- **WHEN** 某角色的模型名为空，或密钥解密后为空
- **THEN** 装配阶段报错并指明角色与字段，任务落 failed

#### Scenario: 无可用设备
- **WHEN** 任务未指定设备串且当前没有在线设备
- **THEN** 装配阶段报错说明无可用设备，MUST NOT 以空设备串启动工作流

### Requirement: provider 配置单一真相源
系统 SHALL 保证「provider → base_url」映射只有一份真相源，且 provider 合法性只由该集合判定。装配阶段收到集合外的 provider SHALL 报错并列出合法集合；引擎侧创建模型连接时对无法处理的 provider SHALL 同样报错，MUST NOT 静默降级为某个兼容实现。装配阶段解析出的 base_url SHALL 生效于模型连接，MUST NOT 被静默丢弃。

#### Scenario: 未知 provider 在装配阶段被拒
- **WHEN** 智能体配置中某角色的 provider 不在合法集合内
- **THEN** 装配阶段报错，错误文案包含该 provider 名与合法集合

#### Scenario: 自定义 base_url 必须生效
- **WHEN** provider 在合法集合内且配置了自定义 base_url
- **THEN** 该 base_url 生效于模型连接；若该 provider 链路不支持自定义地址，则显式报错，不得解析后丢弃

#### Scenario: 兜底分支不再吸收未知 provider
- **WHEN** 引擎收到合法集合之外、且不在 OpenAI 兼容白名单内的 provider
- **THEN** 抛出 ConfigurationError，MUST NOT 按 OpenAI 兼容发起模型请求

#### Scenario: 两侧 provider 集合一致
- **WHEN** 运行一致性测试
- **THEN** 引擎侧可处理的 provider 集合与 Django 侧合法 provider 集合完全相等
