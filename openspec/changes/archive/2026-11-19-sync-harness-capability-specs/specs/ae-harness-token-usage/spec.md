## MODIFIED Requirements

### Requirement: 创建模型时交出密钥环境变量名

模型创建出口在返回模型实例的同时 MUST 交出本次使用的密钥环境变量名。调用方 MUST 传入 `provider`、`api_key_env`、`model_name` 与可选的 `base_url`，无需再读配置文件即可知道「用了哪把密钥」。创建出口 MUST NOT 接受模型短名。

交出的 MUST 只是环境变量名；密钥明文 MUST NOT 出现在返回结构、日志、异常消息或记录文件里。

#### Scenario: 创建时直接拿到密钥环境变量名

- **WHEN** 调用方以 `provider=govee`、`api_key_env=GOVEE_API_KEY` 创建模型
- **THEN** 返回值同时给出模型实例与 `GOVEE_API_KEY`
- **AND** 返回值里不存在密钥明文

#### Scenario: 另一条配置给出另一把密钥名

- **WHEN** 调用方以 `provider=deepseek`、`api_key_env=DEEPSEEK_API_KEY` 创建模型
- **THEN** 返回值给出的环境变量名为 `DEEPSEEK_API_KEY`

### Requirement: 角色创建出口透传密钥环境变量名

角色创建出口 MUST 在返回可运行智能体的同时交出本次使用的密钥环境变量名，且 MUST NOT 因此新增第二种创建入口。入参 MUST 是名称、系统提示词正文和连接参数，MUST NOT 含模型短名。

#### Scenario: 创建智能体后拿到密钥名

- **WHEN** 调用方用 `provider=govee`、`api_key_env=GOVEE_API_KEY` 与一段提示词正文创建智能体
- **THEN** 返回值的智能体可运行
- **AND** 同一返回值的密钥环境变量名为 `GOVEE_API_KEY`
