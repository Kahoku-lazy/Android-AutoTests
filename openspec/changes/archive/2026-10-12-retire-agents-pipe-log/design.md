## Context

见 proposal.md - Why。`engines/agents` 现在有两套落盘：`DialogueLog` 写 `logs/agent_logs/<run-id>.jsonl`；`AgentProcessLog` + `EventStreamRecorder` 写按天管道行。SOP 运行时两者都消费同一条事件流。`EventStreamRecorder` 上的思考与工具汇总没有被角色结果读取，只服务于管道日志。平台侧 `engines/ai` 仍单独实现同一套管道日志，并被 `ai-agent-process-log` 约束。

## Goals / Non-Goals

**Goals:**

- `engines/agents` 的模型运行落盘只剩对话稿。
- 删掉该包里只为管道日志存在的模块与接线，角色启动不再携带日志基路径。

**Non-Goals:**

- 不改 `engines/ai` 的过程日志，也不改 `ai-agent-process-log`。
- 不把对话稿接进 `BaseRole` 的单轮回复。当前没有调用方走这条路径写文件；SOP 运行器已经写对话稿。接进去会和运行器双写。
- 不在运行器里生成 HTML，不改 `temps/dialogue-log-demo.html`。
- 不删除磁盘上已经写下的 `logs/sop-*.log`。

## Decisions

1. 删除 `engines/agents/process_log.py` 与 `engines/agents/messaging/events.py`，而不是留一个空写开关。管道格式不再有第二份实现留在这个包里。备选：保留模块但默认关闭。否决，因为调用方仍要传日志对象，两套代码继续并存。
2. `SopRunner` 去掉 `log` 参数、记录器与管道用量汇总。结束时的汇总仍只走对话稿里已有的汇总块。`独立运行` 这几个字留在角色模块本地常量，不为一个字符串保留过程日志模块。
3. `BaseRole.start` 去掉 `log_enabled` 与 `log_path`。单轮 `reply` 只保留控制台输出，不再建记录器。命令行入口不再 `start(log_enabled=True, log_path="logs/sop.log")`，也不再把过程日志传给 runner。
4. `messages.py` 留下。对话稿仍用它清洗工具返回、去掉图片二进制。

## 模块防火墙自检

- 不跨 App import，不新增 service / runner / consumer 依赖。
- 不写任何业务表，不碰 `api.py`。
- 前端无改动，仪表盘无写操作。
- 日志只落在本地 `logs/agent_logs/`，不经 HTTP。

## Risks / Trade-offs

- [有人还在跟 `logs/sop-*.log` 看这次 SOP] → 这次运行的可读记录只在 `logs/agent_logs/`。平台任务仍写 `engines/ai` 的按天日志，不受影响。
- [单轮 `reply` 不再落盘] → 当前没有调用方依赖它落盘。以后若要记录，再把对话稿接到那条路径，本次不接。
