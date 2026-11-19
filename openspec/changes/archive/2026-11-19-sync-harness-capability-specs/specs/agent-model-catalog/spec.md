## REMOVED Requirements

### Requirement: 模型表是唯一数据源

**Reason**: 聊天模型没有 `models.yaml`，也没有短名。`engines/agents/config/data/models.yaml` 已随旧包删除。
**Migration**: 调用方传入 `provider`、`api_key_env`、`model_name`、`base_url`。嵌入模型仍由 `ae_harness/knowledge/config/models.yaml` 单独声明。

### Requirement: 加载前完成配置校验

**Reason**: 没有模型表可校验。校验改为针对一次调用传入的参数。
**Migration**: 见本变更新增的「连接参数在创建时校验」。

### Requirement: 模型名必须真实存在

**Reason**: 创建层不维护可选模型清单，无法在本地判定厂商模型名是否真实存在。
**Migration**: 未知短名这条失败路径删除。厂商拒绝未知模型名时，按该次调用的错误返回。

### Requirement: 按模型名加载四族模型

**Reason**: realtime 与 tts 已下线。聊天模型不按短名加载，嵌入模型不走聊天创建层。
**Migration**: 聊天走 `create_model`；嵌入只由知识库模块创建。

### Requirement: 能力由声明推导

**Reason**: 没有模型声明表，`vision` 与 `input_types` 不再由引擎推导。
**Migration**: 调用方按所选模型自己决定是否传图片。引擎不替它补能力声明。

### Requirement: 模型级参数与覆盖优先级

**Reason**: 没有模型表，不存在表内参数与角色覆盖的优先级。
**Migration**: 调用参数就是本次创建的全部参数。

### Requirement: 模型实例按规格复用

**Reason**: 创建层不缓存、不按短名复用。
**Migration**: 每次 `create_model` 返回新实例。

### Requirement: 备用模型由主模型派生

**Reason**: 备用模型不再由创建层派生或解析。
**Migration**: 只有调用方已经传入备用实例时，重试层才使用它。

### Requirement: 提示词不进入模型表

**Reason**: 模型表已不存在，这条隔离由「创建层不读提示词」自然满足。
**Migration**: `create_model` 不接收提示词。提示词只进入 `create_agent`。

## ADDED Requirements

### Requirement: 连接参数在创建时校验

`create_model` MUST 校验 `provider`、`api_key_env`、`model_name` 与 `base_url`。`provider` MUST 是 `deepseek`、`dashscope`、`govee` 之一，且 MUST 与允许的密钥环境变量名成对。密钥缺失、参数类型不合法或厂商与密钥名不匹配时 MUST 失败，异常信息 MUST NOT 含密钥明文。

#### Scenario: 合法参数通过

- **WHEN** 传入成对的厂商与密钥名、非空模型名
- **THEN** 返回可用的聊天模型与该密钥环境变量名

#### Scenario: 密钥名不匹配

- **WHEN** `provider` 与 `api_key_env` 不是允许的一对
- **THEN** 创建失败，且错误文本里没有密钥值

### Requirement: 嵌入模型不进入聊天创建层

聊天模型创建层 MUST NOT 创建嵌入、实时语音或语音合成模型。嵌入模型 MUST 只由 `ae_harness/knowledge` 按自己的向量模型配置创建。该配置 MUST NOT 含 chat、realtime 或 tts 字段。

#### Scenario: 向量配置混入聊天字段

- **WHEN** 知识库的向量模型配置出现 chat、realtime 或 tts 字段
- **THEN** 配置装载失败

### Requirement: 同一次调用不复用实例

`create_model` MUST 每次返回新的模型实例。它 MUST NOT 以短名、流式开关或事件循环作为复用键。

#### Scenario: 连续两次相同参数

- **WHEN** 用同一组连接参数连续创建两次
- **THEN** 两次返回的模型不是同一对象
