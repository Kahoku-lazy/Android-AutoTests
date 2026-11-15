## Purpose

把语音助手的使用收成 workflow 的一个出口，让前后端只消费已经创建好的语音助手，不再直接进入语音引擎包。

## ADDED Requirements

### Requirement: 语音助手只经 workflow 出口使用

系统 SHALL 提供一个语音 workflow 出口，供后端启动语音会话、读取就绪状态和转发浏览器音频。该出口 MUST 通过语音助手创建出口取得实时语音智能体，MUST NOT 自己构造实时语音智能体，MUST NOT 读取模型密钥或连接参数。音频传输的生命周期 MUST 由调用方持有；workflow 只借用传输，不在会话结束后替调用方关闭浏览器通道。

#### Scenario: 后端启动一次语音会话

- **WHEN** 已登录用户在知识库助手选择语音并点击启动
- **THEN** 后端经语音 workflow 出口启动会话
- **AND** 后端代码不引用语音引擎包

#### Scenario: 出口不自己造智能体

- **WHEN** 检查语音 workflow 出口的创建路径
- **THEN** 实时语音智能体只来自语音助手创建出口
- **AND** 出口内不出现实时语音智能体的直接构造

### Requirement: 语音引擎包不再对包外公开

语音引擎包 MUST 只作为 workflow 的内部实现。`backend/` 与 `frontend/` MUST NOT import 该包。文字会话若仍复用其中的转写桥，MUST 在本变更中改为经 workflow 出口取得，不得继续直接引用该包。

#### Scenario: 后端不再引用语音引擎包

- **WHEN** 扫描 `backend/` 的 import
- **THEN** 不存在对语音引擎包的导入

#### Scenario: 文字会话不绕回语音引擎包

- **WHEN** 文字问答需要转写桥或日志协议
- **THEN** 它从 workflow 出口取得
- **AND** 不直接 import 语音引擎包
