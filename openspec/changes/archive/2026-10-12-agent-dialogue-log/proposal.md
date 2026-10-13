## Why

终端里的对话块（助手 / 工具 / 用户 / 上下文）和按天的过程日志都不好直接回放：过程日志是竖线分隔的一行一条，终端输出又不落盘。调试时需要一份按次保存、带时间戳和角色、并在助手块上带上模型、用量、费用与耗时的本地记录。

## What Changes

- 新增对话稿：一次 SOP 运行追加写入一份 JSONL，每块一行，标题语义为「类型 · 时间戳 · 角色」。
- 块类型：助手、工具（同一次调用的入参与返回合成一块）、用户、上下文（从工具返回里拆出的工具说明 / 系统提醒）。
- 助手块附带本次模型调用信息：模型名、输入 / 输出 / 缓存命中 token、费用（元）、耗时（秒）。运行结束再写一条汇总块。
- 落盘目录固定为 `logs/agent_logs/`，按运行区分文件，便于和设备日志、过程日志分开调试。
- 既有过程日志 `logs/sop-YYYYMMDD.log` 的格式与路径不变。
- HTML 展示不在本次范围内。

## 关联文档

无关联 PRD 编号：本次只给 `engines/agents` 的本地调试落盘，不改变平台对外接口或页面。

## Capabilities

### New Capabilities
- `agent-dialogue-log`: 把一次智能体运行的对话块实时追加写入 `logs/agent_logs/` 下的 JSONL，助手块带模型、用量、费用与耗时。

### Modified Capabilities
（无）

## Impact

- 代码：`engines/agents/messaging/` 新增一个模块；`engines/agents/role/sop.py` 在运行时把事件与已算出的费用交给该模块。`engines/agents/process_log.py` 与 `logs/sop-*.log` 不改行为。
- 产物：`logs/agent_logs/<run-id>.jsonl`。
- 平台侧（`apps/`、`frontend/`、`engines/ai`）无改动。
- 验证：针对该模块的单元测试，不跑全量回归。
