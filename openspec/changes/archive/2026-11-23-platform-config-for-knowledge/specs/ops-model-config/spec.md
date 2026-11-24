## ADDED Requirements

### Requirement: 向量类型只支持 dashscope 并要求维度

系统 SHALL 在模型类型中增加「向量」。该类型可选厂商 MUST 只有 dashscope，默认厂商与密钥环境变量 MUST 为 dashscope 对应的那一对。保存向量类型时 MUST 要求正整数的向量维度，MUST NOT 要求 API 地址，MUST NOT 要求音色。从其它类型切换到向量时 MUST 按上述规则重置厂商；从向量切换回聊天且厂商仍受聊天支持时 MUST 保留该厂商。

#### Scenario: 新建向量模型

- **WHEN** 用户把模型类型选为向量
- **THEN** 厂商下拉只有 dashscope，并出现向量维度输入
- **AND** 不出现 API 地址与音色输入

#### Scenario: 维度缺失被拒绝

- **WHEN** 用户保存一条向量类型但维度为空或不是正整数
- **THEN** 保存失败并指出维度不合法
- **AND** 不新增模型配置

### Requirement: 向量模型不得绑定 Agent 配置

模型类型为向量的配置 MUST NOT 出现在 Agent 配置的模型下拉中，也 MUST NOT 被评测触发当作聊天模型选择。直接提交该配置作为 Agent 的模型时 MUST 被拒绝且不落库。

#### Scenario: Agent 下拉不含向量模型

- **WHEN** 运营打开 Agent 配置的模型下拉，且平台同时存在聊天模型与向量模型
- **THEN** 下拉只含聊天模型

#### Scenario: 强行绑定被拒绝

- **WHEN** 请求把一条 Agent 配置的模型改为向量类型
- **THEN** 返回可读错误
- **AND** 该 Agent 配置仍绑定原来的模型

## MODIFIED Requirements

### Requirement: 列表展示模型类型

模型配置列表 MUST 以「模型」为首列身份单元（模型名 + 「厂商 · 类型（· 音色）」副行），「模型类型」列 MUST 紧随该首列，取值为聊天、实时语音、语音合成、向量，并以 chip 呈现（1.5px 墨边 + 类型色混底 + 14px 粗字）。记录缺少模型类型时 MUST 按聊天展示（副行与 chip 同时回退为聊天）。向量类型的副行 MUST 展示维度，MUST NOT 展示音色。

#### Scenario: 三类配置并排展示

- **WHEN** 列表里同时存在聊天、实时语音、语音合成、向量四条配置
- **THEN** 每条记录在模型首列的右侧显示与自身类型一致的类型 chip
- **AND** 向量那条的副行含维度且不含音色

#### Scenario: 旧数据缺类型按聊天展示

- **WHEN** 某条历史记录没有模型类型字段
- **THEN** 类型 chip 显示聊天，副行也按聊天渲染
