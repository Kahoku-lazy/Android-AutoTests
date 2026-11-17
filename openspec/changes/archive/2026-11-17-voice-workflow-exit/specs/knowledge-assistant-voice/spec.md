## ADDED Requirements

### Requirement: 知识库语音经 workflow 出口接入

知识库助手的语音会话 MUST 经语音 workflow 出口启动。后端 MUST NOT 直接 import 语音引擎包来取得配置、传输、会话或就绪状态。该调整 MUST NOT 改变 `/ws/knowledge-assistant/` 的路径、鉴权、上行白名单、音频格式或对话日志位置。

#### Scenario: 语音通道的接入点变化不改变协议

- **WHEN** 已登录客户端以 `mode=voice` 连接 `/ws/knowledge-assistant/`
- **THEN** 服务端仍按既有音频与转写协议处理该连接
- **AND** 接入实现不引用语音引擎包
