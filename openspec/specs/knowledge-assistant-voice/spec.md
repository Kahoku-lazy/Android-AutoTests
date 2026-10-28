# knowledge-assistant-voice Specification

## Purpose
为平台提供一个与「AI 助手」并列的「知识库助手」语音入口：用户点击语音按键后用说话提问，页面实时显示用户与助手双方的对话记录，并把每条最终记录追加到本机日志，供事后核对与排障。

## Requirements

### Requirement: 页面提供单一语音按键启动会话

知识库助手页面 MUST 提供一个可见的语音按键作为会话的唯一启动入口。页面首次打开 MUST NOT 主动申请麦克风权限、MUST NOT 自动建立实时语音连接；只有用户点击该按键后，页面才 SHALL 申请麦克风权限并打开会话。会话进行中再次点击 MUST 结束会话并释放麦克风与播放资源。

#### Scenario: 首次打开不申请麦克风

- **WHEN** 已登录用户打开 `/knowledge-assistant`
- **THEN** 页面显示语音按键与空态提示
- **AND** 浏览器未弹出麦克风授权提示，且未建立 `/ws/knowledge-assistant/` 连接

#### Scenario: 点击按键开始会话

- **WHEN** 用户点击语音按键并允许麦克风权限
- **THEN** 页面状态从「未开始」进入「连接中」，成功后进入「聆听中」
- **AND** 浏览器开始向实时语音通道发送音频

#### Scenario: 再次点击结束会话

- **WHEN** 会话进行中用户再次点击语音按键
- **THEN** 页面停止采集与播放，并关闭实时语音连接
- **AND** 页面状态回到「未开始」

### Requirement: 浏览器与实时模型之间的音频桥接

系统 SHALL 通过后端 WebSocket 通道在浏览器与实时语音模型之间双向转发音频：上行 MUST 为单声道 PCM16、采样率与模型输入采样率一致；下行 MUST 为单声道 PCM16、采样率与模型输出采样率一致。浏览器 MUST NOT 获得模型服务商的 API Key。通道 MUST 要求有效登录凭证；凭证缺失或无效时 MUST 拒绝会话并给出可读提示。

#### Scenario: 上行音频按模型输入采样率发送

- **WHEN** 会话已建立且模型输入采样率为 16000 Hz
- **THEN** 浏览器发送的上行音频为单声道 PCM16、16000 Hz
- **AND** 后端按原样转发给实时模型，不做二次编码

#### Scenario: 下行音频在浏览器按模型输出采样率播放

- **WHEN** 后端收到模型输出采样率为 24000 Hz 的音频块
- **THEN** 浏览器按 24000 Hz 解码并连续播放，不出现按错误采样率变速

#### Scenario: 未登录不能建立语音通道

- **WHEN** 未携带访问凭证或凭证已失效的客户端连接 `/ws/knowledge-assistant/`
- **THEN** 服务端拒绝该会话并返回「请重新登录」类提示
- **AND** 不创建模型会话、不写入对话日志

### Requirement: 对话记录实时呈现

会话期间，页面 SHALL 实时显示用户与助手的对话记录。用户语音转写 SHALL 在模型给出转写后以用户消息出现；助手文本 SHALL 随回复增量出现并最终收敛为完整文本。被打断的助手回复 MUST 标记为「已打断」；会话错误 MUST 以可读消息呈现，MUST NOT 静默丢弃。

#### Scenario: 用户转写出现在记录区

- **WHEN** 用户说出一句可识别的话
- **THEN** 记录区新增一条用户消息，内容为该句转写

#### Scenario: 助手回复增量呈现

- **WHEN** 助手开始返回文本增量
- **THEN** 记录区先出现助手消息占位，随后文本随增量增长
- **AND** 回复结束时该消息收敛为完整文本

#### Scenario: 用户打断助手

- **WHEN** 助手回复期间用户开口说话
- **THEN** 正在播放的助手音频停止
- **AND** 被截断的助手消息标记为「已打断」，保留用户实际听到的文本前缀

#### Scenario: 会话失败可读

- **WHEN** 模型连接失败、服务端缺少必要配置或通道异常断开
- **THEN** 页面显示中文错误提示
- **AND** 页面状态回到「未开始」或「出错」，不显示为仍在聆听

### Requirement: 对话记录写入本地日志

每个会话的每条最终对话记录（用户与助手各一条）SHALL 追加写入本机日志文件，按自然日分文件，路径为 `logs/knowledge_assistant/YYYY-MM-DD.jsonl`，每行一个 JSON 对象且 MUST 含 `ts`、`session_id`、`user_id`、`role`、`text` 字段。会话开始与会话结束 SHALL 各写一条事件记录。日志写入 MUST NOT 阻塞或中断语音会话；写入失败 MUST 记录运行期告警并继续会话。日志 MUST NOT 记录 API Key、音频数据或完整鉴权凭证。

#### Scenario: 一轮问答落两条记录

- **WHEN** 用户完成一轮问答且助手正常回复结束
- **THEN** 当日 JSONL 文件新增一条 `role=user` 记录与一条 `role=assistant` 记录
- **AND** 两条记录的 `session_id` 相同，`text` 分别等于屏幕上的最终文本

#### Scenario: 日志按自然日分文件

- **WHEN** 会话跨过本地自然日零点
- **THEN** 零点前的记录写入前一日文件，零点后的记录写入新一日文件

#### Scenario: 日志写入失败不中断会话

- **WHEN** 日志目录不可写或磁盘写入失败
- **THEN** 语音会话继续，页面仍实时显示对话
- **AND** 运行期日志出现一条告警，不向用户抛出未处理异常

#### Scenario: 日志不含敏感数据

- **WHEN** 检查任一对话日志文件
- **THEN** 不存在 API Key、音频字节或 Authorization 头内容

### Requirement: 就绪状态可查询

系统 SHALL 提供 `GET /api/knowledge-assistant/status/`，返回是否启用、是否就绪、不可用原因、模型名、音色、智能体名称与日志目录。响应 MUST NOT 含任何密钥。未就绪时页面 SHALL 在用户点击语音按键前给出可读原因，MUST NOT 让用户以为会话已经可用。

#### Scenario: 配置完整时就绪

- **WHEN** 服务端已配置实时语音所需的 API Key 与依赖
- **THEN** 状态接口返回 `ready=true` 且原因为空字符串
- **AND** 页面语音按键可用

#### Scenario: 缺少密钥时给出原因

- **WHEN** 服务端缺少实时语音所需的 API Key
- **THEN** 状态接口返回 `ready=false` 与中文原因
- **AND** 页面显示该原因，并在点击语音按键前阻止建立会话

### Requirement: 会话结束释放全部资源

会话结束（用户结束、页面离开、通道断开或服务端异常）时，系统 MUST 停止麦克风采集与音频播放，关闭 WebSocket 通道，关闭实时模型会话，并写入会话结束事件。系统 MUST NOT 继续向已关闭的通道推送音频或转写。

#### Scenario: 用户主动结束

- **WHEN** 用户再次点击语音按键结束会话
- **THEN** 麦克风轨道停止、播放缓冲清空、通道关闭、模型会话关闭
- **AND** 当日日志新增一条会话结束事件

#### Scenario: 页面离开

- **WHEN** 用户在会话进行中离开 `/knowledge-assistant` 页面
- **THEN** 会话按「用户主动结束」同样释放资源
- **AND** 再次进入页面时不会自动恢复旧会话

### Requirement: WebSocket 只用于实时语音通道

平台的任务进度与列表 MUST NOT 因本能力改用 WebSocket；本能力新增的 WebSocket 通道 MUST 只承载知识库助手的实时语音与转写事件。该通道 MUST NOT 承载任务执行、设备控制、文件上传或平台写操作。

#### Scenario: 任务进度仍走轮询

- **WHEN** 用户查看任务清单或任务详情
- **THEN** 页面仍通过既有 HTTP 接口轮询，不建立知识库助手通道

#### Scenario: 通道不承载平台写操作

- **WHEN** 客户端通过知识库助手通道发送非语音控制消息
- **THEN** 服务端只接受「打断」与「播放进度」两类白名单消息，其余消息被忽略或拒绝
- **AND** 不产生任何平台写操作

### Requirement: 麦克风输入可观测且无输入可提示

会话进行中，页面 SHALL 显示麦克风状态，至少区分「未采集到音频」「有信号、等待说话」「有输入」三种状态，并显示随音量变化的电平。服务端 SHALL 统计每个会话的上行音频帧数与字节数，并写入该会话的 `session_end` 记录。实时语音会话就绪后 6 秒内未收到任何上行音频帧时，服务端 SHALL 下发一条非致命提示，页面 MUST 以可读文案提示用户检查系统默认输入设备与浏览器麦克风权限，且 MUST NOT 因此关闭会话。

#### Scenario: 有声音时电平更新

- **WHEN** 用户对着麦克风说话且浏览器已授权
- **THEN** 页面麦克风状态显示「有输入」，电平条随音量变化

#### Scenario: 设备静音时可见

- **WHEN** 麦克风已授权但持续没有音频帧
- **THEN** 页面麦克风状态显示「未采集到音频」
- **AND** 服务端在 6 秒后下发一次检查输入设备与权限的提示

#### Scenario: 会话结束记录音频帧数

- **WHEN** 一次语音会话结束
- **THEN** `logs/knowledge_assistant/YYYY-MM-DD.jsonl` 的 `session_end` 记录包含 `audio_frames` 与 `audio_bytes`
- **AND** 有正常说话时 `audio_frames` 大于 0

#### Scenario: 无输入提示不关闭会话

- **WHEN** 服务端下发无输入提示
- **THEN** 页面显示提示但仍保持「聆听中」，用户可切换设备后继续

### Requirement: 实时翻译协议适配

`livetranslate` 模式 SHALL 通过 DashScope Realtime WebSocket 建立会话，并发送 `session.output_modalities`、`session.translation.language`、`session.audio.input.turn_detection=speaker_detection`。源语种转写 SHALL 映射为用户消息；译文 SHALL 从 `response.audio_transcript.delta` 或 `response.text.delta` 映射为助手消息；音频 SHALL 从 `response.audio.delta` 按 24kHz PCM16 播放。会话结束前 SHALL 发送 `session.finish`。

#### Scenario: 中文语音翻译成中文

- **WHEN** 用户说“设备管理里怎么连接设备”，目标语种为 `zh`
- **THEN** 页面出现用户源语转写
- **AND** 助手消息出现中文译文

#### Scenario: 目标语种可配

- **WHEN** 配置 `KNOWLEDGE_ASSISTANT_TRANSLATION_LANGUAGE=en`
- **THEN** `session.translation.language` 为 `en`
- **AND** 助手译文为英文

#### Scenario: 就绪事件暴露调用方式

- **WHEN** WS 会话建立完成
- **THEN** `ready` 事件包含 `mode` 与 `translation_language`
- **AND** 页面「模式」行显示实时翻译或语音问答

### Requirement: 调用方式可选且默认 Omni 直接对话

系统 SHALL 支持两种实时语音调用方式：`omni`（实时对话）与 `livetranslate`（实时翻译）。默认调用方式 MUST 为 `omni`，默认模型 MUST 为 `qwen3.5-omni-plus-realtime`。用户 SHALL 能通过环境变量 `KNOWLEDGE_ASSISTANT_REALTIME_MODE` 显式选择调用方式，或仅设置 `KNOWLEDGE_ASSISTANT_MODEL` 由模型名推断：包含 `livetranslate` 走翻译，否则走 `omni`。调用方式与模型名不匹配时，系统 MUST 拒绝启动并在状态接口返回可读原因。

#### Scenario: 默认使用 omni 问答

- **WHEN** 只配置 `DASHSCOPE_API_KEY`
- **THEN** 状态接口返回 `mode=omni`
- **AND** 模型为 `qwen3.5-omni-plus-realtime`

#### Scenario: 显式启用实时翻译

- **WHEN** 配置 `KNOWLEDGE_ASSISTANT_REALTIME_MODE=livetranslate` 与 `KNOWLEDGE_ASSISTANT_MODEL=qwen3.8-livetranslate-flash-realtime`
- **THEN** 会话使用实时翻译适配器

#### Scenario: 只配模型名自动推断

- **WHEN** 只配置 `KNOWLEDGE_ASSISTANT_MODEL=qwen3.8-livetranslate-flash-realtime`
- **THEN** 调用方式自动推断为 `livetranslate`

#### Scenario: 模式与模型不匹配

- **WHEN** 配置 `KNOWLEDGE_ASSISTANT_REALTIME_MODE=omni` 且模型为 LiveTranslate
- **THEN** 状态接口返回 `ready=false` 与可读原因
- **AND** 不创建模型会话

### Requirement: 直接对话不注入预设答案

系统 SHALL 使用简洁的直接对话系统提示词，MUST NOT 注入平台模块速览、固定答案话术或预先写好的回复。助手回复 MUST 由所选实时模型根据用户语音与通用中文语音助手提示自然生成，而不是从预设答案表中匹配。

#### Scenario: 用户自由提问

- **WHEN** 用户问一个平台使用问题
- **THEN** 助手回答由模型实时生成
- **AND** 代码中不存在按问题匹配的预设回复表

#### Scenario: 提示词只保留直接对话约束

- **WHEN** 检查知识库助手的系统提示词
- **THEN** 只包含中文语音助手角色、简短口语化、回答长度等通用约束
- **AND** 不包含「设备管理：扫描、连接……」这类平台知识速览或逐条回答模板

### Requirement: 前端可选双路线

系统 SHALL 在前端提供两条按会话可选的语音路线：

1. `omni`：`qwen3.5-omni-plus-realtime` 直连，音色 `Tina`。
2. `pipeline`：`livetranslate` ASR + `deepseek-flash` 回答 + `sambert-zhichu-v1`（知厨）播报。

默认路线 MUST 为 `omni`。用户切换路线后，WS 连接 MUST 携带 `mode=omni` 或 `mode=pipeline`；后端 MUST 按该连接选择对应会话实现，不得影响其他连接。页面「模式」行 MUST 显示当前路线。未开始会话时，页面「模型」行 MUST 按当前所选路线显示：`omni` 显示后端默认模型，`pipeline` 显示 pipeline 的 LLM/TTS 模型与音色；会话开始后 MUST 以 `ready` 事件返回的实际 `model`/`voice` 为准。

#### Scenario: 默认 Omni 直连

- **WHEN** 用户只配置 `DASHSCOPE_API_KEY` 并打开页面
- **THEN** 路线默认为 `omni`
- **AND** 模型为 `qwen3.5-omni-plus-realtime`、音色 `Tina`

#### Scenario: 选择 Pipeline

- **WHEN** 用户选择「ASR + DeepSeek Flash + TTS」并开始对话
- **THEN** WS 连接携带 `mode=pipeline`
- **AND** 页面模式显示 ASR + DeepSeek + TTS
- **AND** 模型行显示 `deepseek-flash + sambert-zhichu-v1` 与「知厨」
- **AND** 另一个 Omni 连接不受影响

#### Scenario: 非法 mode

- **WHEN** WS 携带不支持的 mode
- **THEN** 连接返回可读错误并关闭
- **AND** 不创建任何模型会话

### Requirement: Pipeline 问答链路

`pipeline` 模式 SHALL 按以下顺序处理一轮语音：

1. 把浏览器上行 PCM 送入 `qwen3.8-livetranslate-flash-realtime`，只消费源语转写结果。
2. 把源语文本送入 `deepseek-flash`，流式得到中文回答。
3. 把回答文本送入 `sambert-zhichu-v1`，生成 24kHz PCM16 音频并下发浏览器。
4. 在页面上先显示用户源语转写，再显示助手回答文本，并播放 TTS 音频。

ASR 的翻译输出 MUST NOT 被当作助手回答。TTS 失败时 MUST 保留已生成的文字回答，并给出可读提示。TTS 厂商 SHALL 可通过 `KNOWLEDGE_ASSISTANT_PIPELINE_TTS_PROVIDER` 选择 `sambert` 或 `qwen`；默认 MUST 为 `sambert`。

#### Scenario: 用户问，模型答

- **WHEN** 用户说“设备管理里怎么连接设备”
- **THEN** 页面显示用户源语转写
- **AND** 页面显示 DeepSeek 生成的回答
- **AND** 浏览器播放 Sambert「知厨」生成的语音

#### Scenario: 多轮上下文

- **WHEN** 用户在同一会话里连续问两个相关问题
- **THEN** 第二个回答能引用第一轮的用户/助手文本

#### Scenario: 打断

- **WHEN** 助手正在生成或播报时用户点击「打断」
- **THEN** 当前 DeepSeek/TTS 任务被取消
- **AND** 浏览器播放队列被清空
- **AND** 页面回到聆听状态

#### Scenario: TTS 不可用

- **WHEN** `sambert-zhichu-v1` 调用失败
- **THEN** 助手文字回答仍显示并落日志
- **AND** 页面提示语音播报失败
- **AND** 会话不中断

### Requirement: 语音 LLM 的 RAG 增强

系统 SHALL 为语音助手提供本地 RAG：读取配置的数据目录（默认 `D:\Govee\data\rag_data`），解析 `.md/.txt`，切块、嵌入并写入本地索引。

- `pipeline`：每轮提问后先检索，命中片段作为上下文注入 `deepseek-flash`。
- `omni`：通过 `search_knowledge` 只读工具检索，把工具结果交回实时模型组织回答。

未命中时 MUST 保持原有直接回答；RAG 不可用或检索失败 MUST NOT 中断语音会话。

#### Scenario: Pipeline 按资料回答

- **WHEN** 用户问“长按开关按键 3 秒会怎样？”
- **AND** `rag_data` 的按键需求文档包含该说明
- **THEN** 检索结果包含对应资料片段
- **AND** DeepSeek 的回答引用“进入网络待机模式”等资料内容

#### Scenario: Omni 通过工具检索

- **WHEN** 用户选择 `omni` 路线并问 H717D 按键问题
- **THEN** 实时模型可调用 `search_knowledge` 工具
- **AND** 工具返回本地资料片段
- **AND** 助手语音回答基于工具结果，而不是仅凭模型记忆

#### Scenario: 资料未覆盖

- **WHEN** 用户问题在 `rag_data` 中没有相关片段
- **THEN** 系统不注入空上下文或工具返回“没有相关资料”
- **AND** 助手仍正常回答或明确说不知道

#### Scenario: RAG 不可用降级

- **WHEN** 数据目录缺失、嵌入失败或索引损坏
- **THEN** 语音会话仍可建立
- **AND** 回答退化为无 RAG 的直接对话
- **AND** 失败原因写入运行期日志，不向前端泄露密钥

#### Scenario: 索引增量更新

- **WHEN** `rag_data` 中某个文件内容变化
- **THEN** 下一次检索前只重建该文件的文档
- **AND** 未变化文件不重复嵌入

### Requirement: Pipeline 文本输入

`pipeline` 路线 SHALL 提供文本输入框；用户输入文字后，系统 MUST 跳过 ASR，把文字直接交给 DeepSeek（含 RAG）并合成 TTS 音频。未开始会话时发送文字 MUST 自动建立纯文本会话：不申请麦克风、不发送空音频，但仍建立播放器与 `/ws/knowledge-assistant/?mode=pipeline` 连接。

WS 客户端消息白名单 SHALL 在 `interrupt` / `played` 之外增加 `text`，且 `text` 只允许 Pipeline 会话处理。

#### Scenario: 纯文本提问

- **WHEN** 用户在 Pipeline 路线输入“长按开关按键3秒会怎样？”并发送
- **THEN** 页面出现用户文本消息
- **AND** DeepSeek 按 RAG 资料生成回答
- **AND** 浏览器播放 Sambert TTS 音频

#### Scenario: 会话中追加文字

- **WHEN** 语音会话已开始，用户输入文字并发送
- **THEN** 当前回答被取消（如有）
- **AND** 新文字作为新一轮用户问题处理

#### Scenario: 纯文本不打麦克风提示

- **WHEN** 用户未授权麦克风、仅使用文字提问
- **THEN** 会话正常建立
- **AND** 不显示“没有检测到麦克风音频”的提示

#### Scenario: Omni 路线不显示文本输入

- **WHEN** 路线为 `omni`
- **THEN** 不显示 Pipeline 文本输入框

### Requirement: 语音模型 Token 用量记录

系统 SHALL 在对话日志中记录每次语音模型调用的 token 用量：

- `omni`：消费 AgentScope `ModelCallEndEvent`，记录 `input_tokens`、`output_tokens`、`cache_input_tokens`、`cache_creation_input_tokens`。
- `pipeline`：记录 DeepSeek `ChatResponse.usage`；ASR 的 `ResponseDoneEvent` 有 token 时也记录。
- `session_end` MUST 带上本次会话的 token 汇总。

记录 MUST 写入 `logs/knowledge_assistant/YYYY-MM-DD.jsonl` 的 `model_usage` 事件，不向前端暴露密钥。

#### Scenario: Omni 记录每次模型调用

- **WHEN** Omni 完成一次模型回复
- **THEN** JSONL 出现 `model_usage` 事件
- **AND** 包含 input/output tokens
- **AND** `session_end` 包含汇总

#### Scenario: Pipeline 记录 DeepSeek 用量

- **WHEN** Pipeline 完成一次 DeepSeek 回答
- **THEN** JSONL 出现 `model_usage` 事件，`provider="deepseek"`
- **AND** 包含 input/output tokens
- **AND** `session_end` 包含汇总

#### Scenario: 没有 usage 字段

- **WHEN** 模型返回没有 usage
- **THEN** 不写伪造的 0 值事件
- **AND** 会话正常结束

### Requirement: Pipeline 回答链路由 Agent 承担
`pipeline` 路线的回答与语音合成分工 MUST 由 Agent 承担：文本来自 Agent 的文本增量事件，语音来自语音合成中间件产出的音频块。ASR 与传输层 MUST NOT 改变。语音合成适配器 MUST 复用现有 Sambert / Qwen 引擎与音色，MUST NOT 改动默认音色。

#### Scenario: 一轮回答同时产出文本与音频
- **WHEN** 用户在 pipeline 路线说一句话，模型正常返回
- **THEN** 前端按顺序收到 `reply_start`、若干 `transcript_delta`、`transcript_final`、`reply_end`，并在 `reply_end` 之前收到一整段 `audio`

#### Scenario: 音色不变
- **WHEN** 默认配置（sambert / 知厨）下跑一轮回答
- **THEN** 播报仍使用原音色与采样率，不因改为 Agent 而换声音

### Requirement: 音频整段发送
语音合成中间件逐块产出的音频 MUST 由回答器累积成一段 PCM，在 `reply_end` 之前一次性发送；前端音频帧格式 MUST 保持不变。

#### Scenario: 多块音频合并
- **WHEN** 中间件分三次产出三段音频
- **THEN** 前端只收到一次 `audio` 帧，内容是三段按序拼接

### Requirement: 用量口径不变
`model_usage` MUST 取本轮 `ModelCallEndEvent` 的输入、输出与两项缓存 token；`tts_usage` MUST 仍按本轮总字符数记一条，MUST NOT 因改为逐块合成而改变计费口径。

#### Scenario: 一轮回答的用量
- **WHEN** 一轮回答结束
- **THEN** 日志里 `model_usage` 一条（四个 token 字段），`tts_usage` 一条（字符数为整轮文本长度）

### Requirement: 回答链路可回退
回答链路 MUST 由 `KNOWLEDGE_ASSISTANT_PIPELINE_ENGINE` 选择：`agent`（默认）走 Agent，`legacy` 走原直连实现。取值非法时 MUST 拒绝启动并给出可读原因。

#### Scenario: 回退到旧实现
- **WHEN** 配置 `KNOWLEDGE_ASSISTANT_PIPELINE_ENGINE=legacy`
- **THEN** 会话按原直连模型 + 单独合成的方式工作

#### Scenario: 非法取值
- **WHEN** 配置成其它值
- **THEN** 启动失败，报错信息点名该环境变量与可选值
