## 1. 对话稿模块

- [x] 1.1 新增 `engines/agents/messaging/dialogue.py`：按次打开 `logs/agent_logs/<run-id>.jsonl`（默认 run-id 为 `sop-` + 北京时间），自动建目录、UTF-8 追加、加锁、失败只记 warning。验证：`pytest tests/graybox/unit/test_agent_dialogue_log.py -q -k path` 通过，断言目录自动创建且两次运行不是同一个文件
- [x] 1.2 实现助手 / 工具 / 用户 / 上下文 / 汇总五类写入。助手块含 `model`、`tokens`、`cost`（4 位小数）、`duration_sec`（2 位小数或 null）；每块含 `kind`、`ts`、`role`。验证：同文件 `-k blocks` 通过，逐行 `json.loads` 后字段与 spec 一致

## 2. 事件组块

- [x] 2.1 消费模型调用与文本增量：一次调用结束时合成一块助手；无文本仍写空正文；无起止时刻时 `duration_sec` 为 null。费用由调用方传入，本模块不计算价目。验证：同文件 `-k assistant` 通过
- [x] 2.2 按工具调用标识把入参与返回合成一块；拆出 `<tool-instructions>` 与 `<system-reminder>` 为紧随的上下文块；图片二进制不入文件。运行结束时未返回的调用状态为 `-`。验证：同文件 `-k tool` 通过

## 3. 接入 SOP

- [x] 3.1 `SopRunner` 开跑时创建对话稿（目录 `logs/agent_logs`），写入启动输入与步骤开始的用户块，把事件与已算出的费用交给新模块，结束时写汇总块。过程日志路径与行格式不变。`messaging/__init__.py` 导出新入口。验证：`rg -n "agent_logs|DialogueLog" engines/agents/role/sop.py engines/agents/messaging/__init__.py` 能看到接入点；`pytest tests/graybox/unit/test_agent_dialogue_log.py -q` 全部通过；`ruff check engines/agents/messaging/dialogue.py engines/agents/role/sop.py engines/agents/messaging/__init__.py` 无新增问题
