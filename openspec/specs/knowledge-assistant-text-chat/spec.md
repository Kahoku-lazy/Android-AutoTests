# knowledge-assistant-text-chat Specification

## Purpose
为知识库助手提供打字提问的第二入口：用户在同一个对话记录面板里输入问题，回答以流式文本返回，并与语音入口共用同一份本地知识、同一个对话日志与同一本用量账。

## Requirements

### Requirement: 页面提供语音与文字两种会话方式

知识库助手页面 MUST 提供可见的「语音 / 文字」方式选择，用户选定后再点击启动按键建立会话。文字方式 MUST NOT 申请麦克风权限、MUST NOT 创建音频播放；语音方式行为保持不变。一次会话只允许一种方式，切换方式 MUST 先结束当前会话再重新开始。文字方式下对话记录的输入框 MUST 可发送，语音方式下 MUST 不可发送。

#### Scenario: 选择文字方式不申请麦克风

- **WHEN** 用户选择「文字」并点击开始对话
- **THEN** 浏览器未弹出麦克风授权提示
- **AND** 未创建音频播放器，且连接携带 `mode=text`

#### Scenario: 文字方式可发送、语音方式禁用输入

- **WHEN** 文字会话已建立
- **THEN** 对话记录输入框可输入并发送
- **AND** 语音会话中同一输入框不可发送，并提示改用语音

#### Scenario: 切换方式需先结束会话

- **WHEN** 语音会话进行中用户选择「文字」
- **THEN** 页面提示先结束当前会话
- **AND** 已建立的连接方式不发生改变

### Requirement: 文字提问复用同一条知识库通道

文字问答 MUST 复用 `/ws/knowledge-assistant/` 通道并携带 `mode=text`，MUST NOT 新增第二条 WebSocket 连接或 SSE 接口。客户端上行白名单 MUST 包含 `{"type":"text","text":"..."}`，该消息 MUST 只在文字模式被处理；超过长度上限或内容为空白的文本 MUST 被拒绝或忽略，MUST NOT 触发模型调用。服务端 MUST 先回显用户消息，再以既有 `reply_start` / `transcript_delta` / `transcript_final` / `reply_end` 事件下发助手流式回答。

#### Scenario: 发送后回显并流式回答

- **WHEN** 用户在文字会话中发送「长按开关按键3秒会怎样？」
- **THEN** 对话记录先出现内容为该句的用户消息
- **AND** 助手消息随后以增量增长，并在结束时收敛为完整文本

#### Scenario: 空白文本不触发模型

- **WHEN** 用户发送纯空白内容
- **THEN** 不出现用户消息，也不产生助手回答
- **AND** 不产生模型调用

#### Scenario: 超长文本被拒

- **WHEN** 用户发送超过长度上限的文本
- **THEN** 页面给出可读提示
- **AND** 不产生模型调用与日志记录

#### Scenario: 语音模式忽略 text 消息

- **WHEN** 语音会话的连接收到 `text` 消息
- **THEN** 服务端忽略该消息并记录调试日志
- **AND** 不产生回答，也不影响正在进行的语音会话

### Requirement: 文字会话使用 DeepSeek Flash 与本地知识检索

文字会话 MUST 使用 `deepseek-flash` 作为回答模型。MUST 复用与语音入口相同的本地知识检索工具，命中资料时 MUST 以资料为依据回答；检索未命中或不可用时 MUST 退化为直接回答，MUST NOT 中断会话。回答 MUST NOT 来自预设答案表。

#### Scenario: 命中资料时引用资料

- **WHEN** 用户问「长按开关按键3秒会怎样？」，且本地资料包含该说明
- **THEN** 检索命中对应片段
- **AND** 文字回答与该资料一致，而不是仅凭模型记忆

#### Scenario: 资料未覆盖时不编造

- **WHEN** 问题在本地资料中没有相关片段
- **THEN** 助手明确说明资料未覆盖，或给出不含具体参数的通用回答
- **AND** 不编造型号、数值或结论

#### Scenario: 检索不可用时降级

- **WHEN** 索引缺失、嵌入失败或检索异常
- **THEN** 文字会话仍能回答
- **AND** 运行期日志出现一条告警，不向前端泄露密钥

### Requirement: 文字会话的多轮上下文只在本次连接内

同一次文字会话内，后续提问 MUST 能引用本次会话已完成的用户与助手文本。语音会话与文字会话 MUST NOT 共享上下文，切换方式 MUST 视为新话题；会话结束后 MUST NOT 保留可恢复的历史。

#### Scenario: 同一会话内追问

- **WHEN** 用户先问「H717D 怎么恢复出厂设置」，再问「那按键怎么操作」
- **THEN** 第二个回答能承接第一轮的上下文

#### Scenario: 切换方式不继承上下文

- **WHEN** 用户先完成一次语音问答，结束会话后改用文字问「刚才那个呢」
- **THEN** 文字回答不假设自己已知语音会话的内容

### Requirement: 文字入口的就绪状态独立可查

`GET /api/knowledge-assistant/status/` MUST 在既有字段外返回文字入口的模型名与就绪状态（`text_model` / `text_ready` / `text_reason`），响应 MUST NOT 含任何密钥。缺少 DeepSeek 密钥时 `text_ready` MUST 为 false 并给出中文原因，且 MUST NOT 影响语音入口的就绪结果。文字会话失败 MUST 在页面给出中文提示，MUST NOT 静默丢弃。

#### Scenario: 只有语音可用

- **WHEN** 服务端具备实时语音所需密钥但缺少 DeepSeek 密钥
- **THEN** 语音入口可用
- **AND** 文字入口禁用，且页面显示 `text_reason` 给出的原因

#### Scenario: 两个入口都可用

- **WHEN** 两个入口所需密钥与依赖都具备
- **THEN** 状态接口返回 `text_ready=true` 且 `text_model=deepseek-flash`
- **AND** 页面文字方式可选

#### Scenario: 会话失败可读并可重试

- **WHEN** 文字模型调用失败或通道异常断开
- **THEN** 页面显示中文错误提示
- **AND** 用户可以结束会话后重新开始

### Requirement: 文字对话写入日志与用量账本

文字会话的每条最终用户与助手文本 MUST 写入与其他会话相同的 `logs/knowledge_assistant/YYYY-MM-DD.jsonl`，记录 MUST 含 `ts` / `session_id` / `user_id` / `role` / `text`，且会话开始事件 MUST 标明本次是文字方式。每次模型调用 MUST 写 `model_usage` 事件（provider 为 deepseek、模型为 `deepseek-flash`）并进入用量账本，账本 MUST 能和语音会话区分来源。日志或入账失败 MUST NOT 中断会话。

#### Scenario: 一轮文字问答落两条记录

- **WHEN** 一轮文字问答正常结束
- **THEN** 当日 JSONL 新增 `role=user` 与 `role=assistant` 各一条
- **AND** 两条记录 `session_id` 相同，`text` 等于屏幕上的最终文本
- **AND** 该会话的 `session_start` 记录含文字方式的标识

#### Scenario: 用量进入账本并与语音可分

- **WHEN** 完成一次文字回答
- **THEN** 日志出现 `model_usage` 事件，provider 为 deepseek、模型为 `deepseek-flash`
- **AND** 用量账本新增对应记录，且来源与语音会话不同

#### Scenario: 写入失败不中断会话

- **WHEN** 日志目录不可写或入账失败
- **THEN** 回答仍在页面正常显示
- **AND** 运行期日志出现告警，不向用户抛出未处理异常
