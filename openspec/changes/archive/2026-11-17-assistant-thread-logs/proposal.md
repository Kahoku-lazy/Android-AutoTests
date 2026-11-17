## Why

助手测试对话现在只保存最终回复。思考、工具调用和工具结果在 `reply()` 里被吃掉，对话栏也无法回看这一轮发生了什么。需要接上已有事件记录，并在对话栏提供查看入口。SOP 不在本期。

## What Changes

- 助手每一轮改走 `reply_stream`，用现有 `AgentEventRecorder` 记录事件。
- 日志根目录固定为 `logs/agents/assistants/<助手编号>/<对话栏>/`。其下仍由记录器建时间戳目录，写出 JSONL 与 HTML。页面不接受自定义路径。
- 每一轮消息记下该轮报告编号。取消与失败也保留已写出的日志。
- 对话栏增加「日志」。列出该栏各轮的时间与一句话结果；点开在浏览器打开对应 HTML。进行中的一轮显示「还在写」，不打开半份文件。
- 读取必须登录，且路径限制在该助手、该对话栏目录内。不把磁盘路径返回前端。JSONL 不作为页面默认视图。截图 base64 不写入 JSONL。
- 不改 SOP 报告目录，不让 SOP 读取助手日志。

## 关联文档

无。`dev_docs/ARCH_PRD/PRD-平台总需求.md` 不覆盖助手测试对话的运行日志。

## Capabilities

### New Capabilities

- `assistant-thread-log`: 助手对话每一轮的 JSONL 与 HTML 日志、固定目录、白名单读取，以及对话栏的查看入口。

### Modified Capabilities

- `ai-assistant-test-chat`: 发送后的一轮必须留下可回看的运行日志；打开对话仍不跑模型，离开页面仍不取消。

## Impact

- 后端：`backend/apps/ai_assistant` 的对话运行改为流式记录，并增加按栏列出与打开报告的接口。
- 引擎：`engines/backend_bridge` 复用 `ae_harness.event` 记录器，传入助手日志根目录。不改记录器的文件名规则。
- 前端：`frontend/src/modules/ai-assistant` 对话栏增加日志列表与打开报告。
- 测试：一轮写出 jsonl 与 html；越权路径拒绝；进行中不返回可打开的报告。
