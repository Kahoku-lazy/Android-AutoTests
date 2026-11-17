## Context

动机见 `proposal.md - Why`。方案需要的现状事实：

- `useAssistantSession.submitText()` 现在第一句是 `if (!canType.value || !value) return`，而 `canType = canSendText(mode, socketOpen, state)` —— 没连上就直接丢弃输入。
- `start()` 会重置状态（`messages`、`state=connecting`）并建连；`ready` 事件到达后才置 `socketOpen=true`。
- 页面把 `canType` 直接传给输入框的 `can-send`；`VoiceConsole` 在两种方式下都渲染「开始对话」按钮。
- 就绪状态由 `/api/knowledge-assistant/status/` 提供，`text_ready` 为假时页面顶部已给出 ErrorState。

约束：不改 WS 协议与 `text` 消息格式；语音启动方式不变；切方式仍需先结束会话。

## Goals / Non-Goals

**Goals:**

- 文字方式点发送即可，首次发送自动建连并把这句话补发出去。
- 连接前、连接中的输入不丢失，也不重复发送。
- 语音方式的行为、授权时机与按钮完全不变。

**Non-Goals:**

- 不把语音也改成「点一下就自动开麦」——麦克风授权需要用户手势，另案。
- 不在未就绪（`text_ready=false`）时强行建连：就绪检查仍是前置条件。
- 不做消息重发/失败重试队列（发送失败就是会话失败，提示后可重新输入）。

## Decisions

**1. 用「待发队列」而不是「先连上再让用户重打」。**

`submitText()` 在未连接时把文本存进 `pendingText`，然后复用既有 `start("text")` 建连；`ready` 事件里把 `pendingText` 取出并 `send`，随即清空。这样用户只做了一次动作（点发送），中间的网络往返对他是不可见的。

备选：把输入框改成「发送时若无连接则提示先开始对话」→ 否，这正是要消除的摩擦。

**2. `canSendText()` 去掉 `connected` 参数。**

门控语义从「已连接 + 不忙」改成「文字方式 + 不忙」。`connected` 不再是发送前提，因为发送本身会触发连接。签名从 `(mode, connected, state)` 改为 `(mode, state)`，调用方只有 `useAssistantSession` 与单测，改动面很小；保留旧参数会让「传 false 也能发」看起来自相矛盾。

**3. 就绪检查上移到页面，不塞进 composable。**

`index.vue` 把 `can-send` 从 `canType` 改为 `canType && canStart`（`canStart` 已按方式取 `text_ready`）。composable 不关心 `/status`，避免把服务就绪状态耦合进会话逻辑。

**4. 文字方式隐藏「开始对话」按钮，保留「结束对话」。**

连接已经隐式建立，再摆一个启动键会让人以为「不点就不算数」。语音方式的圆形按键与「开始对话」按钮原样保留。

**5. 失败时清空待发文本并报错。**

`fail()` 里清掉 `pendingText`，避免下一次会话把上一句旧文本发出去；同时用户能看到错误、重新输入。

## 模块防火墙自检

- 跨 App import：无，纯前端。
- `INSERT/UPDATE/DELETE`：无。
- 前端不直连模型/数据库：仍只经既有 `/ws/knowledge-assistant/`。
- 通道：不新增端点、不新增 WS；只是把「何时建连」从按钮改成第一次发送。
- 模块边界：改动都在 `modules/knowledge-assistant/` 内，不新增 `shared/` 件。

## Risks / Trade-offs

- **就绪状态过期**（页面挂了很久，`text_ready` 变了但没重拉）→ 建连失败会落到可读错误，与今天的失败路径一致；`onActivated` 的既有重拉逻辑不变。
- **`start()` 会清空对话记录** → 文字方式的「新会话」本来就是这个语义；如果用户在上一段会话结束后再发，记录会重置，与点「开始对话」一致。
- **待发文本按顺序排队** → 连接只需一次往返，正常情况下队列里最多一条；用户在等待期间连发时按原顺序补发，不丢不重。若将来要支持「连接中禁发」，只需收紧 `canSendText` 的忙碌判定。
- **语音按钮位置变化** → 文字方式下左侧动作区会空出一行，需要确认 `.kb-actions` 的间距不塌（样式层用既有 `gap`，无需新增令牌）。

## Migration Plan

纯前端，无数据迁移、无接口变更。上线后硬刷新生效；回滚为单次 `git revert`。
