## Context

助手对话现在调用 `agent.reply()`，只把最终文本写入 `ai_assistant_messages`。`AgentEventRecorder` 已经能把 `reply_stream` 记成 JSONL 与 HTML，目录由调用方传入，文件名由记录器按时间戳生成。平台 SOP 报告根目录是 `logs/agents/backend_bridge/`。动机见 proposal.md。

## Goals / Non-Goals

**Goals:**

- 助手每一轮复用记录器，不新造日志格式。
- 根目录固定，读取走白名单。
- 对话栏只打开 HTML。

**Non-Goals:**

- 不改 SOP，不让 SOP 读取助手日志。
- 不在对话页内嵌第二套事件时间轴。
- 不开放用户手填日志路径。
- 不把 JSONL 作为默认页面。

## Decisions

### 1. 根目录单独常量

在 `backend_bridge/reports` 增加 `ASSISTANT_LOG_ROOT = logs/agents/assistants`。一轮的传入目录是 `ASSISTANT_LOG_ROOT / assistant_id / thread_id`。记录器继续自己建时间戳子目录。不复用 `REPORT_ROOT`，避免和 SOP 混目录。

### 2. 消息只记报告编号

`ai_assistant_messages` 增加可空的 `report_id`。它是时间戳目录名，不是绝对路径。列表接口返回编号、时间和一句话结果。打开接口用编号拼路径，解析后必须仍在该栏目录内，否则 404。

### 3. 运行中不暴露半份文件

记录器边写边落盘。列表在该轮状态仍为 running 时标记 `writing=true`，打开接口返回 409。轮次结束、取消或失败后再允许打开已有 HTML。

### 4. 查看入口在对话栏

对话栏增加「日志」按钮，打开本栏列表。点某一轮用新窗口打开 HTML。不把日志原文嵌进气泡。列表在**对话区内部就地展开**（插在状态行与消息流之间），不改 `.ai-chat__body` 的两栏网格、不做弹层、不新增第二层滚动；日志多了由 `.doc-body` 滚。

## 模块防火墙自检

- 写 `report_id` 只经 `ai_assistant/api.py`。
- `engines` 不读数据库。后端把栏目录作为 `Path` 传入记录器。
- 不 import `ae_harness.assistant`。
- 前端只经助手 api 打开报告，不拼磁盘路径。

## Risks / Trade-offs

- [进程在写到一半时重启] → 该轮标为 interrupted；已写出的 HTML 若存在，结束后可打开，不承诺完整。
- [HTML 含截图] → 只经登录后的白名单接口读取，不进入 JSONL，不进入列表响应。
