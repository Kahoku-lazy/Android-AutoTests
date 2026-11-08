## Why

文字问答现在是两步：先点左侧「开始对话」建立连接，右侧输入框才解除禁用；没点之前输入框是灰的，占位文案还写着「先点『开始对话』，再输入文字提问」。语音需要先点一次是因为要弹麦克风授权，文字没有这个约束——用户面对一个聊天框，直觉就是「打字、回车」，多一步启动只会让人以为坏了。

## What Changes

- 文字方式下**直接输入并发送即可**：不再需要先点启动按键。首次发送时若尚未连接，自动完成「续期 → 建连」，连接就绪后立即把这条文本发出去，不需要用户再点一次。
- 连接建立前发送的文本 MUST 排队且不丢失；连接失败时 MUST 给出可读错误，MUST NOT 把文本吞掉后静默。
- 文字方式的输入框可用性只取决于「是否文字方式」与「是否有回答进行中」，MUST NOT 再依赖「是否已连接」。
- 文字方式下不再显示「开始对话」按键（连接已隐式建立）；会话进行中仍显示「结束对话」。
- 语音方式完全不变：仍需点击圆形语音键开始、麦克风授权时机不变。
- 就绪状态（`text_ready`）仍作为发送前置条件：文字服务未就绪时输入框保持禁用，页面顶部的就绪错误照常提示。

## 关联文档

- 既有规格 `knowledge-assistant-text-chat`：「页面提供语音与文字两种会话方式」原文要求「选定后再点击启动按键建立会话」，本变更只改文字方式的启动方式，语音方式与「切换方式需先结束会话」不变。
- 既有规格 `knowledge-assistant-voice`：语音链路的启动与鉴权行为不受影响。
- 上一张在途变更 `fix-auth-refresh`：本变更复用其 `ensureFreshToken()`，自动建连也走「先续期再连」。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `knowledge-assistant-text-chat`: 改写「页面提供语音与文字两种会话方式」——文字方式改为输入即发送、首次发送自动建连，输入框可用性不再要求已连接。

## Impact

- 前端：`modules/knowledge-assistant/helpers/mode.ts`（发送门控）、`composables/useAssistantSession.ts`（待发队列 + 自动建连）、`index.vue`（可用性与占位文案）、`components/VoiceConsole.vue`（文字方式隐藏启动键）、`constants.ts`（文案）、模块 `AGENTS.md`（约束同步）。
- 后端 / 接口 / 路由：无改动。
- 测试：`frontend/tests/knowledge-assistant/p0/text-chat.spec.ts` 更新门控用例；新增 `text-direct-send.spec.ts` 覆盖「未连接时发送自动建连并补发」。
- 非目标：不改语音启动方式；不改 WS 协议与 `text` 消息格式；不改长度上限与空文本规则。
