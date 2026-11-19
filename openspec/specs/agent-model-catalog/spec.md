# agent-model-catalog Specification

## Purpose

约束聊天模型的创建方式：连接参数由调用方传入并在创建时校验，不维护模型表，不按短名加载。嵌入模型留在知识库模块。

## Requirements

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
