## ADDED Requirements

### Requirement: WebSocket 只承载知识库问答通道

平台的任务进度与列表 MUST NOT 因本能力改用 WebSocket；知识库助手通道 MUST 只承载语音问答与文字问答两类交互，MUST NOT 承载任务执行、设备控制、文件上传或任何平台写操作。

客户端上行白名单 SHALL 为 `interrupt`、`played`、`text` 三类；`text` MUST 只在文字模式的连接上被处理，语音模式收到时 MUST 忽略。任务进度 MUST 继续走 HTTP 轮询。

#### Scenario: 任务进度仍走轮询

- **WHEN** 用户查看任务清单或任务详情
- **THEN** 页面仍通过既有 HTTP 接口轮询
- **AND** 不建立知识库助手通道

#### Scenario: 通道不承载平台写操作

- **WHEN** 客户端通过知识库助手通道发送白名单以外的消息
- **THEN** 服务端忽略或拒绝该消息
- **AND** 不产生任何平台写操作

### Requirement: 页面提供会话方式选择与启动按键

知识库助手页面 MUST 提供可见的「语音 / 文字」方式选择与启动按键。语音方式下，只有用户点击启动后才申请麦克风并建立实时语音连接；文字方式的行为见 `knowledge-assistant-text-chat` 能力。页面首次打开 MUST NOT 主动申请麦克风权限、MUST NOT 自动建立任何连接。会话进行中再次点击 MUST 结束会话并释放麦克风与播放资源。

#### Scenario: 首次打开不申请麦克风

- **WHEN** 已登录用户打开 `/knowledge-assistant`
- **THEN** 页面显示方式选择、启动按键与空态提示
- **AND** 浏览器未弹出麦克风授权提示，且未建立 `/ws/knowledge-assistant/` 连接

#### Scenario: 点击按键开始语音会话

- **WHEN** 用户在语音方式下点击启动按键并允许麦克风权限
- **THEN** 页面状态从「未开始」进入「连接中」，成功后进入「聆听中」
- **AND** 浏览器开始向实时语音通道发送音频

#### Scenario: 再次点击结束会话

- **WHEN** 会话进行中用户再次点击启动按键
- **THEN** 页面停止采集与播放，并关闭实时语音连接
- **AND** 页面状态回到「未开始」

### Requirement: 知识库助手 Token 用量记录

系统 SHALL 在对话日志中记录模型调用的 token 用量：

- 语音会话（Omni）MUST 消费 AgentScope `ModelCallEndEvent`，记录 `input_tokens`、`output_tokens`、`cache_input_tokens`、`cache_creation_input_tokens`。
- 文字会话 MUST 记录 `deepseek-flash` 每次调用的 `input_tokens` 与 `output_tokens`，provider 为 deepseek，账本来源 MUST 与语音会话可区分。
- 语音 `session_end` MUST 带上本次会话的 token 汇总。

记录 MUST 写入 `logs/knowledge_assistant/YYYY-MM-DD.jsonl` 的 `model_usage` 事件，响应与日志 MUST NOT 暴露密钥。

#### Scenario: Omni 记录每次模型调用

- **WHEN** Omni 完成一次模型回复
- **THEN** JSONL 出现 `model_usage` 事件
- **AND** 包含 input/output tokens
- **AND** 该会话 `session_end` 包含汇总

#### Scenario: 文字会话记录 DeepSeek 用量

- **WHEN** 文字会话完成一次回答
- **THEN** JSONL 出现 `model_usage` 事件，provider 为 deepseek、模型为 `deepseek-flash`
- **AND** 包含 input/output tokens

#### Scenario: 没有 usage 字段

- **WHEN** 模型返回没有 usage
- **THEN** 不写伪造的 0 值事件
- **AND** 会话正常结束

### Requirement: 本地知识检索由语音与文字共用

系统 SHALL 为知识库助手提供本地 RAG：读取配置的数据目录（默认 `D:\Govee\data\rag_data`），解析 `.md/.txt`，切块、嵌入并写入本地索引。语音会话与文字会话 MUST 使用同一份索引：Omni 通过 `search_knowledge` 只读工具检索，文字会话通过同一工具检索；命中片段 MUST 作为回答依据，未命中时 MUST 保持原有回答能力。RAG 不可用或检索失败 MUST NOT 中断会话。

#### Scenario: 文字会话按资料回答

- **WHEN** 用户用文字问「长按开关按键 3 秒会怎样？」
- **AND** `rag_data` 的按键需求文档包含该说明
- **THEN** 检索结果包含对应资料片段
- **AND** 文字回答引用「进入网络待机模式」等资料内容

#### Scenario: 语音会话通过工具检索

- **WHEN** 用户用语音问 H717D 按键问题
- **THEN** 实时模型可调用 `search_knowledge` 工具
- **AND** 工具返回本地资料片段
- **AND** 助手语音回答基于工具结果，而不是仅凭模型记忆

#### Scenario: 资料未覆盖

- **WHEN** 用户问题在 `rag_data` 中没有相关片段
- **THEN** 系统不注入空上下文，或工具返回「没有相关资料」
- **AND** 助手仍正常回答或明确说不知道

#### Scenario: RAG 不可用降级

- **WHEN** 数据目录缺失、嵌入失败或索引损坏
- **THEN** 会话仍可建立
- **AND** 回答退化为无 RAG 的直接对话
- **AND** 失败原因写入运行期日志，不向前端泄露密钥

#### Scenario: 索引增量更新

- **WHEN** `rag_data` 中某个文件内容变化
- **THEN** 下一次检索前只重建该文件的文档
- **AND** 未变化文件不重复嵌入

## MODIFIED Requirements

### Requirement: 就绪状态可查询

系统 SHALL 提供 `GET /api/knowledge-assistant/status/`，返回是否启用、是否就绪、不可用原因、模型名、音色、智能体名称与日志目录；SHALL 另返回文字入口的 `text_model` / `text_ready` / `text_reason`。响应 MUST NOT 含任何密钥。两个入口的就绪状态 MUST 互不影响：任一入口未就绪时，页面 SHALL 在用户点击启动前给出该入口的可读原因，MUST NOT 让用户以为该入口已经可用。

#### Scenario: 配置完整时就绪

- **WHEN** 服务端已配置实时语音所需的 API Key 与依赖
- **THEN** 状态接口返回 `ready=true` 且原因为空字符串
- **AND** 页面语音按键可用

#### Scenario: 缺少密钥时给出原因

- **WHEN** 服务端缺少实时语音所需的 API Key
- **THEN** 状态接口返回 `ready=false` 与中文原因
- **AND** 页面显示该原因，并在点击语音按键前阻止建立会话

#### Scenario: 一个入口未就绪不拖累另一个

- **WHEN** 只缺少文字入口所需的 DeepSeek 密钥
- **THEN** 语音入口仍为就绪
- **AND** 页面只禁用文字方式并显示 `text_reason`

## REMOVED Requirements

### Requirement: WebSocket 只用于实时语音通道

**Reason**: 该通道现在同时承载文字问答（见 ADDED「WebSocket 只承载知识库问答通道」），原「只承载实时语音」的表述已不成立。

**Migration**: 客户端新增可选的 `text` 上行消息；未携带 `mode` 的连接仍按语音处理，既有语音客户端无需修改。

### Requirement: 页面提供单一语音按键启动会话

**Reason**: 页面改为「语音 / 文字」二选一后再启动，单一语音按键不再是唯一入口。

**Migration**: 见 ADDED「页面提供会话方式选择与启动按键」；语音方式行为不变。

### Requirement: 语音模型 Token 用量记录

**Reason**: 该要求只覆盖语音侧用量，文字会话使用 DeepSeek Flash 同样需要记账，需按双入口重写。

**Migration**: 见 ADDED「知识库助手 Token 用量记录」。

### Requirement: 语音 LLM 的 RAG 增强

**Reason**: 该要求把检索写成语音专属，且保留已删除的 Pipeline 分支；文字会话复用同一份索引，需按双入口重写。

**Migration**: 见 ADDED「本地知识检索由语音与文字共用」。

### Requirement: 实时翻译协议适配

**Reason**: `livetranslate` 会话实现已从代码中移除，`KNOWLEDGE_ASSISTANT_MODEL` 含 livetranslate 时会在启动阶段被拒绝。

**Migration**: 无需迁移；实时翻译不在本期范围，需要时另开变更重新设计。

### Requirement: 调用方式可选且默认 Omni 直接对话

**Reason**: 现在只支持 `omni` 一种调用方式；`KNOWLEDGE_ASSISTANT_REALTIME_MODE` 取非 `omni` 值会被拒绝启动。

**Migration**: 删除或保留 `omni` 配置即可；不需要再选调用方式。

### Requirement: 前端可选双路线

**Reason**: `pipeline` 路线（ASR + DeepSeek + TTS）已从前后端删除，路线选择器同步下线。

**Migration**: 文字提问改由 `mode=text` 的 DeepSeek Flash 会话承担，且不合成语音。

### Requirement: Pipeline 问答链路

**Reason**: Pipeline 链路的全部实现（ASR / DeepSeek / TTS 编排）已删除。

**Migration**: 语音统一走 Omni；文字走 `knowledge-assistant-text-chat`。

### Requirement: Pipeline 文本输入

**Reason**: 与本变更的文字问答协议冲突：`text` 消息不再属于 Pipeline，而属于 `mode=text` 的连接。

**Migration**: 使用文字方式（`mode=text`）提问，见 `knowledge-assistant-text-chat`。

### Requirement: Pipeline 回答链路由 Agent 承担

**Reason**: 该要求描述的是 Pipeline 的文本 / 音频分工，随 Pipeline 一起移除。

**Migration**: 无需迁移；Omni 会话与文字会话各自产出文本与音频。

### Requirement: 音频整段发送

**Reason**: 该要求针对 Pipeline 的 TTS 音频累积发送；当前语音为 Omni 流式音频，无整段发送环节。

**Migration**: 前端音频帧格式未变，无需修改客户端。

### Requirement: 用量口径不变

**Reason**: 该要求引用 Pipeline 的 `tts_usage`；Pipeline TTS 移除后不再产生该事件。

**Migration**: 语音与文字均只记 `model_usage`（DashScope 实时 / DeepSeek 文本）。

### Requirement: 回答链路可回退

**Reason**: `KNOWLEDGE_ASSISTANT_PIPELINE_ENGINE` 与 `legacy` 直连实现都已删除。

**Migration**: 无需迁移；如需回退请新开变更。
