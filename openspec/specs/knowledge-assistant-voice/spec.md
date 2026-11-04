# knowledge-assistant-voice Specification

## Purpose
为平台提供一个与「AI 助手」并列的「知识库助手」语音入口：用户点击语音按键后用说话提问，页面实时显示用户与助手双方的对话记录，并把每条最终记录追加到本机日志，供事后核对与排障。

## Requirements

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
